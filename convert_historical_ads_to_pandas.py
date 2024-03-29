import gzip
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Any, Set

import langdetect
import pandas as pd
from langdetect import LangDetectException
from spacy.lang.en import English
from spacy.lang.sv import Swedish

from lexutils.config.enums import SupportedPicklePaths
# First download gzipped jsonl files from https://data.jobtechdev.se/expediering/index.html into arbetsformedlingen/
from lexutils.models.wikidata.enums import WikimediaLanguageCode

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Settings
target_language_code = WikimediaLanguageCode.SWEDISH
pickle_filename = SupportedPicklePaths.ARBETSFORMEDLINGEN_HISTORICAL_ADS
dir = r"arbetsformedlingen/"
# This is the output after deduplication of sentences
max_dataframe_rows = 100000
max_words_in_sentence = 50


def split_into_sentences(text: str = None,
                         nlp_instance: Any = None) -> Set[str]:
    if text is None or nlp_instance is None:
        raise ValueError("we did not get what we need")
    doc = nlp_instance(text)
    sentences_without_newlines = []
    sentences_without_newlines_or_stars = []
    sentences_without_newlines_or_stars_or_dashes = []
    sentences_without_newlines_or_stars_or_dashes_or_multiple_spaces = []
    sentences_without_newlines_or_stars_or_dashes_or_multiple_spaces_or_bullets = []
    for sentence in doc.sents:
        sentence = str(sentence).strip()
        if "\n" in sentence:
            logger.info("Split sentence with newline(s) from the sentenizer")
            sentences_without_newlines.extend(sentence.splitlines())
        else:
            sentences_without_newlines.append(sentence)
    for sentence in sentences_without_newlines:
        if "*" in sentence:
            logger.info("Split sentence with stars(es) from the sentenizer")
            sentences_without_newlines_or_stars.extend(sentence.split("*"))
        else:
            sentences_without_newlines_or_stars.append(sentence)
    for sentence in sentences_without_newlines_or_stars:
        if " - " in sentence:
            logger.info("Split sentence with dash(es) from the sentenizer")
            sentences_without_newlines_or_stars_or_dashes.extend(sentence.split(" - "))
        else:
            sentences_without_newlines_or_stars_or_dashes.append(sentence)
    for sentence in sentences_without_newlines_or_stars_or_dashes:
        if "    " in sentence:
            logger.info("Split sentence with 3 spaces from the sentenizer")
            sentences_without_newlines_or_stars_or_dashes_or_multiple_spaces.extend(
                sentence.split("    "))
        else:
            sentences_without_newlines_or_stars_or_dashes_or_multiple_spaces.append(
                sentence)
    for sentence in sentences_without_newlines_or_stars_or_dashes_or_multiple_spaces:
        if "•" in sentence:
            logger.info("Split sentence with bullet from the sentenizer")
            sentences_without_newlines_or_stars_or_dashes_or_multiple_spaces_or_bullets.extend(
                sentence.split("•"))
        else:
            sentences_without_newlines_or_stars_or_dashes_or_multiple_spaces_or_bullets.append(
                sentence)
    return set(sentences_without_newlines_or_stars_or_dashes_or_multiple_spaces_or_bullets)


def clean_swedish_sentence(sentence: str = None) -> str:
    if sentence is None:
        raise ValueError("we did not get what we need")
    # Strip headings
    headings = ["ARBETSUPPGIFTER", "KVALIFIKATIONER",
                "ÖVRIGT", "Villkor", "Kvalifikationer",
                "Beskrivning", "Om oss", "Arbetsmiljö",
                "Vi erbjuder:", "Övrigt", "Ansökan",
                "Placering:", "Lön:", "OM TJÄNSTEN",
                "OM OSS", "ÖVRIG INFORMATION", "KONTAKT",
                "VEM ÄR DU", "OM TJÄNSTEN", "Lön:",
                "Start:", "OM DIG", "OM JOBBET", "Om arbetet"]
    for heading in headings:
        # Position 0 is the start of the sentence
        if sentence.find(heading) == 0:
            logger.debug(f"found {heading} in '{sentence}'")
            sentence = sentence.lstrip(heading).strip()
            logger.debug(f"stripped {heading} -> {sentence}")
    # Remove chars from the start
    chars = ["·", "•", "·", "-", ".", "*", "+", "–", "_", "'", ":", "…", "·"]
    for char in chars:
        if sentence[0:1] == char:
            logger.debug(f"found {char} in start of '{sentence}'")
            sentence = sentence.lstrip(char).strip()
            logger.debug(f"stripped {char} -> {sentence}")
    return sentence.replace("  ", " ").strip()


