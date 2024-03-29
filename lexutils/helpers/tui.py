#!/usr/bin/env python3
from __future__ import annotations

import gettext
import logging
from typing import List, TYPE_CHECKING

from consolemenu import *
from rich import print

from lexutils.config import constants
from lexutils.helpers import util
from lexutils.helpers.console import console
from lexutils.models.historical_job_ads_record import HistoricalJobAd
from lexutils.models.riksdagen_record import RiksdagenRecord
from lexutils.models.wikidata.enums import WikimediaLanguageCode

if TYPE_CHECKING:
    from lexutils.models.usage_example import UsageExample
    from lexutils.models.wikidata.form import Form
    from lexutils.models.wikidata.sense import Sense

_ = gettext.gettext


# Functions in here only have side-effects and use .format
# because gettext does not work with f-strings

logger = logging.getLogger(__name__)


def downloading_from(api_name):
    logger.info(_("Downloading from {}...".format(api_name)))


def europarl_download():
    raise NotImplementedError("Update to new language chooser")
    # print(_("Downloading {} sentence file for {}".format(
    #     europarl.api_name, config.language,
    # )))


def arbetsformedlingen_historical_job_ads_download():
    print("Downloading 400MB Historical Job Ads data "
          "from the Swedish Public Employment Service")


def work_on(form: Form = None):
    return (
            "Work on {} ({}) with the features: {}".format(
                form.representation, form.lexeme_category,
                ", ".join(form.grammatical_features)
            ) +
            f"\n{form.hangor_url()}"
    )


def number_of_found_sentences(number_of_usage_examples: int = None,
                              form: Form = None):
    print(_("Found {} suitable sentences for {} with id "
            "{} and the grammatical features: {}".format(
        number_of_usage_examples, form.representation, form.id, " ".join(form.grammatical_features)
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
              "for the {} form '{}'? \n".format(form.lexeme_category, form.representation) +
              "'{}'".format(usage_example.text)))


def cancel_sentence(form: Form = None):
    if form is None:
        raise ValueError("form was None")
    console.print(
        "Cancelled adding sentence as it does not match the " +
        "sense(s) currently present. \n"
        "[bold]List of recommended tools to improve the lexemes:[/bold]\n"
        f"* [bold]Hangor[/bold]: tool to add senses to this "
        f"form manually {form.hangor_url()}\n"
        f"* [bold]MachtSinn[/bold]: tool to match lexemes with QIDs "
        f"{constants.machtsinn} Warning: This tool is neither well "
        f"maintained nor updated so if be very careful when using it.\n"
        f"* [bold]Orthohin[/bold]: tool to add senses manually "
        f"to any lexeme in a certain language {form.orthohin_url()}\n"
    )


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
        if index > (len(senses) - 1):
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
        form: Form = None
):
    if example is None:
        raise ValueError("example was None")
    if example.record is None:
        raise ValueError("record was None")
    if form is None:
        raise ValueError("form was None")
    if isinstance(example.record, RiksdagenRecord):
        console.print(_("Presenting sentence " +
                        "{}/{} ".format(count, form.number_of_examples_found) +
                        "from {} from {}".format(
                            example.record.date,
                            example.record.human_readable_url(),
                        )))
    elif isinstance(example.record, HistoricalJobAd):
        console.print(_("Presenting sentence " +
                        "{}/{} ".format(count, form.number_of_examples_found) +
                        "with id {} from {}".format(
                            example.record.id,
                            example.record.human_readable_url(),
                        )))
    else:
        console.print(_("Presenting sentence " +
                        "{}/{} ".format(count, form.number_of_examples_found) +
                        "from {}".format(
                            example.record.human_readable_url(),
                        )))


def run_again():
    console.print("No more results. "
                  "Run the script again to continue")


def issue_url():
    return "https://github.com/dpriskorn/LexUtils/issues"


def present_form(form):
    console.print(form.presentation())


# def add_more_senses_suggestion(form: Form = None):
#     if form is None:
#         raise ValueError("form was None")
#     console.print(f"You can add more senses using Orthohin {form.orthohin_url()}")