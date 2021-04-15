#!/usr/bin/env python3
import gettext
import logging

import httpx
from sparqldataframe import wikidata_query
from typing import Dict, Union
from wikibaseintegrator import wbi_core

import config
from modules import loglevel
from modules import tui
from modules import util

# Constants
wd_prefix = "http://www.wikidata.org/entity/"

# Logging
logger = logging.getLogger(__name__)
if config.loglevel is None:
    # Set loglevel
    logger.debug("Setting loglevel in config")
    loglevel.set_loglevel()
logger.setLevel(config.loglevel)
logger.level = logger.getEffectiveLevel()
file_handler = logging.FileHandler("sparql.log")
logger.addHandler(file_handler)

# def count_number_of_senses_with_P5137(lid):
#     """Returns an int"""
#     result = (sparql_query(f'''
#     SELECT
#     (COUNT(?sense) as ?count)
#     WHERE {{
#       VALUES ?l {{wd:{lid}}}.
#       ?l ontolex:sense ?sense.
#       ?sense skos:definition ?gloss.
#       # Exclude lexemes without a linked QID from at least one sense
#       ?sense wdt:P5137 [].
#     }}'''))
#     count = int(result[0]["count"]["value"])
#     logging.debug(f"count:{count}")
#     return count


# def fetch_senses(lid: str) -> Dict:
#     """Returns dictionary with numbers as keys and a dictionary as value with
#     sense id and gloss"""
#     # Thanks to Lucas Werkmeister https://www.wikidata.org/wiki/Q57387675 for
#     # helping with this query.
#     tui.fetching_senses()
#     logging.info(f"...from {lid}")
#     result = (sparql_query(f'''
#     SELECT
#     ?sense ?gloss
#     WHERE {{
#       VALUES ?l {{wd:{lid}}}.
#       ?l ontolex:sense ?sense.
#       ?sense skos:definition ?gloss.
#       # Get only the swedish gloss, exclude otherwise
#       FILTER(LANG(?gloss) = "{config.language_code}")
#       # Exclude lexemes without a linked QID from at least one sense
#       ?sense wdt:P5137 [].
#     }}'''))
#     senses = {}
#     number = 1
#     if result is not None:
#         for row in result:
#             senses[number] = {
#                 "sense_id": row["sense"]["value"].replace(wd_prefix, ""),
#                 "gloss": row["gloss"]["value"]
#             }
#             number += 1
#         logging.debug(f"senses:{senses}")
#         # This returns a tuple if one sense or a dictionary if multiple senses
#         return senses
#     else:
#         logging.error(_("Error. Got None trying to fetch senses. "+
#                         "Please report this as an issue."))
#         exit(1)


def fetch_lexeme_data():
    df = wikidata_query(f'''
    SELECT DISTINCT
    ?entity_lid ?form ?word ?categoryLabel ?grammatical_featureLabel ?sense ?gloss
    WHERE {{
      ?entity_lid a ontolex:LexicalEntry; dct:language wd:{config.language_qid}.
      VALUES ?excluded {{
        # exclude affixes and interfix
        wd:Q62155 # affix
        wd:Q134830 # prefix
        wd:Q102047 # suffix
        wd:Q1153504 # interfix
      }}
      MINUS {{?entity_lid wdt:P31 ?excluded.}}
      ?entity_lid wikibase:lexicalCategory ?category.

      # We want only lexemes with both forms and at least one sense
      ?entity_lid ontolex:lexicalForm ?form.
      ?entity_lid ontolex:sense ?sense.

      # Exclude lexemes without a linked QID from at least one sense
      ?sense wdt:P5137 [].
      ?sense skos:definition ?gloss.
      # Get only the swedish gloss, exclude otherwise
      FILTER(LANG(?gloss) = "{config.language_code}")

      # This remove all lexemes with at least one example which is not
      # ideal
      MINUS {{?entity_lid wdt:P5831 ?example.}}
      ?form wikibase:grammaticalFeature ?grammatical_feature.
      # We extract the word of the form
      ?form ontolex:representation ?word.
      SERVICE wikibase:label
      {{ bd:serviceParam wikibase:language "{config.language_code},en". }}
    }}
    limit {config.sparql_results_size}
    offset {config.sparql_offset}
    ''')
    # https://note.nkmk.me/en/python-pandas-dataframe-rename/
    df.rename(
        columns={
            'grammatical_featureLabel': 'feature',
            'categoryLabel': 'category'
        },
        inplace=True
    )
    df["lid"] = df["entity_lid"].str.replace(util.wd_prefix,'')
    df["formid"] = df["form"].str.replace(util.wd_prefix,'')
    df["senseid"] = df["sense"].str.replace(util.wd_prefix,'')
    return df

