#!/usr/bin/env python3
import gettext
import logging
import random
from time import sleep
from typing import Dict, Union

import config
from modules import download_data
from modules import europarl
from modules import json_cache
from modules import ksamsok
from modules import riksdagen
from modules import tui
from modules import util
from modules import wikidata
from rich import print

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
    logger = logging.getLogger(__name__)
    begin = introduction()
    if begin:
        # TODO store lexuse_introduction_read=1 to settings.json
        print(_("Fetching lexeme forms to work on"))
        if config.use_dataframes == True:
            fetch_and_process_dataframes()
            print(_("You have processed all the fetched lexemes. " +
                    "Run LexUse again to continue working"))
            # fetch more lexeme data?
            # answer = util.yes_no_question("Fetch more lexemes to work on?")
            # if answer != "":
            #    pass 
            
        else:
            logger.debug("Fetching lexeme data")
            results = wikidata.fetch_lexeme_data()
            process_lexeme_data(results)


def prompt_sense_approval(
        sentence: str = None,
        data: Dict[str, Dict[str, str]] = None,
        senses: Dict[str, str] = None,
) -> Union[Dict,str]:
    """Prompts for validating that we have a sense matching the use example
    return dictionary with sense_id and sense_gloss if approved else False"""
    logger = logging.getLogger(__name__)
    # TODO split this up in multiple functions
    # ->prepare_sense_selection()
    # + prompt_single_sense()
    # + prompt_multiple_senses()
    lid = data["lid"]
    number_of_senses = len(senses)
    logging.debug(f"number_of_senses:{number_of_senses}")
    if number_of_senses == 0:
        logging.error("Error. Zero senses. this should never be reached " +
                      "if the SPARQL result was sane")
        sleep(config.sleep_time)
        return "error"
    elif number_of_senses == 1:
        gloss = senses[1]["gloss"]
        sense_id = senses[1]["sense_id"]
        if config.show_sense_urls:
            question = _("Found only one sense. " +
                         "Does this example fit the following " +
                         "gloss?\n{}\n'{}'".format(wd_prefix + sense_id,
                                                  gloss))
        else:
            question = _("Found only one sense. " +
                        "Does this example fit the following " +
                         "gloss?\n'{}'".format(gloss))
        if util.yes_no_question(question):
            return {
                "sense_id": senses[1]["sense_id"],
                "sense_gloss": gloss
            }
        else:
            word = data['word']
            tui.cancel_sentence(word)
            sleep(config.sleep_time)
            return "skip_sentence"
    else:
        print(_("Found {} senses.".format(number_of_senses)))
        sense = None
        # TODO check that all senses has a gloss matching the language of
        # the example
        sense = prompt_choose_sense(senses)
        if sense is not None:
            logging.debug("sense was accepted")
            return {
                "sense_id": sense["sense_id"],
                "sense_gloss": sense["gloss"]
            }
        else:
            return "skip_sentence"

        
def get_sentences_from_apis(data: Dict[str, str]) -> Dict:
    """Returns a dict with sentences as key and id as value"""
    logger = logging.getLogger(__name__)
    formid = data["formid"]
    word = data["word"]
    category = data["category"]
    lid = data["lid"]
    features = data["features"]
    # TODO add grammatical features
    tui.working_on(word=word,
                   category=category,
                   features=features)
    logging.info(f"lid:{lid}")
    if config.language_code == "sv":
        # TODO move to own module for each language modules/lang/sv.py
        records = {}
        # Europarl corpus
        # Download first if not on disk
        download_data.fetch()
        europarl_records = europarl.get_records(data)
        for record in europarl_records:
            records[record] = europarl_records[record]
        logger.debug(f"records in total:{len(records)}")
        # ksamsok
        ksamsok_records = ksamsok.get_records(data)
        for record in ksamsok_records:
            records[record] = ksamsok_records[record]
        logger.debug(f"records in total:{len(records)}")
        # Riksdagen API is slow, only use it if we don't have a lot of sentences already
        if (len(europarl_records) + len(ksamsok_records)) < 50:
            riksdagen_records = riksdagen.get_records(data)
            for record in riksdagen_records:
                records[record] = riksdagen_records[record]
        if config.debug_sentences:
            logger.debug(f"returning from apis:{records}")
        return records
    else:
        logging.error(_("Error. Language code: {} not supported. Feel free to"+
                        "open an issue in the repo if you know any sources "+
                        "that have CC0 metadata and useful sentences.".format(
            config.language_code,
        )))
        exit(1)
    # TODO add wikisource


