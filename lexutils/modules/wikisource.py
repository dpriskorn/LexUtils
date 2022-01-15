from __future__ import annotations
import logging
from typing import List, TYPE_CHECKING

from wikibaseintegrator.wbi_helpers import execute_sparql_query

from lexutils.config import config
from lexutils.helpers.console import console
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.form import Form
from lexutils.models.wikisource import WikisourceRecord

if TYPE_CHECKING:
    from lexutils.models.lexemes import Lexemes


def get_records(
        form: Form = None,
        lexemes: Lexemes = None
) -> List[UsageExample]:
    logger = logging.getLogger(__name__)
    if form is None:
        raise ValueError("form was None")
    if lexemes is None:
        raise ValueError("language was None")
    if lexemes.language_code in config.fast_nlp_languages:
        limit = config.wikisource_max_results_size_fast_nlp
    else:
        limit = config.wikisource_max_results_size_slow_nlp
    logger.info(
        f"Fetching usage examples from the {lexemes.language_code.name.title()} Wikisource...")
    # search using sparql
    # borrowed from Scholia
    # thanks to Vigneron for the tip :)
    results = execute_sparql_query(f'''
 SELECT ?title ?titleUrl ?snippet WHERE {{
  SERVICE wikibase:mwapi {{
      bd:serviceParam wikibase:api "Search" .
      bd:serviceParam wikibase:endpoint "{lexemes.language_code.value}.wikisource.org" .
      bd:serviceParam mwapi:srsearch "{form.representation}" .
      bd:serviceParam mwapi:language "{lexemes.language_code.value}" .
      ?title wikibase:apiOutput mwapi:title .
      ?snippet_ wikibase:apiOutput "@snippet" .
  }}
  hint:Prior hint:runFirst "true" .
  BIND(CONCAT("https://br.wikisource.org/wiki/", ENCODE_FOR_URI(?title)) AS ?titleUrl)
  BIND(REPLACE(REPLACE(?snippet_, '</span>', ''), '<span class="searchmatch">', '') AS ?snippet)
}}
LIMIT {limit}
''')
    logger.debug(f"results:{results}")
    records = []
    for item in results["results"]["bindings"]:
        records.append(WikisourceRecord(json=item,
                                        lexemes=lexemes))
    length = len(records)
    logger.info(f"Got {length} records")
    if logger.getEffectiveLevel() == 10:
        for record in records:
            logging.debug(record)
    return process_records(form=form,
                           records=records,
                           lexemes=lexemes)


def process_records(
        form: Form = None,
        records: List[WikisourceRecord] = None,
lexemes: Lexemes = None
) -> List[UsageExample]:
    logger = logging.getLogger(__name__)
    if records is not None:
        logging.info("Looping through records from Wikisource")
        # records = filter_matching_records(records, form)
        usage_examples = []
        for record in records:
            # find usage examples and add to our list
            usage_examples.extend(record.find_usage_examples_from_summary(form=form))
        logger.info(f"Found {len(usage_examples)} suitable usage examples")
        return usage_examples
