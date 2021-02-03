#!/usr/bin/env python3
import asyncio
import gettext
import logging
import re
import httpx

import config
from modules import loglevel
from modules import util

_ = gettext.gettext

logger = logging.getLogger(__name__)
if config.loglevel is None:
    # Set loglevel
    loglevel.set_loglevel()
logger.setLevel(config.loglevel)
logger.level = logger.getEffectiveLevel()
file_handler = logging.FileHandler("riksdagen.log")
logger.addHandler(file_handler)

# Constants
baseurl = "https://data.riksdagen.se/dokument/"

# Entry is in the bottom get_records(data)

def get_result_count(word):
    # First find out the number of results
    url = (f"http://data.riksdagen.se/dokumentlista/?sok={word}" +
           "&sort=rel&sortorder=desc&utformat=json&a=s&p=1")
    r = httpx.get(url)
    data = r.json()
    results = int(data["dokumentlista"]["@traffar"])
    logging.info(f"results:{results}")
    return results


async def async_fetch(word):
    # This function is called for every task.
    async def get(url, session):
        """Accepts a url and a httpx session"""
        response = await session.get(url)
        return response

    # Get total results count
    results = get_result_count(word)
    # Generate the urls
    if results > config.riksdagen_max_results_size:
        results = config.riksdagen_max_results_size
    # generate urls
    urls = []
    # divide by 20 to know how many requests to send
    for i in range(1, int(results / 20)):
        urls.append(f"http://data.riksdagen.se/dokumentlista/?sok={word}" +
                    f"&sort=rel&sortorder=desc&utformat=json&a=s&p={i}")
    logging.debug(f"urls:{urls}")
    # get urls asynchroniously
    # inspired by https://trio.readthedocs.io/en/stable/tutorial.html
    async with httpx.AsyncClient() as session:
        logger.info("Gathering tasks.")
        # inspired by https://stackoverflow.com/questions/56161595/
        # how-to-use-async-for-in-python
        results = await asyncio.gather(*[get(url, session) for url in urls])
        logger.info(f"All {len(results)} tasks done")
        return results


def process_async_responses(word):
    print("Downloading from the Riksdagen API...")
    results = asyncio.run(async_fetch(word))
    records = []
    for response in results:
        data = response.json()
        # check if dokument is in the list
        key_list = list(data["dokumentlista"].keys())
        if "dokument" in key_list:
            for item in data["dokumentlista"]["dokument"]:
                records.append(item)
    length = len(records)
    logger.info(f"Got {length} records")
    if config.debug_json:
        logger.debug(f"records:{records}")
    return records


# def fetch(word):
#     # Look up records from the Riksdagen API
#     records = []
#     print("Downloading from the Riksdagen API...")
#     for i in range(1, int(config.riksdagen_max_results_size / 20) + 1):
#         if i > 1:
#             # break if i is more than 1 and the results are less than 20
#             # because that means that there are no more results in page 2-5
#             if len(records) < 20:
#                 break
#         url = (f"http://data.riksdagen.se/dokumentlista/?sok={word}" +
#                "&sort=rel" +
#                "&sortorder=desc&utformat=json&a=s" +
#                f"&p={i}")
#         if config.debug_riksdagen:
#             print(url)
#         r = httpx.get(url)
#         data = r.json()
#         # check if dokument is in the list
#         key_list = list(data["dokumentlista"].keys())
#         if "dokument" in key_list:
#             for item in data["dokumentlista"]["dokument"]:
#                 records.append(item)
#         else:
#             # We break if the API does not return any more results
#             if config.debug_riksdagen:
#                 print("API did not return any (more) results")
#             break
#     if config.debug:
#         logging.info(f"Got {len(records)} records from the Riksdagen API")
#     if config.debug_json:
#         print(records)
#     return records


