import gzip
import json
import logging
import os
import re
import time
from datetime import datetime

import langdetect
import pandas as pd
from spacy.lang.sv import Swedish

from lexutils.config.enums import SupportedPickles

# First download gzipped jsonl files from https://data.jobtechdev.se/expediering/index.html into arbetsformedlingen/
from lexutils.models.wikidata.enums import WikimediaLanguageCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
pickle_filename = SupportedPickles.ARBETSFORMEDLINGEN_HISTORICAL_ADS
dir = r"arbetsformedlingen/"
max_dataframe_rows = 200000
files = os.listdir(dir)

start = time.time()
df = pd.DataFrame()
skipped_count = 0
split_count = 0
count_file = 1
for filename in files:
    # we open the gzip as a stream to avoid having to decompress it on disk and taking up a lot of space
    path = dir+filename
    with gzip.open(path, 'r') as file:
        logger.info(f"working on {filename}")
        current_line_number = 1
        # We use a set to avoid duplicates
        cleaned_lines = set()
        for line in file:
            # logger.debug('got line', line)
            if current_line_number % 100 == 0:
                logger.info(f"current_line_number: {current_line_number}")
            # path = dir+filename
            print(f"working on {filename} ({count_file}/{len(files)}) "
                  f"skipped: {skipped_count} dataframe rows: {len(df)}/{max_dataframe_rows} splits: {split_count}")
            data = json.loads(line)
            id = data["id"]
            #pprint(data)
            #exit()
            if "external_id" in data:
                external_id = data["external_id"]
            else:
                external_id = None

            date = datetime.strptime(data["publication_date"], "%Y-%m-%dT%H:%M:%S")
            description = data["description"]
            if "text" in description:
                text = description["text"]
                # detecting language to avoid e.g. english ads
                logger.debug("Detecting the language")
                language_code = WikimediaLanguageCode(langdetect.detect(text))
                logger.debug(f"Detected: {language_code.name.title()}")
                if language_code == WikimediaLanguageCode.SWEDISH:
                    logger.info("Found Swedish ad, splitting it up in sentences")
                    # if (
                    #         # Remove weird dots
                    #         "..." not in line and
                    #         # Only keep lines with more than 4 words
                    #         len(line.split(" ")) > 4
                    # ):
                    #     cleaned_lines.add(line)
                    #     # if current_line_number == 1000:
                    #     #     break
                    current_line_number += 1
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
                    #exit(0)
                    sentences = set()
                    for text in text_after_split:
                        doc = nlp(text)
                        for sentence in doc.sents:
                            sentence = str(sentence).strip()
                            # Strip headings
                            headings = ["ARBETSUPPGIFTER", "KVALIFIKATIONER",
                                        "ÖVRIGT", "Villkor", "Kvalifikationer",
                                        "Beskrivning"]
                            for heading in headings:
                                # We only check the first word
                                words_list = sentence.split(" ")
                                if heading in words_list[0]:
                                    sentence = sentence.lstrip(heading).strip()
                            # Remove chars from the start
                            chars = ["•", "-", "."]
                            for char in chars:
                                if sentence[0:1] == char:
                                    sentence = sentence.lstrip(char).strip()
                            sentence = sentence.replace("  ", " ")
                            logger.debug(f"nlp sentence: {sentence}")
                            # Skip all sentences with numbers
                            # https://stackoverflow.com/questions/4289331/how-to-extract-numbers-from-a-string-in-python
                            if (
                                    len(sentence.split(" ")) > 4 and
                                    # Remove sentences with digits and (, ), [, ], §, /
                                    len(re.findall(r'\d+|\(|\)|§|\[|\]|\/', sentence)) == 0 and
                                    sentence[0:1] != "," and
                                    not sentence[0:1].islower() and
                                    sentence.find("http") == -1
                            ):
                                sentences.add(sentence)
                            else:
                                skipped_count += 1
                                #logger.debug(f"skipped: {sentence}")
                    logger.info(f"found {len(sentences)} in this ad")
                    for sentence in sentences:
                        # print(type(sentence))
                        dictionary = dict(id=id, date=date, external_id=external_id, sentence=sentence)
                        # print(dictionary)
                        # exit()
                        df = df.append(pd.DataFrame(data=[dictionary]))
                        # print(sentence)
                        # print("--")
                else:
                    logger.warning(f"skipping {language_code.name.title()} ad")
                    continue
            else:
                logger.warning("found no text in this ad")
        count_file += 1
        # We devide by 2 here because we have 2 files and we don't
        # want to fill the dataframe based on only one file
        if len(df) > (max_dataframe_rows/2):
            continue
        # We stop when max has been reached
        if len(df) > max_dataframe_rows:
            break
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
