#!/usr/bin/env python3
import logging

from consolemenu import SelectionMenu  # type: ignore
from pydantic import validate_arguments
from rich import print
from wikibaseintegrator.models import Sense  # type: ignore

from lexutils.helpers import util
from lexutils.helpers.console import console
from lexutils.models.wikidata.enums import WikimediaLanguageCode

# Functions in here only have side-effects and use .format
# because gettext does not work with f-strings

logger = logging.getLogger(__name__)


@validate_arguments
def downloading_from(api_name: str):
    logger.info(f"Downloading from {api_name}...")


def europarl_download():
    raise NotImplementedError("Update to new language chooser")
    # print(("Downloading {} sentence file for {}".format(
    #     europarl.api_name, config.language,
    # )))


def usage_examples_introduction():
    if util.yes_no_question(
        "This script enables you to "
        + "semi-automatically add usage examples to "
        + "lexemes with both good senses and forms "
        + "(with P5137 and grammatical features respectively). "
        + "\nPlease pay attention to the lexical "
        + "category of the lexeme. \nAlso try "
        + "adding only short and concise "
        + "examples to avoid bloat and maximise "
        + "usefulness. \nThis script adds edited "
        + "lexemes (indefinitely) to your watchlist. "
        + "\nContinue?"
    ):
        return True
    else:
        return False


def arbetsformedlingen_historical_job_ads_download():
    print(
        "Downloading 400MB Historical Job Ads data "
        "from the Swedish Public Employment Service"
    )


def select_language_menu():
    # TODO make this scale better.
    #  Consider showing a list based on a sparql result of all wikisource language versions
    menu = SelectionMenu(WikimediaLanguageCode.__members__.keys(), "Select a language")
    menu.show()
    menu.join()
    selected_language_index = menu.selected_option
    mapping = {}
    for index, item in enumerate(WikimediaLanguageCode):
        mapping[index] = item
    selected_language = mapping[selected_language_index]
    logger.debug(f"selected:{selected_language_index}=" f"{selected_language}")
    return selected_language


def print_separator():
    print("----------------------------------------------------------")


def print_run_again_text():
    console.print("No more results. " "Run the script again to continue")


def issue_url():
    return "https://github.com/dpriskorn/LexUtils/issues"


# def add_more_senses_suggestion(form: LexutilsForm = None):
#     if form is None:
#         raise ValueError("form was None")
#     console.print(f"You can add more senses using Orthohin {form.orthohin_url()}")
