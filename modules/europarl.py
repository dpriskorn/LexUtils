#!/usr/bin/env python3
import logging

import config
from modules import loglevel


# TODO move common code to common swedish module
logger = logging.getLogger(__name__)
if config.loglevel is None:
    # Set loglevel
    print("Setting loglevel in config")
    loglevel.set_loglevel()
logger.setLevel(config.loglevel)
logger.level = logger.getEffectiveLevel()
file_handler = logging.FileHandler("europarl.log")
logger.addHandler(file_handler)


def find_lines(word):
    """Returns a dictionary with line as
    key and linenumber as value"""
    records = {}
    print(f"Looking for {word} in the Europarl corpus...")
    with open(f'data_{config.language_code}.txt', 'r') as searchfile:
        number = 1
        for line in searchfile:
            if number % 50000 == 0:
                logger.info(number)
            if f" {word} " in line:
                logger.debug(f"matching line:{line}")
                records[line] = dict(
                    line=number,
                    document_id=None,
                    date=None,
                    source="europarl",
                    language_style="formal",
                    type_of_reference="written"
                )
            # if line.split(" ")[0] == word:
            #     print("Found in beginning of line")
            #     records[line] = number
            # if line.split(" ")[-1] == word:
            #     print("Found in end of line")
            #     records[line] = number
            number += 1
    logger.debug(f"records:{records}")
    print(f"Found {len(records)} sentences")
    return records


def get_records(data):
    word = data["word"]
    # The lines are already split in sentences in the corpus. so we just return
    # them as is
    return find_lines(word)

    # TODO check len of records
    # if records is not None:
    #     if config.debug:
    #         print("Looping through records from Europarl corpus")
    #     summaries = riksdagen.extract_summaries_from_records(
    #         records, data
    #     )
    #     unsorted_sentences = {}
    #     # Iterate through the dictionary
    #     for summary in summaries:
    #         # Get result_data
    #         result_data = summaries[summary]
    #         # Add information about the source (written,oral) and
    #         # (formal,informal)
    #         result_data["language_style"] = "formal"
    #         result_data["type_of_reference"] = "written"
    #         # document_id = result_data["document_id"]
    #         # if config.debug_summaries:
    #         #     print(f"Got back summary {summary} with the " +
    #         #           f"correct document_id: {document_id}?")
    #         suitable_sentences = find_usage_examples_from_summary(
    #             word_spaces=data["word_spaces"],
    #             summary=summary
    #         )
    #         if len(suitable_sentences) > 0:
    #             for sentence in suitable_sentences:
    #                 # Make sure the riksdagen_document_id follows
    #                 unsorted_sentences[sentence] = result_data
    #     return unsorted_sentences