def find_usage_examples_from_summary(
        word_spaces=None,
        summary=None
):
    """This tries to find and clean sentences and return the shortest one"""
    # TODO check for duplicates or near duplicates and remove
    cleaned_summary = summary.replace(
        '<span class="traff-markering">', ""
    )
    cleaned_summary = cleaned_summary.replace('</span>', "")
    ellipsis = "…"
    # replace "t.ex." temporarily to avoid regex problems
    cleaned_summary = cleaned_summary.replace("t.ex.", "xxx")
    # Leave the last dot of m.m. to retain the full stop it probably
    # means
    cleaned_summary = cleaned_summary.replace("m.m", "yyy")
    cleaned_summary = cleaned_summary.replace("dvs.", "qqq")
    # bl.a.
    cleaned_summary = cleaned_summary.replace("bl.", "zzz")
    # TODO add "ang." "kl." "s.k." "resp." "prop." "skr."

    # from https://stackoverflow.com/questions/3549075/
    # regex-to-find-all-sentences-of-text
    sentences = re.findall(
        "[A-Z].*?[\.!?]", cleaned_summary, re.MULTILINE | re.DOTALL
    )
    # Remove duplicates naively using sets
    sentences_without_duplicates = list(set(sentences))
    if config.debug_duplicates:
        print("Sentences after duplicate removal " +
              f"{sentences_without_duplicates}")
    suitable_sentences = []
    for sentence in sentences_without_duplicates:
        exclude_this_sentence = False
        # Exclude based on lenght of the sentence
        word_count = util.count_words(sentence)
        if (
                word_count > config.max_word_count or word_count <
                config.min_word_count
        ):
            exclude_this_sentence = True
            # Exclude by breaking out of the iteration early
            break
        else:
            # Exclude based on weird words that are not suitable sentences
            excluded_words = [
                "SAMMANFATTNING",
                "BETÄNKANDE",
                "UTSKOTT",
                "MOTION",
                " EG ",
                " EU ",
                "RIKSDAGEN",
            ]
            for excluded_word in excluded_words:
                result = sentence.upper().find(excluded_word)
                if result != -1:
                    if config.debug_excludes:
                        sentence = (sentence
                                    .replace("\n", "")
                                    .replace("-", "")
                                    .replace(ellipsis, ""))
                        logging.debug(
                            f"Found excluded word {excluded_word} " +
                            f"in {sentence}. Skipping",
                        )
                    exclude_this_sentence = True
                    break
        # Add space to match better
        if word_spaces in sentence and exclude_this_sentence is False:
            # restore the t.ex.
            sentence = sentence.replace("xxx", "t.ex.")
            sentence = sentence.replace("yyy", "m.m")
            sentence = sentence.replace("qqq", "dvs.")
            sentence = sentence.replace("zzz", "bl.")
            # Last cleaning
            sentence = (sentence
                        .replace("\n", "")
                        # This removes "- " because the data is hyphenated
                        # sometimes
                        .replace("- ", "")
                        .replace(ellipsis, "")
                        .replace("  ", " "))
            if config.debug_sentences:
                logging.debug(f"suitable_sentence:{sentence}")
            suitable_sentences.append(sentence)
    return suitable_sentences


def extract_summaries_from_records(records, data):
    # TODO look for more examples from riksdagen if none in the first set of
    # results fit our purpose
    word_spaces = data["word_spaces"]
    word_angle_parens = data["word_angle_parens"]
    word = data["word"]
    count_inexact_hits = 1
    count_exact_hits = 1
    count_summary = 1
    summaries = {}
    for record in records:
        if config.debug_summaries:
            logging.info(f"Working of record number {count_summary}")
        summary = record["summary"]
        # This is needed by present_sentence() and add_usage_example()
        # downstream
        document_id = record["id"]
        # This date is the date it was published on the web after digitization
        # and is useless to us
        # date = record["publicerad"]
        # This date should be when the document was published the first time
        # but
        # its not not always reliable because the dataset is of overall low
        # quality it seems.
        date = record["datum"]
        if config.debug_summaries:
            logger.info(
                f"Found in https://data.riksdagen.se/dokument/{document_id}"
            )
        record_data = {}
        record_data["document_id"] = document_id
        record_data["date"] = date
        # match only the exact word
        added = False
        if word in summary:
            count_inexact_hits += 1
            if word_spaces in summary or word_angle_parens in summary:
                count_exact_hits += 1
                # add to dictionary
                if config.debug_summaries:
                    logging.debug(
                        f"found word_spaces or word_angle_parens in {summary}"
                    )
                summaries[summary] = record_data
                added = True
            else:
                if config.debug_summaries:
                    logging.info("No exact hit in summary. Skipping.")
        else:
            if config.debug_summaries and added is False:
                print(f"'{word}' not found as part of a word or a " +
                      "word in the summary. Skipping")
        count_summary += 1
    # if config.debug_summaries:
    #     logging.debug(f"summaries:{summaries}")
    logger.info(f"Found {len(summaries)} suitable summaries")
    return summaries


def get_records(data):
    word = data["word"]
    records = process_async_responses(word)
    if records is not None:
        if config.debug:
            print("Looping through records from Riksdagen")
        summaries = extract_summaries_from_records(records, data)
        unsorted_sentences = {}
        # Iterate through the dictionary
        for summary in summaries:
            # Get result_data
            result_data = summaries[summary]
            # Add information about the source (written,oral) and
            # (formal,informal)
            result_data["language_style"] = "formal"
            result_data["type_of_reference"] = "written"
            result_data["line"] = None
            result_data["source"] = "riksdagen"
            # document_id = result_data["document_id"]
            # if config.debug_summaries:
            #     print(f"Got back summary {summary} with the " +
            #           f"correct document_id: {document_id}?")
            suitable_sentences = find_usage_examples_from_summary(
                word_spaces=data["word_spaces"],
                summary=summary
            )
            if len(suitable_sentences) > 0:
                for sentence in suitable_sentences:
                    # Make sure the riksdagen_document_id follows
                    unsorted_sentences[sentence] = result_data
        print(f"Found {len(unsorted_sentences)} suitable sentences")
        return unsorted_sentences
