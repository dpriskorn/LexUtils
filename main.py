#!/usr/bin/env python3
import logging
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
import click
from fuzzyfinder import fuzzyfinder

import config
from modules import loglevel
from modules import util

# This is the script that keeps the REPL up

#
# Functions
#

Commands = ['lexuse', 'lexcombine']

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

    while 1:
        user_input = prompt(u'SQL>',
                            history=FileHistory('history.txt'),
                            auto_suggest=AutoSuggestFromHistory(),
                            completer=SQLCompleter(),
                            )
        if user_input == "lexuse":
            begin = util.introduction()
            if begin:
                print("Fetching lexeme forms to work on")
                results = util.fetch_lexeme_forms()
                util.process_lexeme_data(results)


if __name__ == "__main__":
    main()
