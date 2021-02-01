#!/usr/bin/env python3
from datetime import datetime, timezone
import json
import logging
import os.path
import random
import sys
import time
# import asyncio
import httpx
from typing import Dict
from wikibaseintegrator import wbi_core, wbi_login

import config
from modules import download_data
from modules import europarl
from modules import loglevel
from modules import riksdagen
from modules import ksamsok

# Terminology used
# record = sentence + data
# sentence = string of text usable as a usage example on a lexeme in WD

# Data flow
# entrypoint: process_lexeme_data()
# this fetches lexemes to work on and loop through them randomly
# for each one it calls process_result()
# this calls get_sentences_from_apis()
# this goes through the implemented api's and fetch data from them and return
# sentences and their metadata
# then we loop through each sentence and ask the user if it is suitable by
# calling present_sentence()
# if the user approves it we call add_usage_example() and add it to WD and the
# lexeme to the users watchlist.

# Check version
try:
    assert sys.version_info >= (3, 7)
except AssertionError:
    print("Error! This script requires Python 3.7 minimum. " +
          f"Your version of python: {sys.version[0:5]} " +
          "is very old and not " +
          "supported by this script. Please upgrade python. " +
          "If you are on Ubuntu 18.04 we encourage you to upgrade Ubuntu.")
    exit(0)

# Logging
logger = logging.getLogger(__name__)
if config.loglevel is None:
    # Set loglevel
    print("Setting loglevel in config")
    loglevel.set_loglevel()
logger.setLevel(config.loglevel)
logger.level = logger.getEffectiveLevel()
file_handler = logging.FileHandler("util.log")
logger.addHandler(file_handler)

# Constants
wd_prefix = "http://www.wikidata.org/entity/"

#
# Program flow
#
# Entry through process_lexeme_data()
# Call in while loop
#   if not excluded:
#     process_result()
#       Call get_sentences_from_apis()
#         Call europarl..get_records(data)
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


def yes_no_skip_question(message: str):
    # https://www.quora.com/
    # I%E2%80%99m-new-to-Python-how-can-I-write-a-yes-no-question
    # this will loop forever
    while True:
        answer = input(message + ' [(Y)es/(n)o/(s)kip this form]: ')
        if len(answer) == 0 or answer[0].lower() in ('y', 'n', 's'):
            if len(answer) == 0:
                return True
            elif answer[0].lower() == 's':
                return None
            else:
                # the == operator just returns a boolean,
                return answer[0].lower() == 'y'


def yes_no_question(message: str):
    # https://www.quora.com/
    # I%E2%80%99m-new-to-Python-how-can-I-write-a-yes-no-question
    # this will loop forever
    while True:
        answer = input(message + ' [Y/n]: ')
        if len(answer) == 0 or answer[0].lower() in ('y', 'n'):
            if len(answer) == 0:
                return True
            else:
                # the == operator just returns a boolean,
                return answer[0].lower() == 'y'


def sparql_query(query):
    # from https://stackoverflow.com/questions/55961615/
    # how-to-integrate-wikidata-query-in-python
    url = 'https://query.wikidata.org/sparql'
    r = httpx.get(url, params={'format': 'json', 'query': query})
    data = r.json()
    # pprint(data)
    results = data["results"]["bindings"]
    # pprint(results)
    if len(results) == 0:
        print(f"No {config.language} lexemes containing " +
              "both a sense, forms with " +
              "grammatical features and missing a usage example was found")
        exit(0)
    else:
        return results


def count_number_of_senses_with_P5137(lid):
    """Returns an int"""
    result = (sparql_query(f'''
    SELECT
    (COUNT(?sense) as ?count)
    WHERE {{
      VALUES ?l {{wd:{lid}}}.
      ?l ontolex:sense ?sense.
      ?sense skos:definition ?gloss.
      # Exclude lexemes without a linked QID from at least one sense
      ?sense wdt:P5137 [].
    }}'''))
    count = int(result[0]["count"]["value"])
    logging.debug(f"count:{count}")
    return count


