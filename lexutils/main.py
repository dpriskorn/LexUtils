#!/usr/bin/env python3
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import gettext
import logging
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
import click
from fuzzyfinder import fuzzyfinder

import config
# Import util first
from modules import util
from modules import lexuse
from modules import loglevel

# Settings
_ = gettext.gettext

# This is the script that keeps the REPL up

#
# Functions
#

# debug
from modules import wikidata
df = wikidata.fetch_lexeme_forms()
# https://note.nkmk.me/en/python-pandas-dataframe-rename/
df.rename(
    columns={
        'grammatical_featureLabel': 'feature',
        'categoryLabel': 'category'
    },
    inplace=True
)
df["lid"] = df["entity_lid"].str.replace(util.wd_prefix,'')
df["formid"] = df["form"].str.replace(util.wd_prefix,'')
df["senseid"] = df["sense"].str.replace(util.wd_prefix,'')
#import pandas as pd
#pd.set_option("display.max_columns", 10)
# print(df.sample(n=1))
# print(df.describe())
# print(list(df))
#grouped= df.groupby("lid", "senseid", "formid")
#senses = df.groupby("lid", "senseid")
#
#https://stackoverflow.com/a/36394939
forms = df.groupby("formid")["feature"].apply(' '.join).reset_index()
print(forms)
print(list(forms))
# Loop through the rows
for index, row in forms.iterrows():
    formid = row["formid"]
    # find index where formid appears in the original df
    dfindex = df.index[df["formid"] == formid].tolist()[0]
    #print(f"dfindex: {dfindex}")
    print(formid, row["feature"], df.loc[dfindex]["word"])

exit(0)

Commands = ['lexuse']

class SQLCompleter(Completer):
    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        matches = fuzzyfinder(word_before_cursor, Commands)
        for m in matches:
            yield Completion(m, start_position=-len(word_before_cursor))

            
def main():
    logger = logging.getLogger(__name__)
    if config.loglevel is None:
        # Set loglevel
        loglevel.set_loglevel()
    logger.setLevel(config.loglevel)
    logger.level = logger.getEffectiveLevel()
    # file_handler = logging.FileHandler("europarl.log")
    # logger.addHandler(file_handler)

    # TODO enable choosing work language
    print(_('This is the REPL. ' +
            'Type one of the names of the tools to begin: ' +
            'LexUse'))

    while 1:
        user_input = prompt(u'LexUtils>',
                            history=FileHistory('history.txt'),
                            auto_suggest=AutoSuggestFromHistory(),
                            completer=SQLCompleter(),
                            )
        if user_input.lower() == "lexuse":
            lexuse.start()
        # if user_input.lower() == "lexcombine":
        #     print(_('LexCombine has not been implemented yet.'+
        #           ' Feel free to help out by sending pull requests'))

if __name__ == "__main__":
    main()
