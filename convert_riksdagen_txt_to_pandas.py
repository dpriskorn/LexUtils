import logging
import os
import re
import time
import random

import langdetect
import pandas as pd
from spacy.lang.sv import Swedish

from lexutils.config.enums import SupportedPickles

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
pickle_filename = SupportedPickles.RIKSDAGEN
dir = r"riksdagen/"
max_dataframe_rows = 200000
files = os.listdir(dir)

start = time.time()
df = pd.DataFrame()
skipped_count = 0
split_count = 0
count_file = 1
# We shuffle the list to avoid only
# having one of the document types
random.shuffle(files)
for filename in files:
    if ".txt" in filename:
        # print(filename)
        path = dir+filename
        document_id = filename.replace(".txt", "")
        print(f"working on {document_id} ({count_file}/{len(files)}) "
              f"skipped: {skipped_count} dataframe rows: {len(df)}/{max_dataframe_rows} splits: {split_count}")
        current_line_number = 1
        # We use a set to avoid duplicates
        cleaned_lines = set()
        with open(path, "r", encoding="UTF-8") as f:
            for line in f.readlines():
                line = line.strip()
                if (
                        # Remove weird dots
                        "..." not in line and
                        # Only keep lines with more than 4 words
                        len(line.split(" ")) > 4
                ):
                    cleaned_lines.add(line)
                # if current_line_number == 1000:
                #     break
                if current_line_number % 5000 == 0:
                    logger.info(current_line_number)
                current_line_number += 1
        text = " ".join(cleaned_lines)
        #print(text)
        #exit()
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
            # exit(0)
        sentences = set()
        for text in text_after_split:
            doc = nlp(text)
            for sentence in doc.sents:
                sentence = str(sentence)
                # Skip all sentences with numbers
                # https://stackoverflow.com/questions/4289331/how-to-extract-numbers-from-a-string-in-python
                if (
                        len(sentence.split(" ")) > 4 and
                        # Remove sentences with digits and (, ), [, ], §, /
                        len(re.findall(r'\d+|\(|\)|§|\[|\]|\/', sentence)) == 0 and
                        sentence[0:1] != " " and
                        sentence[0:1] != "," and
                        not sentence[0:1].islower() and
                        langdetect.detect(sentence) == "sv"
                ):
                    # Ta bort punktum från början
                    sentences.add(sentence.lstrip("."))
                else:
                    skipped_count += 1
                    # console.print(f"skipped: {sentence}", style="red")
        for sentence in sentences:
            # print(type(sentence))
            dictionary = dict(id=document_id, sentence=sentence)
            #print(dictionary)
            # exit()
            df = df.append(pd.DataFrame(data=[dictionary]))
            # print(sentence)
            # print("--")
        count_file += 1
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
