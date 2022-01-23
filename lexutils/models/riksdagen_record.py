from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from wikibaseintegrator.wbi_helpers import execute_sparql_query

from lexutils.config.enums import SupportedExampleSources, LanguageStyle, ReferenceType
from lexutils.helpers.wdqs import extract_the_first_wikibase_value_from_a_wdqs_result_set
from lexutils.models.record import Record
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.enums import WikimediaLanguageCode

if TYPE_CHECKING:
    from lexutils.models.wikidata.form import Form


class RiksdagenRecord(Record):
    """This models a record in the Riksdagen dataset"""
    api_name = "Riksdagen API"
    base_url = "https://data.riksdagen.se/dokument/"
    language_style = LanguageStyle.FORMAL
    type_of_reference = ReferenceType.WRITTEN
    source = SupportedExampleSources.RIKSDAGEN
    language_code = WikimediaLanguageCode.SWEDISH
    swedish_text: bool = False

    def extract_usage_example_if_suitable(
            self,
            form: Form = None,
    ) -> Optional[UsageExample]:
        # check if the form appears by first cleaning
        # away all chars and then split the text into words
        if form is None:
            raise ValueError("form was None")
        logger = logging.getLogger(__name__)
        # This is a very crude test for relevancy, we lower first to improve matching
        logger.debug(f"Sentence before cleaning: {self.text}")
        cleaned_sentence = self.text.lower()
        punctations = [".", ",", "!", "?", "„", "“", "\n"]
        for punctation in punctations:
            if punctation in cleaned_sentence:
                cleaned_sentence = cleaned_sentence.replace(punctation, " ")
        logger.debug(f"cleaned sentence: {cleaned_sentence}")
        if form.representation.lower() in cleaned_sentence.split():
            logger.info(f"The form '{form.representation}' was found in the cleaned sentence. :)")
            # TODO check length
            return UsageExample(text=self.text,
                                record=self)

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

# Entry is in the bottom get_records(data)

# def get_result_count(word):
#     logger = logging.getLogger(__name__)
#     # First find out the number of results
#     url = (f"http://data.riksdagen.se/dokumentlista/?sok={word}" +
#            "&sort=rel&sortorder=desc&utformat=json&a=s&p=1")
#     try:
#         r = httpx.get(url)
#         data = r.json()
#         results = int(data["dokumentlista"]["@traffar"])
#         logging.info(f"results:{results}")
#         return results
#     except ConnectTimeout:
#         logger.warning("Got timeout when trying to fetch the count of hits from the Riksdagen API")
#
#
# async def async_fetch(word):
#     async def get(url, session):
#         """Accepts a url and a httpx session
#         This function is called for every task."""
#         try:
#             response = await session.get(url)
#             return response
#         except ReadTimeout:
#             logger.warning("Got read timeout from the Riksdagen API")
#
#     logger = logging.getLogger(__name__)
#     # Get total results count
#     results: Optional[int] = get_result_count(word)
#     if results is not None:
#         # Generate the urls
#         if results > config.riksdagen_max_results_size:
#             results = config.riksdagen_max_results_size
#         # generate urls
#         urls = []
#         # divide by 20 to know how many requests to send
#         for i in range(1, int(results / 20)):
#             urls.append(f"http://data.riksdagen.se/dokumentlista/?sok={word}" +
#                         f"&sort=rel&sortorder=desc&utformat=json&a=s&p={i}")
#         logging.debug(f"urls:{urls}")
#         # get urls asynchroniously
#         # inspired by https://trio.readthedocs.io/en/stable/tutorial.html
#         async with httpx.AsyncClient() as session:
#             logger.info("Gathering tasks.")
#             # inspired by https://stackoverflow.com/questions/56161595/
#             # how-to-use-async-for-in-python
#             results = await asyncio.gather(*[get(url, session) for url in urls])
#             logger.info(f"All {len(results)} tasks done")
#             return results
#
#
# def process_async_responses(
#         word: str = None,
#         lexemes: Lexemes = None
# ) -> List[RiksdagenRecord]:
#     logger = logging.getLogger(__name__)
#     if lexemes is None:
#         raise ValueError("lexemes was None")
#     if word is None:
#         raise ValueError("word was None")
#     tui.downloading_from(api_name)
#     results = asyncio.run(async_fetch(word))
#     records = []
#     from lexutils.models.riksdagen import RiksdagenRecord
#     for response in results:
#         if response is not None:
#             data = response.json()
#             # check if dokument is in the list
#             if "dokument" in data["dokumentlista"].keys():
#                 for entry in data["dokumentlista"]["dokument"]:
#                     record = RiksdagenRecord(
#                             entry,
#                             lexemes=lexemes
#                         )
#                     if record.swedish_text:
#                         records.append(record)
#     length = len(records)
#     logger.info(f"Got {length} records in Swedish")
#     # logger.debug(f"records:{records}")
#     return records
#
#
# def filter_matching_records(
#         records,
#         form: Form = None
# ) -> List[RiksdagenRecord]:
#     logger = logging.getLogger(__name__)
#     if form is None:
#         raise ValueError("form was None")
#     # TODO look for more examples from riksdagen if none in the first set of
#     # For now we only support exact hits
#     # count_inexact_hits = 1
#     count = 1
#     records_with_exact_match = []
#     for record in records:
#         if config.debug_summaries:
#             logging.info(f"Working of record number {count}")
#         record.find_form_representation_in_the_text(form.representation)
#         if record.exact_hit:
#             records_with_exact_match.append(record)
#             if config.debug_summaries:
#                 logger.info(
#                     f"Found exact hit in https://data.riksdagen.se/dokument/{record.id}"
#                 )
#         count += 1
#     logger.info(f"Found {len(records_with_exact_match)} records with exact matches for {form.representation}")
#     return records_with_exact_match
#
#
# def get_records(
#         form: Form = None,
#         lexemes: Lexemes = None
# ) -> List[UsageExample]:
#     # logger = logging.getLogger(__name__)
#     if form is None:
#         raise ValueError("form was None")
#     if lexemes is None:
#         raise ValueError("lexemes was None")
#     records: List[RiksdagenRecord] = process_async_responses(form.representation,
#                                                              lexemes=lexemes)
#     return process_records(records, form)
#
#
# def process_records(records: List[RiksdagenRecord], form: Form):
#     logger = logging.getLogger(__name__)
#     if records is not None:
#         logger.debug("Looping through records from Riksdagen")
#         records = filter_matching_records(records, form)
#         usage_examples = []
#         for record in records:
#             # find usage examples and add to our list
#             usage_examples.extend(record.find_usage_examples_from_summary(form))
#         logger.info(f"Found {len(usage_examples)} suitable usage examples")
#         return usage_examples