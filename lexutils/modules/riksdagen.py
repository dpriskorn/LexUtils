#!/usr/bin/env python3
import asyncio
import gettext
import logging
# import re
from typing import List

import httpx

from lexutils.config import config
from lexutils.models.riksdagen import RiksdagenRecord
from lexutils.models.usage_example import UsageExample
from lexutils.helpers import tui
from lexutils.models.wikidata.form import Form
from lexutils.models.wikidata.misc import LexemeLanguage

_ = gettext.gettext

# Constants
api_name = _("Riksdagen API")
baseurl = "https://data.riksdagen.se/dokument/"


# Entry is in the bottom get_records(data)

def get_result_count(word):
    logger = logging.getLogger(__name__)
    # First find out the number of results
    url = (f"http://data.riksdagen.se/dokumentlista/?sok={word}" +
           "&sort=rel&sortorder=desc&utformat=json&a=s&p=1")
    r = httpx.get(url)
    data = r.json()
    results = int(data["dokumentlista"]["@traffar"])
    logging.info(f"results:{results}")
    return results


async def async_fetch(word):
    async def get(url, session):
        """Accepts a url and a httpx session
        This function is called for every task."""
        response = await session.get(url)
        return response

    logger = logging.getLogger(__name__)
    # Get total results count
    results = get_result_count(word)
    # Generate the urls
    if results > config.riksdagen_max_results_size:
        results = config.riksdagen_max_results_size
    # generate urls
    urls = []
    # divide by 20 to know how many requests to send
    for i in range(1, int(results / 20)):
        urls.append(f"http://data.riksdagen.se/dokumentlista/?sok={word}" +
                    f"&sort=rel&sortorder=desc&utformat=json&a=s&p={i}")
    logging.debug(f"urls:{urls}")
    # get urls asynchroniously
    # inspired by https://trio.readthedocs.io/en/stable/tutorial.html
    async with httpx.AsyncClient() as session:
        logger.info("Gathering tasks.")
        # inspired by https://stackoverflow.com/questions/56161595/
        # how-to-use-async-for-in-python
        results = await asyncio.gather(*[get(url, session) for url in urls])
        logger.info(f"All {len(results)} tasks done")
        return results


def process_async_responses(
        word: str = None,
        lexemelanguage: LexemeLanguage = None
) -> List[RiksdagenRecord]:
    logger = logging.getLogger(__name__)
    if lexemelanguage is None:
        raise ValueError("lexemelanguage was None")
    if word is None:
        raise ValueError("word was None")
    tui.downloading_from(api_name)
    results = asyncio.run(async_fetch(word))
    records = []
    for response in results:
        data = response.json()
        # check if dokument is in the list
        if "dokument" in data["dokumentlista"].keys():
            for entry in data["dokumentlista"]["dokument"]:
                records.append(RiksdagenRecord(
                    entry,
                    lexemelanguage=lexemelanguage
                ))
    length = len(records)
    logger.info(f"Got {length} records")
    # logger.debug(f"records:{records}")
    return records


def filter_matching_records(
        records,
                            form: Form = None
) -> List[RiksdagenRecord]:
    logger = logging.getLogger(__name__)
    if form is None:
        raise ValueError("form was None")
    # TODO look for more examples from riksdagen if none in the first set of
    # For now we only support exact hits
    # count_inexact_hits = 1
    count = 1
    records_with_exact_match = []
    for record in records:
        if config.debug_summaries:
            logging.info(f"Working of record number {count}")
        record.find_form_representation_in_the_text(form.representation)
        if record.exact_hit:
            records_with_exact_match.append(record)
            if config.debug_summaries:
                logger.info(
                    f"Found exact hit in https://data.riksdagen.se/dokument/{record.id}"
                )
        count += 1
    logger.info(f"Found {len(records_with_exact_match)} records with exact matches for {form.representation}")
    return records_with_exact_match


def get_records(
        form: Form = None,
        lexemelanguage: LexemeLanguage = None
) -> List[UsageExample]:
    # logger = logging.getLogger(__name__)
    if form is None:
        raise ValueError("form was None")
    if lexemelanguage is None:
        raise ValueError("lexemelanguage was None")
    records: List[RiksdagenRecord] = process_async_responses(form.representation,
                                                             lexemelanguage=lexemelanguage)
    return process_records(records, form)


def process_records(records: List[RiksdagenRecord], form: Form):
    logger = logging.getLogger(__name__)
    if records is not None:
        logger.debug("Looping through records from Riksdagen")
        records = filter_matching_records(records, form)
        usage_examples = []
        for record in records:
            # find usage examples and add to our list
            usage_examples.extend(record.find_usage_examples_from_summary(form))
        logger.info(f"Found {len(usage_examples)} suitable usage examples")
        return usage_examples