def prompt_choose_sense(senses):
    """Returns a dictionary with sense_id -> sense_id
    and gloss -> gloss or False"""
    # from https://stackoverflow.com/questions/23294658/
    # asking-the-user-for-input-until-they-give-a-valid-response
    while True:
        try:
            options = _("Please choose the correct sense corresponding " +
                        "to the meaning in the usage example")
            number = 1
            # Put each key -> value into a new nested dictionary
            for sense in senses:
                options += _(
                    "\n{}) {}".format(number, senses[number]['gloss'])
                )
                if config.show_sense_urls:
                    options += " ({} )".format(
                        wd_prefix + senses[number]['sense_id']
                    )
                number += 1
            options += _("\nPlease input a number or 0 to cancel: ")
            choice = int(input(options))
        except ValueError:
            print(_("Sorry, I didn't understand that."))
            # better try again... Return to the start of the loop
            continue
        else:
            logging.debug(f"length_of_senses:{len(senses)}")
            if choice > 0 and choice <= len(senses):
                return {
                    "sense_id": senses[choice]["sense_id"],
                    "gloss": senses[choice]["gloss"]
                }
            else:
                print(_("Cancelled adding this sentence."))
                return False

def choose_sense(sentence: str, data: Dict, senses: Dict) -> str:
    logger = logging.getLogger(__name__)
    result = prompt_sense_approval(
        sentence=sentence,
        data=data,
        senses=senses,
    )
    if result is Dict:
        lid = data["lid"]
        sense_id = result["sense_id"]
        sense_gloss = result["sense_gloss"]
        if (sense_id is not None and sense_gloss is not None):
            logger.debug("sense_id:{sense_id}")
            logger.debug("sense_gloss:{sense_gloss}")
            result = None
            result = wikidata.add_usage_example(
                # FIXME where is the document_id?
                document_id=document_id,
                sentence=sentence,
                lid=lid,
                formid=data["formid"],
                sense_id=sense_id,
                word=data["word"],
                publication_date=date,
                language_style=language_style,
                type_of_reference=type_of_reference,
                source=source,
                line=line,
            )
            if result is not None:
                logger.debug(f"wbi:{result}")
                print("Successfully added usage example " +
                      f"to {wd_prefix + lid}")
                wikidata.add_to_watchlist(lid)
                json_cache.save_to_exclude_list(data)
                return "added" 
            else:
                # No result from WBI, what does that mean?
                logger.error("Error. WBI returned None.")
                exit(1)
        else:
            logger.error("Error. sense id and or gloss not found."+
                         "Please report an issue.")
            sleep(config.sleep_time)
            return "error"
    else:
        # Pass on return value
        return result

            
def present_sentence(
        data: dict = None,
        sentence: str = None,
        document_id: str = None,
        date: str = None,
        language_style: str = None,
        type_of_reference: str = None,
        source: str = None,
        line: str = None
):
    """This function presents the sentence and ask the user to choose a sense
    that fits if any"""
    # TODO improve return from this function
    lid = data["lid"]
    word_count = util.count_words(sentence)
    result = util.yes_no_skip_question(
           tui.found_sentence(word_count, data, sentence) 
    )
    skipped = False
    if result is False:
        return "skip_sentence"
    elif result is None:
        return "skip_form"
    if result is True:
        # The sentence was accepted
        raise ValueError("Not finished")
        senses = sparql.fetch_senses(lid)
        sense_result = choose_sense(sentence, data, senses)
        return sense_result


def process_result(
#        result: str,
        data: Dict,
):
    """This has only side-effects"""
    logger = logging.getLogger(__name__)
    # ask to continue
    # if yes_no_question(f"\nWork on {data['word']}?"):
    # This dict holds the sentence as key and
    # riksdagen_document_id or other id as value
    separator = "----------------------------------------------------------"
    # Fetch sentence data from all APIs
    sentences_and_result_data = get_sentences_from_apis(data)
    dict_length = len(sentences_and_result_data)
    tui.number_of_found_sentences(dict_length)
    if dict_length == 0:
        print(separator)
    if sentences_and_result_data is not None:
        # Sort so that the shortest sentence is first
        sorted_sentences = sorted(
            sentences_and_result_data, key=len,
        )
        count = 1
        # Loop through sentence list (that has no result data)
        for sentence in sorted_sentences:
            # We lookup the sentence in the original dict to get the
            # result_data
            result_data = sentences_and_result_data[sentence]
            document_id = result_data["document_id"]
            date = result_data["date"]
            style = result_data["language_style"]
            medium = result_data["type_of_reference"]
            source = result_data["source"]
            line = result_data["line"]
            if source == "riksdagen":
                print(_("Presenting sentence " +
                        "{}/{} ".format(count, dict_length) +
                        "from {} from {}".format(
                            date, riksdagen.baseurl + document_id,
                        )))
            elif source == "europarl":
                print(_("Presenting sentence " +
                        "{}/{} ".format(count, dict_length) +
                        "from europarl"))
            elif source == "ksamsok":
                # ksamsok.api_name
                print(_("Presenting sentence " +
                        "{}/{} ".format(count, len(sorted_sentences)) +
                        "from {}".format(ksamsok.baseurl + document_id)))
            else:
                logger.error(_("Internal error. Source is missing. Please report"+
                               " this bug."))
                exit = True
                return exit
            logging.info(f"with style: {style} " +
                         f"and medium: {medium}")
            result = present_sentence(
                data=data,
                # Trim sentence
                sentence=sentence.strip(),
                document_id=document_id,
                date=date,
                language_style=style,
                type_of_reference=medium,
                source=source,
                line=line,
            )
            count += 1
            if result == "skip_sentence":
                continue
            if result == "skip_form" or result == "error":
                print(separator)
                return result
    elif dict_length == 0:
        print(separator)
    else:
        print(separator)


