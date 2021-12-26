#!/usr/bin/env python3
import gettext
import logging
# import random
from time import sleep
from typing import Union, List

# from lexutils import config
from lexutils.config.config import sparql_results_size, language_code, debug_sentences, show_sense_urls, wd_prefix, \
    sleep_time
from lexutils.config.enums import SupportedExampleSources, Choices
from lexutils.models.riksdagen import RiksdagenRecord
from lexutils.models.usage_example import UsageExample

from lexutils.models.wikidata import LexemeLanguage, Form, Sense, Lexeme
# from lexutils.modules import download_data
# from lexutils.modules import europarl
from lexutils.modules import json_cache
# from lexutils.modules import ksamsok
from lexutils.modules import riksdagen
from lexutils.modules import tui
from lexutils.modules import util
from rich import print

# from lexutils.modules.wdqs import extract_wikibase_value_from_result
from lexutils.modules.tui import prompt_choose_sense
from lexutils.modules.util import add_to_watchlist, yes_no_question
from lexutils.modules.wikidata import fetch_senses

_ = gettext.gettext


# Program flow
#
# Entry through start()

#
# Program flow
#
# Entry through start()
# Fetch data using sparqldataframes
# Call in while loop
#   if not excluded:
#     process_result()
#       Call get_sentences_from_apis()
#         Call europarl.get_records(data)
#         Call riksdagen.get_records(data)
#         Collect records in one big dictionary
#       for loop
#         present_sentence()
#           Sort showing shortest first
#           call prompt_sense_approval()
#             if >1
#               call prompt_choose_sense()
#           Add usage example
#           Add to watchlist
#           Add form to exclude list to avoid duplicates caused by sparql lag
#
# Data flow
# 
# entrypoint: start()
# this fetches lexemes to work on and loop through them in order
# for each one it calls process_result()
# this calls get_sentences_from_apis()
# this goes through the implemented api's and fetch data from them and return
# sentences and their metadata
# then we loop through each sentence and ask the user if it is suitable by
# calling present_sentence()
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
    # rewrite to OOP
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    print(logger.getEffectiveLevel())
    # disabled for now
    # begin = introduction()
    begin = True
    if begin:
        # TODO store lexuse_introduction_read=1 to settings.json
        print(_("Fetching lexeme forms to work on"))
        # logger.debug("Fetching lexeme data")
        logger.info("Fetching forms")
        language = LexemeLanguage("sv")
        language.fetch_forms_missing_an_example()
        # logger.debug(f"forms:{len(language.forms_without_an_example)}")
        # results = fetch_lexeme_data()
        process_forms(language)


def sense_selection_handler():
    pass


def prompt_single_sense(
        form: Form = None,
        senses: List[Sense] = None):
    if form is None:
        raise ValueError("form was None")
    if senses is None:
        raise ValueError("senses was None")
    if show_sense_urls:
        question = _("Found only one sense. " +
                     "Does this example fit the following " +
                     "gloss?\n{}\n'{}'".format(senses[0].url(),
                                               senses[0].gloss))
    else:
        question = _("Found only one sense. " +
                     "Does this example fit the following " +
                     "gloss?\n'{}'".format(senses[0].gloss))
    if util.yes_no_question(question):
        return senses[0]
    else:
        tui.cancel_sentence(form.representation)
        sleep(sleep_time)
        return Choices.SKIP_USAGE_EXAMPLE


def prompt_multiple_senses(senses: List[Sense] = None):
    """Prompt and enable user to choose between multiple senses"""
    number_of_senses = len(senses)
    print(_("Found {} senses.".format(number_of_senses)))
    sense = None
    # TODO check that all senses has a gloss matching the language of
    # the example
    sense: Sense = prompt_choose_sense(senses)
    if sense is not None:
        logging.info("a sense was accepted")
        return sense
    else:
        # should this be propagated from prompt_choose_sense() instead?
        return Choices.SKIP_USAGE_EXAMPLE


# def sense_approval_handler(
#         form: Form = None,
#         senses: List[Sense] = None,
#         usage_example: UsageExample = None,
# ) -> Union[Sense, Choices]:
#     """Prompts for validating that we have a sense matching the use example
#     Calls prompt_single_sense() or prompt_multiple_senses()"""
#     logger = logging.getLogger(__name__)
#     if form is None:
#         raise ValueError("form was None")
#     if senses is None:
#         raise ValueError("senses was None")
#     if usage_example is None:
#         raise ValueError("usage_example was None")
#     # raise NotImplementedError("Update to OOP")
#     number_of_senses = len(senses)
#     logging.info(f"number_of_senses:{number_of_senses}")
#     if number_of_senses == 0:
#         raise ValueError("Error. Zero senses. this should never be reached " +
#                          "if the SPARQL result was sane")
#     elif number_of_senses == 1:
#         return prompt_single_sense(
#             form=form,
#             senses=senses
#         )
#     else:
#         return prompt_multiple_senses(
#             # form=form,
#             senses=senses
#         )


