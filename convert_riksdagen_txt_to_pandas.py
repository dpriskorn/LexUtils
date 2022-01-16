import os
import re
import time
import zipfile as ziplib

import pandas as pd
from spacy.lang.sv import Swedish

from lexutils.helpers.console import console
pickle_filename = "departementsserien.pkl.gz"
dir = r"riksdagen/ds-text/"
files = os.listdir(dir)

start = time.time()
df = pd.DataFrame()
skipped_count = 0
split_count = 0
for zipfile in files:
    print(zipfile)
    if ".zip" in zipfile:
        # This probably read the whole thing into memory which is not ideal...
        with ziplib.ZipFile(dir + zipfile) as z:
            count_file = 1
            for filename in z.namelist():
               #print(filename)
                document_id = filename.replace(".txt", "")
                print(f"working on {document_id} ({count_file}/{len(z.namelist())}) "
                      f"skipped: {skipped_count} dataframe rows: {len(df)} splits: {split_count}")
                if not os.path.isdir(filename):
                    # read the file
                    with z.open(filename) as f:
                        current_line_number = 1
                        # We use a set to avoid duplicates
                        cleaned_lines = set()
                        for line in f.readlines():
                            line = line.decode("utf-8").strip()
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
                                print(current_line_number)
                            current_line_number += 1
                        text = " ".join(cleaned_lines)
                        nlp = Swedish()
                        nlp.add_pipe('sentencizer')
                        # 100.000 char is the max for the NLP parser so we split along something we discard anyway
                        # the effect of this split is unknown, it might result in 2 garbage sentences for every split
                        if len(text) > 95000:
                            print("splitting the text up")
                            text_after_split = text.split("1")
                            print(f"len(text_after_split):{len(text_after_split)}")
                            split_count += 1
                            #exit(0)
                        sentences = set()
                        for text in text_after_split:
                            doc = nlp(text)
                            for sentence in doc.sents:
                                # Skip all sentences with numbers
                                # https://stackoverflow.com/questions/4289331/how-to-extract-numbers-from-a-string-in-python
                                if len(re.findall(r'\b\d+\b', str(sentence))) == 0:
                                    sentences.add(sentence)
                                else:
                                    skipped_count += 1
                                    # console.print(f"skipped: {sentence}", style="red")
                        for sentence in sentences:
                            df = df.append(pd.DataFrame(data=[dict(id=document_id,sentence=sentence)]))
                            # print(sentence)
                            # print("--")
                count_file += 1
                #break
    #break
print(df.info(), df.describe())
df.to_pickle(pickle_filename)
end = time.time()
print(f"total duration: {round(end - start)}s")
