#!/usr/bin/env python3
import gettext
import json
import logging
import os
from datetime import datetime

from lexutils import config # type: ignore

_ = gettext.gettext


def save_to_exclude_list(data: dict):
    """Only has side-effects.
    dict has the following keys:
    formid
    word
    """
    logger = logging.getLogger(__name__)
    # date, lid and lang
    if data is None:
        logger.error("Error. Data was None")
    else:
        formid = data["form_id"]
        word = data["word"]
        print(f"Adding {word} to local exclude list '{config.exclude_list}'")
        if config.debug_exclude_list:
            logging.debug(f"data to exclude:{data}")
        form_data = dict(
            word=word,
            date=datetime.now().isoformat(),
            lang=config.language_code,
        )
        if config.debug_exclude_list:
            logging.debug(f"adding:{form_id}:{form_data}")
        if os.path.isfile('exclude_list.json'):
            # Read the file
            with open(config.exclude_list, 'r', encoding='utf-8') as myfile:
                json_data = myfile.read()
            if len(json_data) > 0:
                with open(config.exclude_list, 'w', encoding='utf-8') as myfile:
                    # parse file
                    exclude_list = json.loads(json_data)
                    exclude_list[form_id] = form_data
                    if config.debug_exclude_list:
                        logging.debug(f"dumping altered list:{exclude_list}")
                    json.dump(exclude_list, myfile, ensure_ascii=False)
            else:
                logger.error(_("Error. JSON data had no entries. Remove the"+
                               " exclude_list.json and try again."))
        else:
            # Create the file
            with open(config.exclude_list, "w", encoding='utf-8') as outfile:
                # Create new file with dict and item
                exclude_list = {}
                exclude_list[form_id] = form_data
                if config.debug_exclude_list:
                    logging.debug(f"dumping:{exclude_list}")
                json.dump(exclude_list, outfile, ensure_ascii=False)
