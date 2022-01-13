import logging
from typing import List, Optional

import pandas as pd
from pandas import DataFrame
import spacy as spacy
from spacy.lang.sv import Swedish

from lexutils.config import config
from lexutils.helpers import download_data
from lexutils.models.arbetsformedlingen import HistoricalJobAd
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.form import Form


def download_and_load_into_memory():
    download_data.fetch_arbetsformedlingen_historical_job_ads()
    print("Loading the Historical Ads dataframe into memory")
    return pd.read_pickle("historical_ads.pkl.gz")


def find_form_representation_in_the_dataframe(
        dataframe: DataFrame = None,
        form: Form = None
) -> Optional[List[UsageExample]]:
    if dataframe is None:
        raise ValueError("dataframe was None")
    if form is None:
        raise ValueError("form was None")
    logger = logging.getLogger(__name__)
    result: DataFrame = dataframe[dataframe["text"].str.contains(form.representation)]
    number_of_matches = len(result)
    if number_of_matches > 0:
        logger.info(f"Found {number_of_matches} number of rows matching "
                    f"{form.representation} in the Historical Ads")
        examples = []
        count = 1
        if config.historical_ads_max_results_size > number_of_matches:
            maximum_result_size_reached = False
        else:
            maximum_result_size_reached = True
        for row in result.itertuples(index=False):
            if count < config.historical_ads_max_results_size:
                if maximum_result_size_reached:
                    logger.info(f"Processing match {count}/{config.historical_ads_max_results_size} "
                                f"out of a total of {number_of_matches} matches")
                else:
                    logger.info(f"Processing match {count}/{number_of_matches} matches")
                record: HistoricalJobAd = row.object
                examples.extend(record.find_usage_examples_from_summary(form=form))
                count += 1
            else:
                break
        return examples
    else:
        logger.info(f"Found no rows matching {form.representation} in the Historical Ads")