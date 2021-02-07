#!/usr/bin/env python3
import asyncio
import gettext
import logging
import re
import httpx
from pprint import pprint
from typing import Dict, List

import config
from modules import loglevel
from modules import util
from modules import tui

_ = gettext.gettext

logger = logging.getLogger(__name__)
if config.loglevel is None:
    # Set loglevel
    loglevel.set_loglevel()
logger.setLevel(config.loglevel)
logger.level = logger.getEffectiveLevel()
file_handler = logging.FileHandler("ksamsok.log")
logger.addHandler(file_handler)

# Constants
headers = {'Accept': 'application/json'}
api_name = _("K-Samsök API")
baseurl = "http://kulturarvsdata.se/"
language_style = "formal"
type_of_reference = "written"
source = "ksamsok"

# Entry is in the bottom get_records(data)
# This file is forked from riksdagen.py and improved with typing 

async def async_fetch(word: str) -> List:
    # This function is called for every task.
    async def get(url: str, session):
        """Accepts a url and a httpx session"""
        # catch read timeouts gracefully
        # https://github.com/encode/httpx/blob/
        # e3a7b6d7318f943b2289437f74028cb36b5b02e4/docs/exceptions.md
        try:
            response = await session.get(url, headers=headers)
        except httpx.RequestError as exc:
            logger.info(f"An error occurred while requesting {exc.request.url!r}.")
        return response
    
    urlbase = ("http://kulturarvsdata.se/ksamsok/api?"+
               "x-api=test&method=search&hitsPerPage=50"+
               f"&query={word}&startRecord=")
    results = get_result_count(word)
    if results > config.ksamsok_max_results_size:
        results = config.ksamsok_max_results_size
    urls = []
    # send in steps of 50
    for i in range(1, results, 50):
        url = urlbase + str(i)
        urls.append(url)
    logger.debug(f"urls:{urls}")
    # get urls asynchroniously
    # inspired by https://trio.readthedocs.io/en/stable/tutorial.html
    async with httpx.AsyncClient() as session:
        logger.info("Gathering tasks.")
        # inspired by https://stackoverflow.com/questions/56161595/
        # how-to-use-async-for-in-python
        results = await asyncio.gather(
            *[get(url, session) for url in urls],
        )
        logger.info(f"All {len(results)} tasks done")
        return results

def get_result_count(word: str) -> int:
    url = ("http://kulturarvsdata.se/ksamsok/api?"+
               f"x-api=test&method=search&hitsPerPage=1&query={word}")
    r = httpx.get(url, headers=headers)
    #pprint(r.json())
    results = r.json()["result"]["totalHits"]
    logger.info(f"results:{results}")
    return int(results)


def process_async_responses(word: str) -> List:
    tui.downloading_from(api_name)
    results = asyncio.run(async_fetch(word))
    records = []
    for response in results:
        data = response.json()
        # pprint(data)
        if len(data["result"]["records"]) > 0:
            for item in data["result"]["records"]:
                records.append(item)
    length = len(records)
    logger.info(f"Found {length} records")
    if config.debug_json:
        logger.debug(f"records:{records}")
    return records    


def extract_descriptions_from_records(records: List, data: Dict) -> Dict:
    # First find out the number of results
    # print(r)
    word = data["word"]
    descriptions = {}
    # Create a pattern to match string 'sample'
    pattern = re.compile("http")
    if len(records) > 0:
        for r in records:
            #pprint(r["record"])
            record = r["record"]
            ksamsok_uri = None
            if "@graph" in record:
                graph= record["@graph"]
                # First find the id
                for item in graph:
                    # pprint(item)
                    if item["@type"] == "Entity":
                        ksamsok_uri = item["@id"].replace(
                            baseurl, "",
                        )
                        # Break out early
                        break
            else:
                logger.debug("@graph not found for {ksamsok_uri}")
                # pprint(item)
            # Then find the description
            if ksamsok_uri is not None:
                for item in graph:
                    if item["@type"] == "ItemDescription":
                        if "desc" in item:
                            desc = item["desc"].strip()
                            #print(desc)
                            word_list = desc.split(" ")
                            converted_list = (
                                [x.strip().upper().replace(".", "")
                                 for x in word_list]
                            ) 
                            #logger.debug(converted_list)
                            # Skip OCR garbage
                            if "[OCR]" in converted_list:
                                logger.debug(f"ocr description {desc} skipped")
                                break
                            # Append only if it contains what we want
                            if word.upper() in converted_list:
                                record_data = {}
                                record_data["document_id"] = ksamsok_uri
                                # ksamsok does not have dates on the creation of
                                # objects and neither of say when a photo was
                                # taken. This means we cannot reliably import a
                                # date in Wikidata on the reference.
                                # See e.g. http://kulturarvsdata.se/MM/foto/703356
                                record_data["date"] = None
                                descriptions[desc] = record_data
                                #print(item["desc"])
    logger.info(f"Number of descriptions:{len(descriptions)}")
    # pprint(descriptions)
    return(descriptions)
    

def get_records(data: dict) -> Dict:
    """Return dictionary similar to riksdagen.py with the sentence as key and a
    dictionary as value that contains details about the sentence."""
    word = data["word"]
    records = process_async_responses(word)
    if records is not None:
        logger.debug(f"Looping through records from {api_name}")
        sentences = extract_descriptions_from_records(records, data)
        unsorted_sentences = {}
        # Iterate through the dictionary
        for sentence in sentences:
            # Exclude based on lenght of the sentence
            word_count = util.count_words(sentence)
            if (
                    word_count > config.max_word_count or word_count <
                    config.min_word_count
            ):
                # Exclude by breaking out of the iteration early
                break
            # Get result_data
            result_data = sentences[sentence]
            logger.debug(result_data)
            # Add information about the source (written,oral) and
            # (formal,informal)
            result_data["language_style"] = language_style
            result_data["type_of_reference"] = type_of_reference
            result_data["source"] = source
            result_data["line"] = None
            # document_id = result_data["document_id"]
            # if config.debug_summaries:
            #     print(f"Got back summary {summary} with the " +
            #           f"correct document_id: {document_id}?")
            unsorted_sentences[sentence] = result_data
        logging.info(_("Found {} suitable sentences from {}".format(
            len(unsorted_sentences), api_name
        )))
        return unsorted_sentences