def get_usage_examples_from_apis(
        form: Form = None,
        language: LexemeLanguage = None
) -> List[UsageExample]:
    """Find examples and return them as Example objects"""
    logger = logging.getLogger(__name__)
    examples = []
    # TODO add grammatical features
    tui.working_on(form)
    # logging.info(f"lid:{lid}")
    if language_code == "sv":
        # TODO move to own module for each language modules/lang/sv.py
        records = {}
        # TODO support wiktionary
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
        # Riksdagen API is slow, only use it if we don't have a lot of sentences already
        if len(records) < 50:
            riksdagen_examples: List[UsageExample] = riksdagen.get_records(form)
            examples.extend(riksdagen_examples)
        if debug_sentences:
            logger.debug(f"returning from apis:{examples}")
        return examples
    else:
        raise ValueError(_("Error. Language code: {} not supported. Feel free to" +
                           "open an issue in the repo if you know any sources " +
                           "that have CC0 metadata and useful sentences.".format(
                               language_code,
                           )))


def choose_sense_handler(
        form: Form = None,
        usage_example: UsageExample = None,
        senses: List[Sense] = None
) -> str:
    """Helper to choose a suitable sense for
    the example in question"""
    if form is None:
        raise ValueError("form was None")
    if senses is None:
        raise ValueError("senses was None")
    if usage_example is None:
        raise ValueError("usage_example was None")
    logger = logging.getLogger(__name__)
    number_of_senses = len(senses)
    logging.info(f"number_of_senses:{number_of_senses}")
    if number_of_senses == 0:
        raise ValueError("Error. Zero senses. this should never be reached " +
                         "if the SPARQL result was sane")
    elif number_of_senses == 1:
        sense_choice = prompt_single_sense(
            form=form,
            senses=senses
        )
    else:
        sense_choice = prompt_multiple_senses(
            # form=form,
            senses=senses
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
                  f"to {form.url()}")
            add_to_watchlist(form.lexeme_id)
            # logger.info("debug exit")
            # exit(0)
            # json_cache.save_to_exclude_list(usage_example)
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
            usage_example=usage_example)
    )
    if result is Choices.ACCEPT_USAGE_EXAMPLE:
        # The sentence was accepted
        senses = fetch_senses(form=form)
        logging.info(f"senses found:")
        for sense in senses:
            logging.info(sense)
        # raise NotImplementedError("Update to OOP")
        sense_result = choose_sense_handler(
            usage_example=usage_example,
            senses=senses,
            form=form
        )
        return sense_result
    else:
        # Return the choice
        return result


def process_result(
        form: Form = None,
        language: LexemeLanguage = None
):
    """This has only side-effects"""
    logger = logging.getLogger(__name__)
    # ask to continue
    if yes_no_question(f"\nWork on {form.representation}?"):
        separator = "----------------------------------------------------------"
        # Fetch sentence data from all APIs
        examples: List[UsageExample] = get_usage_examples_from_apis(form, language)
        number_of_examples = len(examples)
        tui.number_of_found_sentences(number_of_examples)
        if number_of_examples == 0:
            print(separator)
        if examples is not None:
            # Sort so that the shortest sentence is first
            # raise NotImplementedError("presenting the examples is not implemented yet")
            # TODO How to do this with objects?
            # sorted_sentences = sorted(
            #     examples, key=len,
            # )
            count = 1
            # Loop through sentence list (that has no result data)
            for example in examples:
                if example.record.source == SupportedExampleSources.RIKSDAGEN:
                    print(_("Presenting sentence " +
                            "{}/{} ".format(count, number_of_examples) +
                            "from {} from {}".format(
                                example.record.date,
                                example.record.url(),
                            )))
                #     elif source == "europarl":
                #         print(_("Presenting sentence " +
                #                 "{}/{} ".format(count, number_of_examples) +
                #                 "from europarl"))
                #     elif source == "ksamsok":
                #         # ksamsok.api_name
                #         print(_("Presenting sentence " +
                #                 "{}/{} ".format(count, len(sorted_sentences)) +
                #                 "from {}".format(ksamsok.baseurl + document_id)))
                # else:
                #     logger.error(_("Internal error. Source is missing. Please report" +
                #                    " this bug."))
                #     exit = True
                #     return True
                result = handle_usage_example(
                    form=form,
                    usage_example=example
                )
                count += 1
                if result == Choices.SKIP_USAGE_EXAMPLE:
                    continue
                elif result == Choices.SKIP_FORM:
                    print(separator)
                    return result
        elif number_of_examples == 0:
            print(separator)
        else:
            print(separator)


