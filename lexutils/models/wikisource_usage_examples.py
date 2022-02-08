import logging
from typing import List

from wikibaseintegrator.wbi_helpers import execute_sparql_query

from lexutils.config import config
from lexutils.models.api_usage_examples import APIUsageExamples
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikisource_record import WikisourceRecord


class WikisourceUsageExamples(APIUsageExamples):
    """This is a helper class to hold all records and usage example

    When instantiated it fetches and processes records into usage examples
    and stores them in an attribute."""

    def get_records(self) -> None:
        logger = logging.getLogger(__name__)
        if self.lexemes.language_code in config.fast_nlp_languages:
            limit = config.wikisource_max_results_size_fast_nlp
        else:
            limit = config.wikisource_max_results_size_slow_nlp
        logger.info(
            f"Fetching usage examples from the {self.lexemes.language_code.name.title()} Wikisource...")
        # search using sparql
        # borrowed from Scholia
        # thanks to Vigneron for the tip :)
        results = execute_sparql_query(f'''
            SELECT ?title ?titleUrl ?snippet WHERE {{
            SERVICE wikibase:mwapi {{
              bd:serviceParam wikibase:api "Search" .
              bd:serviceParam wikibase:endpoint "{self.lexemes.language_code.value}.wikisource.org" .
              bd:serviceParam mwapi:srsearch "{self.form.representation}" .
              bd:serviceParam mwapi:language "{self.lexemes.language_code.value}" .
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
        self.records = []
        for item in results["results"]["bindings"]:
            self.records.append(WikisourceRecord(json=item,
                                                 lexemes=self.lexemes))
        length = len(self.records)
        logger.info(f"Got {length} records")
        if logger.getEffectiveLevel() == 10:
            for record in self.records:
                logging.debug(record)

    def process_records_into_usage_examples(
            self
    ) -> List[UsageExample]:
        logger = logging.getLogger(__name__)
        if self.records is not None:
            logging.info("Looping through records from Wikisource")
            # records = filter_matching_records(records, form)
            usage_examples = []
            for record in self.records:
                # find usage examples and add to our list
                usage_examples.extend(record.find_usage_examples_from_summary(form=self.form))
            logger.info(f"Found {len(usage_examples)} suitable usage examples from Wikisource")
            return usage_examples
