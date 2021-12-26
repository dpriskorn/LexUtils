#!/usr/bin/env python3
import gettext
import logging

from typing import Dict, List
from urllib.parse import quote

from rich import print

from lexutils import config
from lexutils.config.config import show_sense_urls, wd_prefix
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata import Form, Sense
from lexutils.modules import europarl, util

# from lexutils.modules.examples import _

_ = gettext.gettext


# Functions in here only have side-effects and use .format
# because gettext does not work with f-strings


def downloading_from(api_name):
    print(_("Downloading from {}...".format(api_name)))


def europarl_download():
    print(_("Downloading {} sentence file for {}".format(
        europarl.api_name, config.language,
    )))


def working_on(form: Form):
    features = []
    for feature in form.grammatical_features:
        features.append(feature.name.title())
    print(_("Working on {} ({}) with the features: {}".format(
        form.representation, form.lexeme_category.name.lower(),
        ", ".join(features)
    )))
    print(form.url())


def number_of_found_sentences(dict_length):
    print(_("Found {} suitable sentences".format(
        dict_length,
    )))


def found_sentence(form: Form = None,
                   usage_example: UsageExample = None):
    if usage_example is None:
        raise ValueError("usage_example was None")
    if form is None:
        raise ValueError("form was None")
    # FIXME add grammatical features here
    word_count = util.count_words(usage_example.content)
    return (_("Found the following sentence with {} ".format(word_count) +
              "words. Is it suitable as a usage example " +
              "for the {} form '{}'? \n".format(form.lexeme_category.name.lower(), form.representation) +
              "'{}'".format(usage_example.content)))


def fetching_senses():
    print(_("Fetching senses..."))


def cancel_sentence(word: str):
    # We quote the url because it can contain äöå.
    print(_("Cancelled adding sentence as it does not match the " +
            "only sense currently present. \nLexemes are " +
            "entirely dependent on good quality QIDs. \n" +
            "Please add labels " +
            "and descriptions to relevant QIDs and then use " +
            "MachtSinn to add " +
            "more senses to lexemes by matching on QID concepts " +
            "with similar labels and descriptions in the lexeme " +
            "language." +
            "\nSearch for {} in Wikidata: ".format(word)) +
          quote("https://www.wikidata.org/w/index.php?" +
                "search={}&title=Special%3ASearch&".format(word) +
                "profile=advanced&fulltext=0&" +
                "advancedSearch-current=%7B%7D&ns0=1"))


def prompt_choose_sense(senses: List[Sense] = None):
    """Returns a dictionary with sense_id -> sense_id
    and gloss -> gloss or False"""
    raise NotImplementedError("Update to OOP and TUI library")
    if senses is None:
        raise ValueError("senses was None")
    # TODO use the TUI library from itemsubjector instead
    # from https://stackoverflow.com/questions/23294658/
    # asking-the-user-for-input-until-they-give-a-valid-response
    # while True:
    #     try:
    #         options = _("Please choose the correct sense corresponding " +
    #                     "to the meaning in the usage example")
    #         number = 1
    #         # Put each key -> value into a new nested dictionary
    #         for sense in senses:
    #             options += _(
    #                 "\n{}) {}".format(number, senses[number]['gloss'])
    #             )
    #             if show_sense_urls:
    #                 options += " ({} )".format(
    #                     wd_prefix + senses[number]['sense_id']
    #                 )
    #             number += 1
    #         options += _("\nPlease input a number or 0 to cancel: ")
    #         choice = int(input(options))
    #     except ValueError:
    #         print(_("Sorry, I didn't understand that."))
    #         # better try again... Return to the start of the loop
    #         continue
    #     else:
    #         logging.debug(f"length_of_senses:{len(senses)}")
    #         if choice > 0 and choice <= len(senses):
    #             return {
    #                 "sense_id": senses[choice]["sense_id"],
    #                 "gloss": senses[choice]["gloss"]
    #             }
    #         else:
    #             print(_("Cancelled adding this sentence."))
    #             return False