def fetch_senses(lid):
    """Returns dictionary with numbers as keys and a dictionary as value with
    sense id and gloss"""
    # Thanks to Lucas Werkmeister https://www.wikidata.org/wiki/Q57387675 for
    # helping with this query.
    result = (sparql_query(f'''
    SELECT
    ?sense ?gloss
    WHERE {{
      VALUES ?l {{wd:{lid}}}.
      ?l ontolex:sense ?sense.
      ?sense skos:definition ?gloss.
      # Get only the swedish gloss, exclude otherwise
      FILTER(LANG(?gloss) = "{config.language_code}")
      # Exclude lexemes without a linked QID from at least one sense
      ?sense wdt:P5137 [].
    }}'''))
    senses = {}
    number = 1
    for row in result:
        senses[number] = {
            "sense_id": row["sense"]["value"].replace(wd_prefix, ""),
            "gloss": row["gloss"]["value"]
        }
        number += 1
    logging.debug(f"senses:{senses}")
    return senses


def fetch_lexeme_forms():
    return sparql_query(f'''
    SELECT DISTINCT
    ?l ?form ?word ?catLabel
    WHERE {{
      ?l a ontolex:LexicalEntry; dct:language wd:{config.language_qid}.
      VALUES ?excluded {{
        # exclude affixes and interfix
        wd:Q62155 # affix
        wd:Q134830 # prefix
        wd:Q102047 # suffix
        wd:Q1153504 # interfix
      }}
      MINUS {{?l wdt:P31 ?excluded.}}
      ?l wikibase:lexicalCategory ?cat.

      # We want only lexemes with both forms and at least one sense
      ?l ontolex:lexicalForm ?form.
      ?l ontolex:sense ?sense.

      # Exclude lexemes without a linked QID from at least one sense
      ?sense wdt:P5137 [].

      # This remove all lexemes with at least one example which is not
      # ideal
      MINUS {{?l wdt:P5831 ?example.}}
      ?form wikibase:grammaticalFeature [].
      # We extract the word of the form
      ?form ontolex:representation ?word.
      SERVICE wikibase:label
      {{ bd:serviceParam wikibase:language "en". }}
    }}
    limit {config.sparql_results_size}
    offset {config.sparql_offset}
    ''')


def extract_data(result):
    lid = result["l"]["value"].replace(
        wd_prefix, ""
    )
    form_id = result["form"]["value"].replace(
        wd_prefix, ""
    )
    word = result["word"]["value"]
    word_spaces = " " + word + " "
    word_angle_parens = ">" + word + "<"
    category = result["catLabel"]["value"]
    return dict(
        lid=lid,
        form_id=form_id,
        word=word,
        word_spaces=word_spaces,
        word_angle_parens=word_angle_parens,
        category=category
    )


