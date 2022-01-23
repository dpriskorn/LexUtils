import logging
from typing import List, Optional

from pandas import DataFrame

from lexutils.config import config
from lexutils.config.enums import SupportedPickles
from lexutils.models.historical_job_ads import HistoricalJobAd
from lexutils.models.usage_example import UsageExample
from lexutils.models.usage_examples import DataframeUsageExamples
from lexutils.models.wikidata.form import Form


class HistoricalJobAdsUsageExamples(DataframeUsageExamples):
    pickle = SupportedPickles.ARBETSFORMEDLINGEN_HISTORICAL_ADS

    def find_form_representation_in_the_dataframe(
            self,
            form: Form = None
    ) -> Optional[List[UsageExample]]:
        if self.dataframe is None:
            raise ValueError("dataframe was None")
        if form is None:
            raise ValueError("form was None")
        logger = logging.getLogger(__name__)
        result: DataFrame = self.dataframe[self.dataframe["text"].str.contains(form.representation)]
        number_of_matches = len(result)
        if number_of_matches > 0:
            logger.info(f"Found {number_of_matches} number of rows matching "
                        f"{form.representation} in the {self.pickle.name.title()}")
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
            logger.info(f"Found no rows matching {form.representation} in the {self.pickle.name.title()}")