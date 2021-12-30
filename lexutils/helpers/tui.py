#!/usr/bin/env python3
from __future__ import annotations
import gettext
import logging

from typing import List, TYPE_CHECKING
from urllib.parse import quote

from consolemenu import *
from rich import print

from lexutils.config import config
from lexutils.helpers.console import console
from lexutils.models.riksdagen import RiksdagenRecord
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.modules import europarl
from lexutils.helpers import util

if TYPE_CHECKING:
    from lexutils.models.usage_example import UsageExample
    from lexutils.models.wikidata.form import Form
    from lexutils.models.wikidata.sense import Sense

_ = gettext.gettext


# Functions in here only have side-effects and use .format
# because gettext does not work with f-strings


def downloading_from(api_name):
    print(_("Downloading from {}...".format(api_name)))


def europarl_download():
    raise NotImplementedError("Update to new language chooser")
    print(_("Downloading {} sentence file for {}".format(
        europarl.api_name, config.language,
    )))


def working_on(form: Form):
    features = []
    for feature in form.grammatical_features:
        features.append(feature.value)
    print(_(
        "Working on {} ({}) with the features: {}".format(
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
    word_count = util.count_words(usage_example.text)
    return (_("Found the following sentence with {} ".format(word_count) +
              "words. Is it suitable as a usage example " +
              "for the {} form '{}'? \n".format(form.lexeme_category.name.lower(), form.representation) +
              "'{}'".format(usage_example.text)))


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


def choose_sense_menu(senses: List[Sense] = None):
    """Returns a dictionary with sense_id -> sense_id
    and gloss -> gloss or False"""
    logger = logging.getLogger(__name__)
    # raise NotImplementedError("Update to OOP and TUI library")
    if senses is None:
        raise ValueError("senses was None")
    menu = SelectionMenu(senses, "Select a sense")
    menu.show()
    menu.join()
    index = menu.selected_option
    # logger.debug(f"index:{index}")
    # exit(0)
    if index is not None:
        logger.debug(f"selected:{index}")
        if index == len(senses) + 1:
            logger.debug("No sense was chosen")
            return None
        else:
            selected_item = senses[index]
            logger.debug("Returning the chosen sense")
            return selected_item


def select_language_menu():
    # TODO make this scale better.
    #  Consider showing a list based on a sparql result of all wikisource language versions
    logger = logging.getLogger(__name__)
    menu = SelectionMenu(WikimediaLanguageCode.__members__.keys(), "Select a language")
    menu.show()
    menu.join()
    selected_language_index = menu.selected_option
    mapping = {}
    for index, item in enumerate(WikimediaLanguageCode):
        mapping[index] = item
    selected_language = mapping[selected_language_index]
    logger.debug(f"selected:{selected_language_index}="
                 f"{selected_language}")
    return selected_language


def print_separator():
    print("----------------------------------------------------------")


def present_sentence(
        count: int = None,
        example: UsageExample = None,
        examples: List[UsageExample] = None
):
    if example is None:
        raise ValueError("example was None")
    if example.record is None:
        raise ValueError("record was None")
    if isinstance(example.record, RiksdagenRecord):
        console.print(_("Presenting sentence " +
                        "{}/{} ".format(count, len(examples)) +
                        "from {} from {}".format(
                            example.record.date,
                            example.record.url(),
                        )))
    else:
        console.print(_("Presenting sentence " +
                        "{}/{} ".format(count, len(examples)) +
                        "from {}".format(
                            example.record.url(),
                        )))