async def async_fetch_from_url(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response


def add_usage_example(
        document_id=None,
        sentence=None,
        lid=None,
        form_id=None,
        sense_id=None,
        word=None,
        publication_date=None,
        language_style=None,
        type_of_reference=None,
        source=None,
        line=None,
):
    # Use WikibaseIntegrator aka wbi to upload the changes in one edit
    link_to_form = wbi_core.Form(
        prop_nr="P5830",
        value=form_id,
        is_qualifier=True
    )
    link_to_sense = wbi_core.Sense(
        prop_nr="P6072",
        value=sense_id,
        is_qualifier=True
    )
    if language_style == "formal":
        style = "Q104597585"
    else:
        if language_style == "informal":
            style = "Q901711"
        else:
            print(f"Error. Language style {language_style} " +
                  "not one of (formal,informal)")
            exit(1)
    logging.debug("Generating qualifier language_style " +
                  f"with {style}")
    language_style_qualifier = wbi_core.ItemID(
        prop_nr="P6191",
        value=style,
        is_qualifier=True
    )
    # oral or written
    if type_of_reference == "written":
        medium = "Q47461344"
    else:
        if type_of_reference == "oral":
            medium = "Q52946"
        else:
            print(f"Error. Type of reference {type_of_reference} " +
                  "not one of (written,oral)")
            exit(1)
    logging.debug("Generating qualifier type of reference " +
                  f"with {medium}")
    type_of_reference_qualifier = wbi_core.ItemID(
        prop_nr="P3865",
        value=medium,
        is_qualifier=True
    )
    if source == "riksdagen":
        if publication_date is not None:
            publication_date = datetime.fromisoformat(publication_date)
        else:
            print("Publication date of document {document_id} " +
                  "is missing. We have no fallback for that at the moment. " +
                  "Abort adding usage example.")
            return False
        stated_in = wbi_core.ItemID(
            prop_nr="P248",
            value="Q21592569",
            is_reference=True
        )
        document_id = wbi_core.ExternalID(
            prop_nr="P8433",  # Riksdagen Document ID
            value=document_id,
            is_reference=True
        )
        reference = [
            stated_in,
            document_id,
            wbi_core.Time(
                prop_nr="P813",  # Fetched today
                time=datetime.utcnow().replace(
                    tzinfo=timezone.utc
                ).replace(
                    hour=0,
                    minute=0,
                    second=0,
                ).strftime("+%Y-%m-%dT%H:%M:%SZ"),
                is_reference=True,
            ),
            wbi_core.Time(
                prop_nr="P577",  # Publication date
                time=publication_date.strftime("+%Y-%m-%dT00:00:00Z"),
                is_reference=True,
            ),
            type_of_reference_qualifier,
        ]
    if source == "europarl":
        stated_in = wbi_core.ItemID(
            prop_nr="P248",
            value="Q5412081",
            is_reference=True
        )
        reference = [
            stated_in,
            wbi_core.Time(
                prop_nr="P813",  # Fetched today
                time=datetime.utcnow().replace(
                    tzinfo=timezone.utc
                ).replace(
                    hour=0,
                    minute=0,
                    second=0,
                ).strftime("+%Y-%m-%dT%H:%M:%SZ"),
                is_reference=True,
            ),
            wbi_core.Time(
                prop_nr="P577",  # Publication date
                time="+2012-05-12T00:00:00Z",
                is_reference=True,
            ),
            wbi_core.Url(
                prop_nr="P854",  # reference url
                value="http://www.statmt.org/europarl/v7/sv-en.tgz",
                is_reference=True,
            ),
            # filename in archive
            wbi_core.String(
                (f"europarl-v7.{config.language_code}" +
                 f"-en.{config.language_code}"),
                "P7793",
                is_reference=True,
            ),
            # line number
            wbi_core.String(
                str(line),
                "P7421",
                is_reference=True,
            ),
            type_of_reference_qualifier,
        ]
    if source == "ksamsok":
        # No date is provided unfortunately, so we set it to unknown value
        stated_in = wbi_core.ItemID(
            prop_nr="P248",
            value="Q7654799",
            is_reference=True
        )
        document_id = wbi_core.ExternalID(
            # K-Samsök URI
            prop_nr="P1260",  
            value=document_id,
            is_reference=True
        )
        reference = [
            stated_in,
            document_id,
            wbi_core.Time(
                prop_nr="P813",  # Fetched today
                time=datetime.utcnow().replace(
                    tzinfo=timezone.utc
                ).replace(
                    hour=0,
                    minute=0,
                    second=0,
                ).strftime("+%Y-%m-%dT%H:%M:%SZ"),
                is_reference=True,
            ),
            wbi_core.Time(
                # We don't know the value of the publication dates unfortunately
                prop_nr="P577",  # Publication date
                time="",
                snak_type="somevalue",
                is_reference=True,
            ),
            type_of_reference_qualifier,
        ]
    if reference is None:
        logger.error("No reference defined, cannot add usage example")
        exit(1)
    # This is the usage example statement
    claim = wbi_core.MonolingualText(
        sentence,
        "P5831",
        language=config.language_code,
        # Add qualifiers
        qualifiers=[
            link_to_form,
            link_to_sense,
            language_style_qualifier,
        ],
        # Add reference
        references=[reference],
    )
    if config.debug_json:
        logging.debug(f"claim:{claim.get_json_representation()}")
    item = wbi_core.ItemEngine(
        data=[claim], append_value=["P5831"], item_id=lid,
    )
    # if config.debug_json:
    #     print(item.get_json_representation())
    if config.login_instance is None:
        # Authenticate with WikibaseIntegrator
        print("Logging in with Wikibase Integrator")
        config.login_instance = wbi_login.Login(
            user=config.username, pwd=config.password
        )
    result = item.write(
        config.login_instance,
        edit_summary="Added usage example with [[Wikidata:LexUse]]"
    )
    if config.debug_json:
        logging.debug(f"result from WBI:{result}")
    return result


def count_words(string):
    # from https://www.pythonpool.com/python-count-words-in-string/
    return(len(string.strip().split(" ")))


def prompt_choose_sense(senses):
    """Returns a dictionary with sense_id -> sense_id
    and gloss -> gloss or False"""
    # from https://stackoverflow.com/questions/23294658/
    # asking-the-user-for-input-until-they-give-a-valid-response
    while True:
        try:
            options = ("Please choose the correct sense corresponding " +
                       "to the meaning in the usage example")
            number = 1
            # Put each key -> value into a new nested dictionary
            for sense in senses:
                options += f"\n{number}) {senses[number]['gloss']}"
                if config.show_sense_urls:
                    options += f" ({wd_prefix + senses[number]['sense_id']} )"
                number += 1
            options += "\nPlease input a number or 0 to cancel: "
            choice = int(input(options))
        except ValueError:
            print("Sorry, I didn't understand that.")
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
                print("Cancelled adding this sentence.")
                return False


def add_to_watchlist(lid):
    # Get session from WBI, it cannot be None because this comes after adding
    # an
    # usage example with WBI.
    session = config.login_instance.get_session()
    # adapted from https://www.mediawiki.org/wiki/API:Watch
    url = "https://www.wikidata.org/w/api.php"
    params_token = {
        "action": "query",
        "meta": "tokens",
        "type": "watch",
        "format": "json"
    }

    result = session.get(url=url, params=params_token)
    data = result.json()

    csrf_token = data["query"]["tokens"]["watchtoken"]

    params_watch = {
        "action": "watch",
        "titles": "Lexeme:" + lid,
        "format": "json",
        "formatversion": "2",
        "token": csrf_token,
    }

    result = session.post(
        url, data=params_watch
    )
    if config.debug_json:
        print(result.text)
    print(f"Added {lid} to your watchlist")


def prompt_sense_approval(sentence=None, data=None):
    """Prompts for validating that we have a sense matching the use example
    return dictionary with sense_id and sense_gloss if approved else False"""
    # TODO split this up in multiple functions
    # ->prepare_sense_selection()
    # + prompt_single_sense()
    # + prompt_multiple_senses()
    lid = data["lid"]
    # This returns a tuple if one sense or a dictionary if multiple senses
    senses = fetch_senses(lid)
    number_of_senses = len(senses)
    logging.debug(f"number_of_senses:{number_of_senses}")
    if number_of_senses > 0:
        if number_of_senses == 1:
            gloss = senses[1]["gloss"]
            sense_id = senses[1]["sense_id"]
            if config.show_sense_urls:
                question = ("Found only one sense. " +
                            "Does this example fit the following " +
                            f"gloss? {wd_prefix + sense_id}\n'{gloss}'")
            else:
                question = ("Found only one sense. " +
                            "Does this example fit the following " +
                            f"gloss?\n'{gloss}'")
            if yes_no_question(question):
                return {
                    "sense_id": senses[1]["sense_id"],
                    "sense_gloss": gloss
                }
            else:
                word = data['word']
                print("Cancelled adding sentence as it does not match the " +
                      "only sense currently present. \nLexemes are " +
                      "entirely dependent on good quality QIDs. \n" +
                      "Please add labels " +
                      "and descriptions to relevant QIDs and then use " +
                      "MachtSinn to add " +
                      "more senses to lexemes by matching on QID concepts " +
                      "with similar labels and descriptions in the lexeme " +
                      "language." +
                      f"\nSearch for {word} in Wikidata: " +
                      "https://www.wikidata.org/w/index.php?" +
                      f"search={word}&title=Special%3ASearch&" +
                      "profile=advanced&fulltext=0&" +
                      "advancedSearch-current=%7B%7D&ns0=1")
                time.sleep(5)
                return False
        else:
            print(f"Found {number_of_senses} senses.")
            sense = False
            # TODO check that all senses has a gloss matching the language of
            # the example
            sense = prompt_choose_sense(senses)
            if sense:
                logging.debug("sense was accepted")
                return {
                    "sense_id": sense["sense_id"],
                    "sense_gloss": sense["gloss"]
                }
            else:
                return False
    else:
        # Check if any suitable senses exist
        count = (count_number_of_senses_with_P5137("L35455"))
        if count > 0:
            print("{language.title()} gloss is missing for {count} sense(s)" +
                  ". Please fix it manually here: " +
                  f"{wd_prefix + lid}")
            time.sleep(5)
            return False
        else:
            logging.debug("no senses this should never be reached " +
                          "if the sparql result was sane")
            return False


def get_sentences_from_apis(result: str) -> Dict:
    """Returns a dict with sentences as key and id as value"""
    data = extract_data(result)
    form_id = data["form_id"]
    word = data["word"]
    print(f"Trying to find examples for the {data['category']} lexeme " +
          f"form: {word} with id: {form_id}")
    if config.language_code == "sv":
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
    """Return True, False or None (skip)"""
    word_count = count_words(sentence)
    result = yes_no_skip_question(
            f"Found the following sentence with {word_count} " +
            "words. Is it suitable as a usage example " +
            f"for the {data['category']} form '{data['word']}'? \n" +
            f"'{sentence}'"
    )
    if result:
        selected_sense = prompt_sense_approval(
            sentence=sentence,
            data=data
        )
        if selected_sense is not False:
            lid = data["lid"]
            sense_id = selected_sense["sense_id"]
            sense_gloss = selected_sense["sense_gloss"]
            if (sense_id is not None and sense_gloss is not None):
                result = False
                result = add_usage_example(
                    document_id=document_id,
                    sentence=sentence,
                    lid=lid,
                    form_id=data["form_id"],
                    sense_id=sense_id,
                    word=data["word"],
                    publication_date=date,
                    language_style=language_style,
                    type_of_reference=type_of_reference,
                    source=source,
                    line=line,
                )
                if result:
                    print("Successfully added usage example " +
                          f"to {wd_prefix + lid}")
                    add_to_watchlist(lid)
                    save_to_exclude_list(data)
                    return True
                else:
                    return False
            else:
                return False
    elif result is None:
        # None means skip
        return None
    else:
        return False


def save_to_exclude_list(data: dict):
    # date, lid and lang
    if data is None:
        print("Error. Data was None")
        exit(1)
    form_id = data["form_id"]
    word = data["word"]
    print(f"Adding {word} to local exclude list '{config.exclude_list}'")
    if config.debug_exclude_list:
        logging.debug(f"data to exclude:{data}")
    form_data = dict(
        word=word,
        date=datetime.now().isoformat(),
        lang=config.language_code,
    )
    if config.debug_exclude_list:
        logging.debug(f"adding:{form_id}:{form_data}")
    if os.path.isfile('exclude_list.json'):
        # Read the file
        with open(config.exclude_list, 'r', encoding='utf-8') as myfile:
            json_data = myfile.read()
        if len(json_data) > 0:
            with open(config.exclude_list, 'w', encoding='utf-8') as myfile:
                # parse file
                exclude_list = json.loads(json_data)
                exclude_list[form_id] = form_data
                if config.debug_exclude_list:
                    logging.debug(f"dumping altered list:{exclude_list}")
                json.dump(exclude_list, myfile, ensure_ascii=False)
        else:
            print("Error. json data is null.")
            exit(1)
    else:
        # Create the file
        with open(config.exclude_list, "w", encoding='utf-8') as outfile:
            # Create new file with dict and item
            exclude_list = {}
            exclude_list[form_id] = form_data
            if config.debug_exclude_list:
                logging.debug(f"dumping:{exclude_list}")
            json.dump(exclude_list, outfile, ensure_ascii=False)


def process_result(result, data):
    # ask to continue
    # if yes_no_question(f"\nWork on {data['word']}?"):
    # This dict holds the sentence as key and
    # riksdagen_document_id or other id as value
    sentences_and_result_data = get_sentences_from_apis(result)
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
                print("Presenting sentence " +
                      f"{count}/{len(sorted_sentences)} from {date} from " +
                      f"{riksdagen.baseurl + document_id}")
            elif source == "europarl":
                print("Presenting sentence " +
                      f"{count}/{len(sorted_sentences)} " +
                      "from europarl")
            elif source == "ksamsok":
                print("Presenting sentence " +
                      f"{count}/{len(sorted_sentences)} " +
                      "from ksamsok")
            else:
                print("Presenting sentence " +
                      f"{count}/{len(sorted_sentences)} from {date}")
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
            # Break out of the for loop by returning early because one
            # example was already choosen for this result or if the form
            # was skipped. False means that we could not find a sentence, it
            # could be related to low number of records being fetched so we
            # don't excude it.
            if result is not False:
                # Add to temporary exclude_list
                logging.debug("adding to exclude list after presentation")
                save_to_exclude_list(data)
                # break
                return
    # else:
    #     print("Added to excludelist because of no " +
    #           "suitable sentences were found")
    #     save_to_exclude_list(data)


def in_exclude_list(data: dict):
    # Check if in exclude_list
    if os.path.isfile('exclude_list.json'):
        if config.debug_exclude_list:
            logging.debug("Looking up in exclude list")
        # Read the file
        with open('exclude_list.json', 'r', encoding='utf-8') as myfile:
            json_data = myfile.read()
            # parse file
            exclude_list = json.loads(json_data)
            lid = data["lid"]
            for form_id in exclude_list:
                form_data = exclude_list[form_id]
                if config.debug_exclude_list:
                    logging.debug(f"found:{form_data}")
                if (
                        # TODO check the date also
                        lid == form_id
                        and config.language_code == form_data["lang"]
                ):
                    logging.debug("Match found")
                    return True
        # Not found in exclude_list
        return False
    else:
        # No exclude_list
        return False


def process_lexeme_data(results):
    """Go through the SPARQL results randomly"""
    words = []
    for result in results:
        data = extract_data(result)
        words.append(data["word"])
    print(f"Got {len(words)} suitable forms from Wikidata")
    logging.debug(f"words:{words}")
    # Go through the results at random
    print("Going through the list of forms at random.")
    # from http://stackoverflow.com/questions/306400/ddg#306417
    earlier_choices = []
    while (True):
        if len(earlier_choices) == config.sparql_results_size:
            # We have gone checked all results now
            # TODO offer to fetch more
            print("No more results. Run the script again to continue")
            exit(0)
        else:
            result = random.choice(results)
            # Prevent running more than once for each result
            if result not in earlier_choices:
                earlier_choices.append(result)
                data = extract_data(result)
                word = data['word']
                logging.debug(f"random choice:{word}")
                if in_exclude_list(data):
                    # Skip if found in the exclude_list
                    logging.debug(
                        f"Skipping result {word} found in exclude_list",
                    )
                    continue
                else:
                    # not in exclude_list
                    logging.debug(f"processing:{word}")
                    process_result(result, data)


def introduction():
    if yes_no_question("This script enables you to " +
                       "semi-automatically add usage examples to " +
                       "lexemes with both good senses and forms " +
                       "(with P5137 and grammatical features respectively). " +
                       "\nPlease pay attention to the lexical " +
                       "category of the lexeme. \nAlso try " +
                       "adding only short and concise " +
                       "examples to avoid bloat and maximise " +
                       "usefullness. \nThis script adds edited " +
                       "lexemes (indefinitely) to your watchlist. " +
                       "\nContinue?"):
        return True
    else:
        return False