def process_forms(language: LexemeLanguage = None):
    """Process forms into the Form model"""
    logger = logging.getLogger(__name__)
    logger.info("Processing forms")
    # from http://stackoverflow.com/questions/306400/ddg#306417
    earlier_choices = []
    run = True
    while (run):
        if len(earlier_choices) == sparql_results_size:
            # We have gone checked all results now
            # TODO offer to fetch more
            print("No more results. "
                  "Run the script again to continue")
            exit(0)
        else:
            # if util.in_exclude_list(data):
            #     # Skip if found in the exclude_list
            #     logging.debug(
            #         f"Skipping result {word} found in exclude_list",
            #     )
            #     continue
            # else:
            # not in exclude_list
            for form in language.forms_without_an_example:
                logging.info(f"processing:{form.representation}")
                if form.lexeme_id is None:
                    raise ValueError("lexeme_id on form was None")
                exit = process_result(
                    form=form,
                    language=language
                )
                earlier_choices.append(form)
                # if exit:
                #     run = False

# def fetch_and_process_dataframes():
#     # fetch lexeme data
#     df = fetch_lexeme_data()
#     if len(df) == 0:
#         print(_("No suitable lexemes found. Please add senses and P5137 to"+
#                 " lexemes and run the program again."))
#         exit(0)
#     # group forms by formid
#     forms = df.groupby("formid")["feature"].apply(', '.join).reset_index()
#     # They are ordered from F1-~
#     # Loop through the rows
#     # https://stackoverflow.com/a/36394939
#     for index, row in forms.iterrows():
#         formid = row["formid"]
#         # find index where formid appears in the original df
#         dfindex = df.index[df["formid"] == formid].tolist()[0]
#         #print(f"dfindex: {dfindex}")
#         word = df.loc[dfindex]["word"]
#         lid = df.loc[dfindex]["lid"]
#         features = row["feature"]
#         category = df.loc[dfindex]["category"]
#         print(lid, formid, features, category, word)
#         # print(list(df))
#         #  Check if word is in exlude list and find example sentence if not
#         if util.in_exclude_list(dict(
#                 formid=formid,
#                 word=word,
#                 lid=lid)):
#             # Skip if found in the exclude_list
#             logging.debug(
#                 f"Skipping result {word} found in exclude_list",
#             )
#             continue
#         else:
#             # not in exclude_list
#             logging.debug(f"processing:{word}")
#             senses = df.loc[df.lid == lid].groupby("senseid")
#             exit = process_result(
#                 #result=result,
#                 data=dict(
#                     formid=formid,
#                     word=word,
#                     features=features,
#                     category=category,
#                     lid=lid,
#                     senses=senses,  # dataframe
#                 ),
#             )
#         #  present example
#         # print(type(senses))
#         # print(senses)
#         # print(list(senses))
#         # We don't need to worry about length because the SPARQL query only
#         # returns lexemes with at least one sense. :)
#         # print("Senses:")
#         # for sense in senses:
#         #     # print("printing sense")
#         #     # print(sense)
#         #     # Extract first part of tuple which has the senseid
#         #     senseid = sense[0]
#         #     # Pick from group df the first (outputs a series) and take the
#         #     # second part. Reset the index and get the gloss from the first frame
#         #     gloss = sense[1].reset_index().at[0,"gloss"]
#         #     # print(type(gloss))
#         #     print(f"{senseid}: {gloss}")
#         #  upload
#         #  save to exclude list
#         # json_cache.save_to_exclude_list(dict(formid=formid,
#         #                                      word=word)
#
#     exit(0)
#
#     # get dataframes from Wikidata
#     # df = wikidata.fetch_lexeme_forms()
#     #import pandas as pd
#     #pd.set_option("display.max_columns", 10)
#     # print(df.sample(n=1))
#     # print(df.describe())
#     # print(list(df))
#     #grouped= df.groupby("lid", "senseid", "formid")
#     #senses = df.groupby("lid", "senseid")
#     # print(forms)
#     # print(list(forms))
