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
