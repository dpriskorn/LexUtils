#!/usr/bin/env python3
import gettext
import logging
# import random
from time import sleep
from typing import Union, Optional

from rich import print

from lexutils.config import config
from lexutils.config.enums import ReturnValues, SupportedFormPickles
from lexutils.helpers import tui, util
from lexutils.helpers.console import console
from lexutils.helpers.handle_pickles import add_to_pickle
from lexutils.helpers.tui import choose_sense_menu, print_separator, select_language_menu
from lexutils.models.lexemes import Lexemes
from lexutils.models.riksdagen import RiksdagenRecord
from lexutils.models.usage_example import UsageExample
# from lexutils.modules import europarl
# from lexutils.modules import ksamsok
from lexutils.models.wikidata.entities import Lexeme
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.form import Form
from lexutils.models.wikidata.sense import Sense

_ = gettext.gettext


# Program flow
# 
# entrypoint: start()
# show introduction
# let the user choose a language
# instantiate the Lexemes class and fetch examples for all forms while
# ignoring those we already declined or uploaded examples to earlier
# then we loop through each usage example and ask the user if it is suitable by
# calling tui.present_sentence()
# if the user approves it we call add_usage_example() and add it to WD
# save the results to pickles to avoid working on the same form twice


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
    logger = logging.getLogger(__name__)
    # disabled for now
    # begin = introduction()
    begin = True
    if begin:
        choosen_language: WikimediaLanguageCode = select_language_menu()
        # TODO store lexuse_introduction_read=True to e.g. settings.pkl
        with console.status(f"Fetching lexeme forms to work on for {choosen_language.name.title()}"):
            lexemes = Lexemes(language_code=choosen_language.value)
            lexemes.fetch_forms_missing_an_example()
            lexemes.fetch_usage_examples()
        if len(lexemes.forms_with_usage_examples_found) > 0:
            for form in lexemes.forms_with_usage_examples_found:
                result = process_usage_examples(form=form)
                # Save the results to persistent memory
                if result == ReturnValues.SKIP_FORM:
                    add_to_pickle(pickle=SupportedFormPickles.DECLINED_FORMS,
                                  form_id=form.id)
                    continue
                if result == ReturnValues.USAGE_EXAMPLE_ADDED:
                    add_to_pickle(pickle=SupportedFormPickles.FINISHED_FORMS,
                                  form_id=form.id)


def prompt_single_sense(form: Form = None) -> Union[ReturnValues, Sense]:
    if form is None:
        raise ValueError("form was None")
    if config.show_sense_urls:
        question = _("Found only one sense. " +
                     "Does this example fit the following " +
                     "gloss?\n{}\n'{}'".format(form.senses[0].url(),
                                               form.senses[0].gloss))
    else:
        question = _("Found only one sense. " +
                     "Does this example fit the following " +
                     "gloss?\n'{}'".format(form.senses[0].gloss))
    if util.yes_no_question(question):
        return form.senses[0]
    else:
        tui.cancel_sentence(form.representation)
        sleep(config.sleep_time)
        return ReturnValues.SKIP_USAGE_EXAMPLE


def prompt_multiple_senses(form: Form = None) -> Union[ReturnValues, Sense]:
    """Prompt and enable user to choose between multiple senses"""
    if form is None:
        raise ValueError("form was None")
    number_of_senses = len(form.senses)
    print(_("Found {} senses.".format(number_of_senses)))
    sense = None
    # TODO check that all senses has a gloss matching the language of
    # the example
    sense: Union[Sense, None] = choose_sense_menu(form.senses)
    if sense is not None:
        logging.info("a sense was accepted")
        return sense
    else:
        # should this be propagated from prompt_choose_sense() instead?
        return ReturnValues.SKIP_USAGE_EXAMPLE