# def sparql_query(query):
#     # from https://stackoverflow.com/questions/55961615/
#     # how-to-integrate-wikidata-query-in-python
#     url = 'https://query.wikidata.org/sparql'
#     r = httpx.get(url, params={'format': 'json', 'query': query})
#     data = r.json()
#     # pprint(data)
#     results = data["results"]["bindings"]
#     # pprint(results)
#     if len(results) == 0:
#         print(_( "No lexemes was returned from Wikidata for the choosen language"+
#                  " . This script only works on lexemes that has at least one sense"+
#                  " with item for this sense (P5137) and at least one form with " +
#                  "grammatical features."+
#                  "Try running the script again." ))
#     else:
#         return results

# def extract_wikibase_entity(result: Dict, field: str) -> str:
#     return result[field]["value"].replace(
#         wd_prefix, ""
#     )

# def extract_wikibase_value(result: Dict, field: str) -> str:
#     return result[field]["value"].replace(
#         wd_prefix, ""
#     )

# def extract_lexeme_forms_data(result):
#     """Extract SPARQL result"""
#     # For now only used by lexuse
#     lid = extract_wikibase_entity(result, "lid")
#     form_id = extract_wikibase_entity(result, "form")
#     word = extract_wikibase_value(result, "word")
#     word_spaces = " " + word + " "
#     word_angle_parens = ">" + word + "<"
#     category = extract_wikibase_value(result, "catLabel")
#     grammatical_feature = extract_wikibase_value(
#         result, "grammatical_featureLabel",
#     )
#     return dict(
#         lid=lid,
#         form_id=form_id,
#         word=word,
#         word_spaces=word_spaces,
#         word_angle_parens=word_angle_parens,
#         category=category
#     )

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
            print(_( "Error. Language style {} ".format(language_style) +
                     "not one of (formal,informal). Please report a bug at "+
                     "https://github.com/egils-consulting/LexUtils/issues" ))
            sleep(config.sleep_time)
            return "error"
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
            print(_( "Error. Type of reference {} ".format(type_of_reference) +
                     "not one of (written,oral). Please report a bug at "+
                     "https://github.com/egils-consulting/LexUtils/issues" ))
            sleep(config.sleep_time)
            return "error"
    logging.debug(_( "Generating qualifier type of reference " +
                  "with {}".format(medium) ))
    type_of_reference_qualifier = wbi_core.ItemID(
        prop_nr="P3865",
        value=medium,
        is_qualifier=True
    )
    if source == "riksdagen":
        if publication_date is not None:
            publication_date = datetime.fromisoformat(publication_date)
        else:
            print(_("Publication date of document {} ".format(document_id) +
                    "is missing. We have no fallback for that at the moment. " +
                    "Abort adding usage example."))
            return "error"
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
        logger.error(_( "No reference defined, cannot add usage example" ))
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
        edit_summary=(
            _( "Added usage example "+
               "with [[Wikidata:Tools/LexUtils]] v{}".format(config.version) )
        )
    )
    if config.debug_json:
        logging.debug(f"result from WBI:{result}")
    # TODO add handling of result from WBI and return True == Success or False 
    return result
