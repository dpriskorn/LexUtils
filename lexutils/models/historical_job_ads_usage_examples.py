import logging
from typing import List, Optional

from pandas import DataFrame

from lexutils.config import config
from lexutils.config.enums import SupportedPicklePaths
from lexutils.models.dataframe_usage_examples import DataframeUsageExamples
from lexutils.models.wikidata.form import Form


class HistoricalJobAdsUsageExamples(DataframeUsageExamples):
    pickle_path = SupportedPicklePaths.ARBETSFORMEDLINGEN_HISTORICAL_ADS

    def convert_matches_to_user_examples(
            self,
            form: Form = None
    ):
        logger = logging.getLogger(__name__)
        # maximum_result_size_reached = False
        if self.number_of_matches > 0:
            logger.info(f"Found {self.number_of_matches} number of rows matching "
                        f"{form.representation} in the {self.pickle_path.name.title()}")
            examples = []
            count = 1
            for row in self.matches.itertuples(index=False):
                logger.info(row)
                if count < config.riksdagen_max_results_size:
                    if self.number_of_matches > config.riksdagen_max_results_size:
                        logger.info(f"Processing match {count}/{config.historical_ads_max_results_size} "
                                    f"out of a total of {self.number_of_matches} matches")
                    else:
                        logger.info(f"Processing match {count}/{self.number_of_matches} matches")
                    from lexutils.models.historical_job_ads_record import HistoricalJobAd
                    record = HistoricalJobAd(id=row.id, text=row.sentence,
                                             filename=row.filename, date=row.date)
                    example = record.extract_usage_example_if_suitable(form=form)
                    if example is not None:
                        # logger.info("Looking up the QID for the document")
                        # example.record.lookup_qid()
                        examples.append(example)
                    count += 1
                else:
                    break
            logger.debug(f"returning {len(examples)} examples")
            return examples
        else:
            logger.info(f"Found no rows matching {form.representation} in the {self.pickle_path.name.title()}")