def choose_sense_handler(
        form: Form = None,
        usage_example: UsageExample = None
) -> Union[ReturnValues, ReturnValues]:
    """Helper to choose a suitable sense for
    the example in question"""
    if form is None:
        raise ValueError("form was None")
    if usage_example is None:
        raise ValueError("usage_example was None")
    logger = logging.getLogger(__name__)
    number_of_senses = len(form.senses)
    logging.info(f"number_of_senses:{number_of_senses}")
    if number_of_senses == 0:
        raise ValueError("Error. Zero senses. this should never be reached " +
                         "if the SPARQL result was sane")
    elif number_of_senses == 1:
        sense_choice = prompt_single_sense(
            form=form
        )
    else:
        sense_choice = prompt_multiple_senses(
            form=form
        )
    # sense_choice: Union[Sense, ReturnValues] = sense_approval_handler(
    #     usage_example=usage_example,
    #     senses=senses,
    #     form=form
    # )
    if isinstance(sense_choice, Sense):
        logger.info("We got a sense that was accepted")
        # Prepare
        if isinstance(usage_example.record, RiksdagenRecord):
            usage_example.record.lookup_qid()
        sense = sense_choice
        lexeme = Lexeme(id=form.lexeme_id)
        # Add
        result = lexeme.add_usage_example(
            form=form,
            sense=sense,
            usage_example=usage_example
        )
        if result is not None:
            logger.info(f"wbi:{sense_choice}")
            print("Successfully added usage example " +
                  f"{lexeme.usage_example_url()}")
            # logger.info("debug exit")
            # exit(0)
            # json_cache.save_to_exclude_list(usage_example)
            return ReturnValues.USAGE_EXAMPLE_ADDED
        else:
            # No result from WBI, what does that mean?
            raise Exception("Error. WBI returned None.")
    else:
        # Pass on return value
        return sense_choice


def handle_usage_example(
        form: Form = None,
        usage_example: UsageExample = None
):
    """This function presents the usage example sentence and
    ask the user to choose a sense that fits if any"""
    if usage_example is None:
        raise ValueError("usage_example was None")
    if form is None:
        raise ValueError("form was None")
    result: ReturnValues = util.yes_no_skip_question(
        tui.found_sentence(
            form=form,
            usage_example=usage_example
        )
    )
    if result is ReturnValues.ACCEPT_USAGE_EXAMPLE:
        # The sentence was accepted
        senses = form.fetch_senses(usage_example=usage_example)
        if len(form.senses) == 0:
            return ReturnValues.SKIP_USAGE_EXAMPLE
        else:
            for sense in form.senses:
                logging.info(sense)
            # raise NotImplementedError("Update to OOP")
            handler_result = choose_sense_handler(
                usage_example=usage_example,
                form=form
            )
            return handler_result
    else:
        # Return the choice
        return result


def process_usage_examples(
        form: Form = None,
) -> Optional[ReturnValues]:
    """Go through each usage example and present it"""
    if form is None:
        raise ValueError("form was None")
    if form.usage_examples is None or len(form.usage_examples) == 0:
        raise ValueError("form had no usage examples")
    logger = logging.getLogger(__name__)
    # Sort so that the shortest sentence is first
    count = 1
    # Sort the usage examples by word count
    # https://stackoverflow.com/questions/403421/how-to-sort-a-list-of-objects-based-on-an-attribute-of-the-objects
    form.usage_examples.sort(key=lambda x: x.word_count, reverse=False)
    # Loop through usage examples
    for example in form.usage_examples:
        tui.present_sentence(
            count=count,
            example=example,
            form=form,
        )
        result = handle_usage_example(
            form=form,
            usage_example=example
        )
        logger.info(f"process_result: result: {result}")
        count += 1
        if result == ReturnValues.SKIP_USAGE_EXAMPLE:
            continue
        elif result == ReturnValues.SKIP_FORM or result == ReturnValues.USAGE_EXAMPLE_ADDED:
            print_separator()
            return result

# def process_result(
#         form: Form = None,
#         lexemelanguage: Lexemes = None
# ) -> Optional[ReturnValues]:
#     """This handles confirmation working on a form and gets usage examples
#     It has only side-effects"""
# 
#     def fetch_usage_examples():
#         tui.number_of_found_sentences(number_of_examples, form=form)
#         if number_of_examples == 0:
#             print_separator()
#         elif number_of_examples > 0:
#             return process_usage_examples(
#                 examples=examples,
#                 form=form
#             )
#         else:
#             print_separator()
# 
#     logger = logging.getLogger(__name__)
#     # ask to continue
#     if config.require_form_confirmation:
#         if yes_no_question(tui.work_on(form=form)):
#             return fetch_usage_examples()
#         else:
#             return ReturnValues.SKIP_FORM
#     else:
#         return fetch_usage_examples()
