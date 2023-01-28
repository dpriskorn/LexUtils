from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from wikibaseintegrator.wbi_helpers import execute_sparql_query

from lexutils.config import config
from lexutils.config.enums import SupportedExampleSources, LanguageStyle, ReferenceType, BaseURLs
from lexutils.helpers.wdqs import extract_the_first_wikibase_value_from_a_wdqs_result_set
from lexutils.models.record import Record
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.enums import WikimediaLanguageCode

if TYPE_CHECKING:
    from lexutils.models.wikidata.form import Form


class RiksdagenRecord(Record):
    """This models a record in the Riksdagen dataset"""
    api_name = "Riksdagen API"
    base_url = BaseURLs.RIKSDAGEN.value
    # Because of language detection during the pre-processing
    # we know all sentences are Swedish
    language_code = WikimediaLanguageCode.SWEDISH
    language_style = LanguageStyle.FORMAL
    type_of_reference = ReferenceType.WRITTEN
    source = SupportedExampleSources.RIKSDAGEN

    def lookup_qid(self):
        # Given a docuemnt id lookup the QID if any
        result = execute_sparql_query(
            f"""
                SELECT ?item
                WHERE 
                {{
                  ?item wdt:P8433 "{self.id}".
                }}
                """
        )
        logging.info(f"result:{result}")
        self.document_qid = extract_the_first_wikibase_value_from_a_wdqs_result_set(result, "item")
        logging.info(f"document_qid:{self.document_qid}")