files = os.listdir(dir)
start = time.time()
df = pd.DataFrame()
skipped_count = 0
split_count = 0
count_file = 1
for filename in files:
    # we open the gzip as a stream to avoid having to decompress it on disk and taking up a lot of space
    path = dir + filename
    with gzip.open(path, 'r') as file:
        logger.info(f"working on {filename}")
        current_line_number = 0
        # We use a set to avoid duplicates
        cleaned_lines = set()
        total_number_of_lines = "unknown"
        for line in file:
            current_line_number += 1
            # We stop when max has been reached
            if len(df) > max_dataframe_rows:
                break
            # We devide by 2 here because we have 2 files and we don't
            # want to fill the dataframe based on only one file
            if count_file == 1 and len(df) > (max_dataframe_rows / 2):
                print("Reached half of the wanted rows, breaking out now")
                break
            # We only process every 10th line because the ads are in chronological order
            # and we want ads from the whole year, not just the start.
            if current_line_number % 10 == 0:
                if current_line_number % 1000 == 0:
                    # Only deduplicate every 100 lines (it is CPU expensive)
                    df.drop_duplicates(inplace=True, subset=["sentence"])
                    print(f"working on {filename} ({count_file}/{len(files)}) "
                          f"line: {current_line_number}/{total_number_of_lines} "
                          f"skipped: {skipped_count} dataframe rows: "
                          f"{len(df)}/{max_dataframe_rows} splits: {split_count}")
                data = json.loads(line)
                id = data["id"]
                # pprint(data)
                # exit()
                if "external_id" in data:
                    external_id = data["external_id"]
                else:
                    external_id = None
                date = datetime.strptime(data["publication_date"][0:18], "%Y-%m-%dT%H:%M:%S", )
                description = data["description"]
                if "text" in description:
                    text = description["text"]
                    if text is not None and text != "":
                        # detecting language to avoid e.g. english ads
                        logger.debug("Detecting the language")
                        language_code = None
                        try:
                            language_code = langdetect.detect(text)
                            logger.debug(f"Detected language: {language_code}")
                        except LangDetectException:
                            logger.warning(f"Could not detect language for '{text}'")
                            pass
                        if language_code == target_language_code.value:
                            # Branch off into the supported languages
                            if language_code == WikimediaLanguageCode.SWEDISH.value:
                                logger.info(
                                    f"Found {target_language_code.name.title()} ad, splitting it up in sentences")
                                # print(text)
                                # exit()
                                nlp = Swedish()
                                nlp.add_pipe('sentencizer')
                                # 100.000 char is the max for the NLP parser so we split along something we discard anyway
                                # the effect of this split is unknown, it might result in 2 garbage sentences for every split
                                text_after_split = ""
                                if len(text) > 95000:
                                    logger.info("splitting the text up")
                                    text_after_split = text.split("1")
                                    logger.debug(f"len(text_after_split):{len(text_after_split)}")
                                    split_count += 1
                                    exit(0)
                                else:
                                    logger.info("the text was not over 95000 chars")
                                    text_after_split = [text]
                                # logger.debug(f"text:{text}")
                                # exit(0)
                                sentences = set()
                                for text in text_after_split:
                                    split_sentences = split_into_sentences(text=text,
                                                                           nlp_instance=nlp)
                                    for sentence in split_sentences:
                                        sentence = clean_swedish_sentence(sentence=sentence)
                                        # logger.debug(f"nlp sentence: {sentence}")
                                        # Skip all sentences with numbers
                                        # https://stackoverflow.com/questions/4289331/how-to-extract-numbers-from-a-string-in-python
                                        if (
                                                len(sentence.split(" ")) > 4 and
                                                # We don't want too long sentences as examples in Wikidata
                                                len(sentence.split(" ")) < max_words_in_sentence and
                                                # Remove sentences with digits and (, ), [, ], §, /
                                                len(re.findall(r'\d+|\(|\)|§|\[|\]|\/', sentence)) == 0 and
                                                sentence[0:1] != "," and
                                                not sentence[0:1].islower() and
                                                sentence.find("http") == -1 and
                                                sentence.find(".se") == -1 and
                                                sentence.find(" ") == -1 and
                                                sentence.find(":") == -1 and
                                                sentence.find(";") == -1
                                        ):
                                            sentences.add(sentence.strip())
                                        else:
                                            skipped_count += 1
                                            # logger.debug(f"skipped: {sentence}")
                                logger.info(f"found {len(sentences)} in this ad")
                                for sentence in sentences:
                                    # print(type(sentence))
                                    dictionary = dict(id=id, date=date, external_id=external_id,
                                                      filename=filename, sentence=sentence)
                                    # print(dictionary)
                                    # exit()
                                    df = df.append(pd.DataFrame(data=[dictionary]))
                                    # print(sentence)
                                    # print("--")
                            # elif language_code == WikimediaLanguageCode.ENGLISH.value:
                            #     logger.info(
                            #         f"Found {target_language_code.name.title()} ad, splitting it up in sentences")
                            #     current_line_number += 1
                            #     # print(text)
                            #     # exit()
                            #     nlp = English()
                            #     nlp.add_pipe('sentencizer')
                            #     # 100.000 char is the max for the NLP parser so we split along something we discard anyway
                            #     # the effect of this split is unknown, it might result in 2 garbage sentences for every split
                            #     text_after_split = ""
                            #     if len(text) > 95000:
                            #         logger.info("splitting the text up")
                            #         text_after_split = text.split("1")
                            #         logger.debug(f"len(text_after_split):{len(text_after_split)}")
                            #         split_count += 1
                            #         exit(0)
                            #     else:
                            #         logger.info("the text was not over 95000 chars")
                            #         text_after_split = [text]
                            #     # logger.debug(f"text:{text}")
                            #     # exit(0)
                            #     sentences = set()
                            #     for text in text_after_split:
                            #         doc = nlp(text)
                            #         sentences_without_newlines = []
                            #         for sentence in doc.sents:
                            #             sentence = str(sentence).strip()
                            #             # Strip headings
                            #             # headings = ["ARBETSUPPGIFTER", "KVALIFIKATIONER",
                            #             #             "ÖVRIGT", "Villkor", "Kvalifikationer",
                            #             #             "Beskrivning"]
                            #             # for heading in headings:
                            #             #     # We only check the first word
                            #             #     words_list = sentence.split(" ")
                            #             #     if heading in words_list[0]:
                            #             #         sentence = sentence.lstrip(heading).strip()
                            #             # Remove chars from the start
                            #             chars = ["•", "-", "."]
                            #             for char in chars:
                            #                 if sentence[0:1] == char:
                            #                     sentence = sentence.lstrip(char).strip()
                            #             sentence = sentence.replace("  ", " ").strip()
                            #             logger.debug(f"nlp sentence: {sentence}")
                            #             # Skip all sentences with numbers
                            #             # https://stackoverflow.com/questions/4289331/how-to-extract-numbers-from-a-string-in-python
                            #             if (
                            #                     len(sentence.split(" ")) > 4 and
                            #                     # Remove sentences with digits and (, ), [, ], §, /
                            #                     len(re.findall(r'\d+|\(|\)|§|\[|\]|\/', sentence)) == 0 and
                            #                     sentence[0:1] != "," and
                            #                     not sentence[0:1].islower() and
                            #                     sentence.find("http") == -1
                            #             ):
                            #                 sentences.add(sentence.strip())
                            #             else:
                            #                 skipped_count += 1
                            #                 # logger.debug(f"skipped: {sentence}")
                            #     if logger.getEffectiveLevel() > 10:
                            #         logger.info(f"found {len(sentences)} in this ad")
                            #         for sentence in sentences:
                            #             # print(type(sentence))
                            #             dictionary = dict(id=id, date=date, external_id=external_id,
                            #                               filename=filename, sentence=sentence)
                            #             # print(dictionary)
                            #             # exit()
                            #             df = df.append(pd.DataFrame(data=[dictionary]))
                            #             # print(sentence)
                            #             # print("--")
                            else:
                                logger.error(f"The chosen language "
                                             f"{target_language_code.name.title()} "
                                             f"is not supported (yet)")
                        else:
                            logger.info(f"skipping {language_code} language ad")
                            continue
                    else:
                        logger.info("skipping ad with no text")
                else:
                    logger.info("found no text in this ad")
        # We stop when max has been reached
        if len(df) > max_dataframe_rows:
            break
        count_file += 1
# break
print("before removing duplicates")
df.info()
print("and after")
df.drop_duplicates(inplace=True, subset=["sentence"])
print(df.info(), df.describe(), df.sample(10))
df.to_pickle(pickle_filename.value)
print(f"saved to {pickle_filename.value}")
end = time.time()
print(f"total duration: {round(end - start)}s")
