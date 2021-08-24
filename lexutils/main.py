#!/usr/bin/env python3
import warnings
import gettext
import logging
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
#import click
from fuzzyfinder import fuzzyfinder

#from lexutils import config
from lexutils.modules import examples
from lexutils.modules import statistics

# Settings
warnings.simplefilter(action='ignore', category=FutureWarning)
_ = gettext.gettext
Commands = ['examples', 'statistics']

# This is the script that keeps the REPL up


class Completer(Completer):
    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        matches = fuzzyfinder(word_before_cursor, Commands)
        for m in matches:
            yield Completion(m, start_position=-len(word_before_cursor))

            
def main():
    logger = logging.getLogger(__name__)
    print(logger.getEffectiveLevel())
    logger.setLevel(10)
    #logger = logging.getLogger(__name__)
    # TODO enable choosing work language
    print(_('This is the REPL. ' +
            'Type one of the names of the tools to begin: ' +
            'Examples'))

    while 1:
        user_input = prompt(u'LexUtils>',
                            history=FileHistory('history.txt'),
                            auto_suggest=AutoSuggestFromHistory(),
                            completer=Completer(),
                            )
        if user_input.lower() == "examples":
            # raise Exception("Rewrite to use OOP not finished yet")
            examples.start()
        if user_input.lower() == "statistics":
            statistics.main()
        # if user_input.lower() == "lexcombine":
        #     print(_('LexCombine has not been implemented yet.'+
        #           ' Feel free to help out by sending pull requests'))


if __name__ == "__main__":
    main()
