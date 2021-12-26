# #!/usr/bin/env python3
# import gettext
# import logging
# from datetime import datetime, timezone
# from time import sleep
#
# import config
# from modules import util
# from sparqldataframe import wikidata_query
# from wikibaseintegrator import wbi_core, wbi_login, wbi_datatype
#
# _ = gettext.gettext
#
# # Constants
# wd_prefix = "http://www.wikidata.org/entity/"
#
# # TODO Move all of this code into methods of classes
#
#
#
import logging
from typing import List
from wikibaseintegrator.wbi_helpers import execute_sparql_query

from lexutils import config
from lexutils.config.config import language_code, wd_prefix
from lexutils.models.wikidata import Sense, Form
from lexutils.modules import tui


def fetch_senses(form: Form = None) -> List[Sense]:
    """Returns dictionary with numbers as keys and a dictionary as value with
    sense id and gloss"""
    logger = logging.getLogger(__name__)
    if form is None:
        raise ValueError("form was None")
    # Thanks to Lucas Werkmeister https://www.wikidata.org/wiki/Q57387675 for
    # helping with this query.
    tui.fetching_senses()
    logging.info(f"...from {form.lexeme_id}")
    result = (execute_sparql_query(f'''
    SELECT
    ?sense ?gloss
    WHERE {{
      VALUES ?l {{wd:{form.lexeme_id}}}.
      ?l ontolex:sense ?sense.
      ?sense skos:definition ?gloss.
      # Get only the swedish gloss, exclude otherwise
      FILTER(LANG(?gloss) = "{language_code}")
      # Exclude lexemes without a linked QID from at least one sense
      ?sense wdt:P5137 [].
    }}'''))
    senses = []
    number = 1
    # TODO Move this into the model
    if result is not None:
        print(f"result:{result}")
        rows = result["results"]["bindings"]
        number_of_rows = len(rows)
        if number_of_rows > 0:
            for row in rows:
                print(f"row:{row}")
                senses.append(
                    Sense(
                        id=row["sense"]["value"],
                        gloss=row["gloss"]["value"]
                ))
                number += 1
            logging.debug(f"senses:{senses}")
            return senses
        else:
            raise ValueError("number of senses was 0")
    else:
        raise ValueError(_("Error. Got None trying to fetch senses. "+
                        "Please report this as an issue."))
#
#
#
# # def sparql_query(query):
# #     # from https://stackoverflow.com/questions/55961615/
# #     # how-to-integrate-wikidata-query-in-python
# #     url = 'https://query.wikidata.org/sparql'
# #     r = httpx.get(url, params={'format': 'json', 'query': query})
# #     data = r.json()
# #     # pprint(data)
# #     results = data["results"]["bindings"]
# #     # pprint(results)
# #     if len(results) == 0:
# #         print(_( "No lexemes was returned from Wikidata for the choosen language"+
# #                  " . This script only works on lexemes that has at least one sense"+
# #                  " with item for this sense (P5137) and at least one form with " +
# #                  "grammatical features."+
# #                  "Try running the script again." ))
# #     else:
# #         return results
#
#
# # def extract_lexeme_forms_data(result):
# #     """Extract SPARQL result"""
# #     # For now only used by lexuse
# #     lid = extract_wikibase_entity(result, "lid")
# #     form_id = extract_wikibase_entity(result, "form")
# #     word = extract_wikibase_value(result, "word")
# #     word_spaces = " " + word + " "
# #     word_angle_parens = ">" + word + "<"
# #     category = extract_wikibase_value(result, "catLabel")
# #     grammatical_feature = extract_wikibase_value(
# #         result, "grammatical_featureLabel",
# #     )
# #     return dict(
# #         lid=lid,
# #         form_id=form_id,
# #         word=word,
# #         word_spaces=word_spaces,
# #         word_angle_parens=word_angle_parens,
# #         category=category
# #     )
#
