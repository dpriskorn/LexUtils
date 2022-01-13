#!/usr/bin/env python3
import gettext
import logging
# import random
from time import sleep
from typing import Union, List, Optional

from rich import print

from lexutils.config import config
from lexutils.config.enums import Choices, Result
from lexutils.helpers import tui, util
from lexutils.helpers.console import console
from lexutils.helpers.tui import choose_sense_menu, print_separator, select_language_menu
from lexutils.helpers.util import add_to_watchlist, yes_no_question
from lexutils.models.riksdagen import RiksdagenRecord
from lexutils.models.usage_example import UsageExample
# from lexutils.modules import download_data
# from lexutils.modules import europarl
# from lexutils.modules import json_cache
# from lexutils.modules import ksamsok
from lexutils.models.wikidata.entities import Lexeme
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.form import Form
from lexutils.models.wikidata.misc import LexemeLanguage
from lexutils.models.wikidata.sense import Sense
from lexutils.modules import historical_job_ads
from lexutils.modules import riksdagen
from lexutils.modules import wikisource

_ = gettext.gettext


# Data flow
# 
# entrypoint: start()
# this fetches lexemes to work on and loop through them in order
# for each one it calls process_result()
# this calls get_sentences_from_apis()
# this goes through the implemented api's and fetch data from them and return
# usage examples
# then we loop through each usage example and ask the user if it is suitable by
# calling tui.present_sentence()
# if the user approves it we call add_usage_example() and add it to WD and the
# lexeme to the users watchlist.


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
        # TODO store lexuse_introduction_read=1 to settings.json
        with console.status(f"Fetching lexeme forms to work on for {choosen_language.name.title()}"):
            lexemelanguage = LexemeLanguage(language_code=choosen_language.value)
            lexemelanguage.fetch_forms_missing_an_example()
        process_forms(lexemelanguage)


def prompt_single_sense(form: Form = None) -> Union[Choices, Sense]:
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
        return Choices.SKIP_USAGE_EXAMPLE


def prompt_multiple_senses(form: Form = None) -> Union[Choices, Sense]:
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
        return Choices.SKIP_USAGE_EXAMPLE


def get_usage_examples_from_apis(
        form: Form = None,
        lexemelanguage: LexemeLanguage = None
) -> List[UsageExample]:
    """Find examples and return them as Example objects"""
    logger = logging.getLogger(__name__)
    examples = []
    # Europarl corpus
    # Download first if not on disk
    # TODO convert to UsageExample
    # download_data.fetch()
    # europarl_records = europarl.get_records(form)
    # for record in europarl_records:
    #     records[record] = europarl_records[record]
    # logger.debug(f"records in total:{len(records)}")
    # ksamsok
    # Disabled because it yields very little of value
    # unfortunately because the data is such low quality overall
    # ksamsok_records = ksamsok.get_records(form)
    # for record in ksamsok_records:
    #     records[record] = ksamsok_records[record]
    # logger.debug(f"records in total:{len(records)}")
    if lexemelanguage.language_code == WikimediaLanguageCode.SWEDISH:
        historical_job_ads_examples: Optional[List[UsageExample]] = \
            historical_job_ads.find_form_representation_in_the_dataframe(
                dataframe=lexemelanguage.historical_ads_dataframe,
                form=form
            )
        if historical_job_ads_examples:
            examples.extend(historical_job_ads_examples)
        # print("debug exit")
        # exit()
        # Riksdagen API is slow, only use it if we don't have a lot of sentences already
        if len(examples) < 25:
            riksdagen_examples: List[UsageExample] = riksdagen.get_records(
                form=form,
                lexemelanguage=lexemelanguage
            )
            examples.extend(riksdagen_examples)
    # Wikisource
    if len(examples) < 50:
        # If we already got 50 examples from a better source,
        # then don't fetch from Wikisource
        with console.status(
                f"Fetching usage examples from the {lexemelanguage.language_code.name.title()} Wikisource..."):
            examples.extend(wikisource.get_records(
                form=form,
                lexemelanguage=lexemelanguage
            ))
    # Check for nested list
    for example in examples:
        if not isinstance(example, UsageExample):
            raise ValueError("Nested list error")
    if len(examples) > 0:
        logger.debug(f"examples found:{[example.text for example in examples]}")
    return examples


