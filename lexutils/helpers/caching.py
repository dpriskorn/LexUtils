import logging
from os.path import exists
from typing import Optional

import pandas as pd

# This code is adapted from https://github.com/dpriskorn/WikidataMLSuggester

logger = logging.getLogger(__name__)

# lookups where inspired by
# https://stackoverflow.com/questions/24761133/pandas-check-if-row-exists-with-certain-values


def read_from_cache(
        qid: str = None,
) -> Optional[str]:
    """Returns None or result from the cache"""
    if qid is None:
        raise ValueError("did not get all we need")
    logger.debug("Reading from the cache")
    if exists("cache.pkl"):
        df = pd.read_pickle("cache.pkl")
        # This tests whether any row matches
        match = (df['form_id'] == qid).any()
        logger.debug(f"match:{match}")
        if match:
            # Here we find the row that matches and extract the
            # result column and extract the value using any()
            result = df.loc[df["form_id"] == qid, "label"][0]
            logger.debug(f"result:{result}")
            if result is not None:
                return result


def add_to_cache(
        label: str = None,
        qid: str = None
) -> None:
    if label is None or qid is None:
        raise ValueError("did not get all we need")
    logger.debug("Adding to cache")
    data = dict(qid=qid, label=label)
    if exists("cache.pkl"):
        df = pd.read_pickle("cache.pkl")
        # This tests whether any row matches
        match = (df['form_id'] == qid).any()
        logger.debug(f"match:{match}")
        if not match:
            # We only give save the value once for now
            df = df.append(pd.DataFrame(data=[data]))
            logger.debug(f"Saving pickle with new label {label}")
            df.to_pickle("cache.pkl")
    else:
        pd.DataFrame(data=[data]).to_pickle("cache.pkl")