def process_lexeme_data(results):
    """Go through the SPARQL results randomly"""
    words = []
    for result in results:
        words.append(wikidata.extract_wikibase_value(result, "word"))
    print(f"Got {len(words)} suitable forms from Wikidata")
    logging.debug(f"words:{words}")
    # Go through the results at random
    print("Going through the list of forms at random.")
    # from http://stackoverflow.com/questions/306400/ddg#306417
    earlier_choices = []
    run = True
    while (run):
        if len(earlier_choices) == config.sparql_results_size:
            # We have gone checked all results now
            # TODO offer to fetch more
            print("No more results. Run the script again to continue")
            exit(0)
        else:
            # Select a lexeme randomly
            result = random.choice(results)
            # Prevent running more than once for each result
            if result not in earlier_choices:
                earlier_choices.append(result)
                data = util.extract_lexeme_forms_data(result)
                word = data['word']
                logging.debug(f"random choice:{word}")
                if util.in_exclude_list(data):
                    # Skip if found in the exclude_list
                    logging.debug(
                        f"Skipping result {word} found in exclude_list",
                    )
                    continue
                else:
                    # not in exclude_list
                    logging.debug(f"processing:{word}")
                    exit = process_result(
                        result=result,
                        data=data,
                    )
                    if exit:
                        run = False

def fetch_and_process_dataframes():
    # fetch lexeme data
    df = wikidata.fetch_lexeme_data()
    if len(df) == 0:
        print(_("No suitable lexemes found. Please add senses and P5137 to"+
                " lexemes and run the program again."))
        exit(0)
    # group forms by formid
    forms = df.groupby("formid")["feature"].apply(', '.join).reset_index()
    # They are ordered from F1-~
    # Loop through the rows
    # https://stackoverflow.com/a/36394939
    for index, row in forms.iterrows():
        formid = row["formid"]
        # find index where formid appears in the original df
        dfindex = df.index[df["formid"] == formid].tolist()[0]
        #print(f"dfindex: {dfindex}")
        word = df.loc[dfindex]["word"]
        lid = df.loc[dfindex]["lid"]
        features = row["feature"]
        category = df.loc[dfindex]["category"]
        print(lid, formid, features, category, word)
        # print(list(df))
        #  Check if word is in exlude list and find example sentence if not
        if util.in_exclude_list(dict(
                formid=formid,
                word=word,
                lid=lid)):
            # Skip if found in the exclude_list
            logging.debug(
                f"Skipping result {word} found in exclude_list",
            )
            continue
        else:
            # not in exclude_list
            logging.debug(f"processing:{word}")
            senses = df.loc[df.lid == lid].groupby("senseid")
            exit = process_result(
                #result=result,
                data=dict(
                    formid=formid,
                    word=word,
                    features=features,
                    category=category,
                    lid=lid,
                    senses=senses,  # dataframe
                ),
            )
        #  present example
        # print(type(senses))
        # print(senses)
        # print(list(senses))
        # We don't need to worry about length because the SPARQL query only
        # returns lexemes with at least one sense. :)
        # print("Senses:")
        # for sense in senses:
        #     # print("printing sense")
        #     # print(sense)
        #     # Extract first part of tuple which has the senseid
        #     senseid = sense[0]
        #     # Pick from group df the first (outputs a series) and take the
        #     # second part. Reset the index and get the gloss from the first frame 
        #     gloss = sense[1].reset_index().at[0,"gloss"]
        #     # print(type(gloss))
        #     print(f"{senseid}: {gloss}")
        #  upload
        #  save to exclude list
        # json_cache.save_to_exclude_list(dict(formid=formid,
        #                                      word=word)
        
    exit(0)
    
    # get dataframes from Wikidata
    # df = wikidata.fetch_lexeme_forms()
    #import pandas as pd
    #pd.set_option("display.max_columns", 10)
    # print(df.sample(n=1))
    # print(df.describe())
    # print(list(df))
    #grouped= df.groupby("lid", "senseid", "formid")
    #senses = df.groupby("lid", "senseid")
    # print(forms)
    # print(list(forms))