def choose_sense_handler(
        form: Form = None,
        usage_example: UsageExample = None
) -> Union[Choices, Result]:
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
    # sense_choice: Union[Sense, Choices] = sense_approval_handler(
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
            if config.add_to_watchlist:
                add_to_watchlist(form.lexeme_id)
            # logger.info("debug exit")
            # exit(0)
            # json_cache.save_to_exclude_list(usage_example)
            return Result.USAGE_EXAMPLE_ADDED
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
    result: Choices = util.yes_no_skip_question(
        tui.found_sentence(
            form=form,
            usage_example=usage_example
        )
    )
    if result is Choices.ACCEPT_USAGE_EXAMPLE:
        # The sentence was accepted
        senses = form.fetch_senses(usage_example=usage_example)
        if len(form.senses) == 0:
            return Choices.SKIP_USAGE_EXAMPLE
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
        examples: List[UsageExample] = None,
        form: Form = None,
) -> Optional[Choices]:
    """Go through each usage example and present it"""
    if form is None:
        raise ValueError("form was None")
    logger = logging.getLogger(__name__)
    if examples is not None:
        # Sort so that the shortest sentence is first
        # raise NotImplementedError("presenting the examples is not implemented yet")
        # TODO How to do this with objects?
        # sorted_sentences = sorted(
        #     examples, key=len,
        # )
        count = 1
        # Sort the usage examples by word count
        # https://stackoverflow.com/questions/403421/how-to-sort-a-list-of-objects-based-on-an-attribute-of-the-objects
        examples.sort(key=lambda x: x.word_count, reverse=False)
        # Loop through usage examples
        for example in examples:
            tui.present_sentence(
                count=count,
                example=example,
                examples=examples
            )
            result = handle_usage_example(
                form=form,
                usage_example=example
            )
            logger.info(f"process_result: result: {result}")
            count += 1
            if result == Choices.SKIP_USAGE_EXAMPLE:
                continue
            elif result == Choices.SKIP_FORM or result == Result.USAGE_EXAMPLE_ADDED:
                print_separator()
                return result
    else:
        raise ValueError("examples was None")


def process_result(
        form: Form = None,
        lexemelanguage: LexemeLanguage = None
) -> Optional[Choices]:
    """This handles confirmation working on a form and gets usage examples
    It has only side-effects"""

    def fetch_usage_examples():
        # Fetch sentence data from all APIs
        examples: List[UsageExample] = get_usage_examples_from_apis(
            form=form,
            lexemelanguage=lexemelanguage
        )
        number_of_examples = len(examples)
        tui.number_of_found_sentences(number_of_examples, form=form)
        if number_of_examples == 0:
            print_separator()
        elif number_of_examples > 0:
            return process_usage_examples(
                examples=examples,
                form=form
            )
        else:
            print_separator()

    logger = logging.getLogger(__name__)
    # ask to continue
    if config.require_form_confirmation:
        if yes_no_question(tui.work_on(form=form)):
            return fetch_usage_examples()
        else:
            return Choices.SKIP_FORM
    else:
        return fetch_usage_examples()


def process_forms(lexemelanguage: LexemeLanguage = None):
    """Process forms into the Form model"""
    logger = logging.getLogger(__name__)
    logger.info("Processing forms")
    # from http://stackoverflow.com/questions/306400/ddg#306417
    # We do this now because we only want to do it once
    # and keep it in memory during the looping through all the forms
    if lexemelanguage.language_code.SWEDISH:
        lexemelanguage.historical_ads_dataframe = historical_job_ads.download_and_load_into_memory()
    earlier_choices = []
    run = True
    while (run):
        if len(earlier_choices) == config.number_of_forms_to_fetch:
            # We have gone checked all results now
            # TODO offer to fetch more
            print("No more results. "
                  "Run the script again to continue")
            run = False
        else:
            # if util.in_exclude_list(data):
            #     # Skip if found in the exclude_list
            #     logging.debug(
            #         f"Skipping result {word} found in exclude_list",
            #     )
            #     continue
            # else:
            # not in exclude_list
            for form in lexemelanguage.forms_without_an_example:
                logging.info(f"processing:{form.representation}")
                if form.lexeme_id is None:
                    raise ValueError("lexeme_id on form was None")
                result = process_result(
                    form=form,
                    lexemelanguage=lexemelanguage
                )
                earlier_choices.append(form)
                if result == Choices.SKIP_FORM:
                    continue
