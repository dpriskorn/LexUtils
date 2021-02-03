#!/usr/bin/env python3
import gettext

from modules import util

_ = gettext.gettext

def introduction():
    if util.yes_no_question(_("This script enables you to " +
            "semi-automatically add usage examples to " +
            "lexemes with both good senses and forms " +
            "(with P5137 and grammatical features respectively). " +
            "\nPlease pay attention to the lexical " +
            "category of the lexeme. \nAlso try " +
            "adding only short and concise " +
            "examples to avoid bloat and maximise " +
            "usefullness. \nThis script adds edited " +
            "lexemes (indefinitely) to your watchlist. " +
            "\nContinue?")):
        return True
    else:
        return False

def start():
    begin = introduction()
    if begin:
        print(_("Fetching lexeme forms to work on"))
        results = util.fetch_lexeme_forms()
        util.process_lexeme_data(results)
