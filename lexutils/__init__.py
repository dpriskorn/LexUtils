#!/usr/bin/env python3
import gettext
import logging
import warnings

from wikibaseintegrator.wbi_config import config as wbiconfig  # type: ignore

import config
from lexutils.usage_example_session import UsageExamplesSession

# from prompt_toolkit import prompt
# from prompt_toolkit.history import FileHistory
# from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
# from prompt_toolkit.completion import Completer, Completion
# import click
# from fuzzyfinder import fuzzyfinder

# from lexutils.modules import statistics

# Settings
logging.basicConfig(level=config.loglevel)
warnings.simplefilter(action="ignore", category=FutureWarning)
_ = gettext.gettext
Commands = ["examples", "statistics"]


# This is the script that keeps the REPL up


# class Completer(Completer):
#     def get_completions(self, document, complete_event):
#         word_before_cursor = document.get_word_before_cursor(WORD=True)
#         matches = fuzzyfinder(word_before_cursor, Commands)
#         for m in matches:
#             yield Completion(m, start_position=-len(word_before_cursor))


def main():
    wbiconfig["USER_AGENT"] = config.user_agent
    session = UsageExamplesSession()
    session.fetch_and_present_usage_examples()
    # # TODO enable choosing work language
    # print(_('This is the REPL. ' +
    #         'Type one of the names of the tools to begin: ' +
    #         'Examples'))
    # while 1:
    #     user_input = prompt(u'LexUtils>',
    #                         history=FileHistory('history.txt'),
    #                         auto_suggest=AutoSuggestFromHistory(),
    #                         completer=Completer(),
    #                         )
    #     if user_input.lower() == "examples":
    #         # raise Exception("Rewrite to use OOP not finished yet")
    #         dataframe_usage_examples_extractor.start()
    #     if user_input.lower() == "statistics":
    #         statistics.main()
    #     # if user_input.lower() == "lexcombine":
    #     #     print(_('LexCombine has not been implemented yet.'+
    #     #           ' Feel free to help out by sending pull requests'))


if __name__ == "__main__":
    main()
