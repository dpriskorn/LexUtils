import logging
from os.path import exists

import pandas as pd

# This code is adapted from https://github.com/dpriskorn/WikidataMLSuggester
from lexutils.config.enums import SupportedFormPickles

logger = logging.getLogger(__name__)

# lookups where inspired by
# https://stackoverflow.com/questions/24761133/pandas-check-if-row-exists-with-certain-values

# This code stores the earlier choices the users made on forms
# We lookup based on form-ids like L1-F1
# We have 2 pickles:
# finished_forms.pkl
# declined_forms.pkl
# We define finish as: having 1 usage example added. This is good enough for now.


def read_from_pickle(
        pickle: SupportedFormPickles = None,
        form_id: str = None,
) -> bool:
    """Returns boolean"""
    if form_id is None or pickle is None:
        raise ValueError("did not get all we need")
    pickle_filename = pickle.value
    logger.debug(f"Reading from {pickle.name.title()}")
    if exists(pickle_filename):
        df = pd.read_pickle(pickle_filename)
        # This tests whether any row matches
        return (df['form_id'] == form_id).any()


def add_to_pickle(
        pickle: SupportedFormPickles = None,
        form_id: str = None
) -> None:
    if form_id is None or pickle is None:
        raise ValueError("did not get all we need")
    pickle_filename = pickle.value
    logger.debug(f"Adding to {pickle.name.title()}")
    data = dict(form_id=form_id)
    if exists(pickle_filename):
        df = pd.read_pickle(pickle_filename)
        # This tests whether any row matches
        match = (df['form_id'] == form_id).any()
        logger.debug(f"match:{match}")
        if not match:
            # We only give save the value once for now
            df = df.append(pd.DataFrame(data=[data]))
            logger.debug(f"Adding form id {form_id} to pickle {pickle.name.title()}")
            df.to_pickle(pickle_filename)
    else:
        pd.DataFrame(data=[data]).to_pickle(pickle_filename)
