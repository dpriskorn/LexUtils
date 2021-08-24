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
# # def fetch_senses(lid: str) -> Dict:
# #     """Returns dictionary with numbers as keys and a dictionary as value with
# #     sense id and gloss"""
# #     # Thanks to Lucas Werkmeister https://www.wikidata.org/wiki/Q57387675 for
# #     # helping with this query.
# #     tui.fetching_senses()
# #     logging.info(f"...from {lid}")
# #     result = (sparql_query(f'''
# #     SELECT
# #     ?sense ?gloss
# #     WHERE {{
# #       VALUES ?l {{wd:{lid}}}.
# #       ?l ontolex:sense ?sense.
# #       ?sense skos:definition ?gloss.
# #       # Get only the swedish gloss, exclude otherwise
# #       FILTER(LANG(?gloss) = "{config.language_code}")
# #       # Exclude lexemes without a linked QID from at least one sense
# #       ?sense wdt:P5137 [].
# #     }}'''))
# #     senses = {}
# #     number = 1
# #     if result is not None:
# #         for row in result:
# #             senses[number] = {
# #                 "sense_id": row["sense"]["value"].replace(wd_prefix, ""),
# #                 "gloss": row["gloss"]["value"]
# #             }
# #             number += 1
# #         logging.debug(f"senses:{senses}")
# #         # This returns a tuple if one sense or a dictionary if multiple senses
# #         return senses
# #     else:
# #         logging.error(_("Error. Got None trying to fetch senses. "+
# #                         "Please report this as an issue."))
# #         exit(1)
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
