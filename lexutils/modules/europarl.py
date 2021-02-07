#!/usr/bin/env python3
import gettext
import logging

import config
from modules import loglevel
from modules import tui

_ = gettext.gettext

# TODO move common code to common swedish module
logger = logging.getLogger(__name__)
if config.loglevel is None:
    # Set loglevel
    # print("Setting loglevel in config")
    loglevel.set_loglevel()
logger.setLevel(config.loglevel)
logger.level = logger.getEffectiveLevel()
file_handler = logging.FileHandler("europarl.log")
logger.addHandler(file_handler)

# Constants
api_name = _("Europarl corpus")

def find_lines(word):
    """Returns a dictionary with line as
    key and linenumber as value"""
    records = {}
    tui.downloading_from(api_name)
    with open(f'data_{config.language_code}.txt', 'r') as searchfile:
        number = 1
        for line in searchfile:
            # if number % 50000 == 0:
            #     logger.info(number)
            if line.find(" {word} ") != -1:
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
    if config.debug_sentences:
        logger.debug(f"records:{records}")
    logger.info(f"Found {len(records)} lines containing '{word}'.")
    return records


def get_records(data):
    word = data["word"]
    # The lines are already split in sentences in the corpus. so we just return
    # them as is
    return find_lines(word)

    # TODO check len of records
