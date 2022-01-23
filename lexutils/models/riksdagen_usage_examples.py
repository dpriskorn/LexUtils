import logging
from typing import List, Optional

from lexutils.config import config
from lexutils.config.enums import SupportedPickles
from lexutils.models.dataframe_usage_examples import DataframeUsageExamples
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.form import Form


class RiksdagenUsageExamples(DataframeUsageExamples):
    pickle = SupportedPickles.RIKSDAGEN

    def find_form_representation_in_the_dataframe(
            self,
            form: Form = None
    ) -> Optional[List[UsageExample]]:
        if self.dataframe is None:
            raise ValueError("dataframe was None")
        if form is None:
            raise ValueError("form was None")
        # logger = logging.getLogger(__name__)
        target_column = "sentence"
        self.matches = self.dataframe[self.dataframe[target_column].str.contains(form.representation)]
        self.number_of_matches = len(self.matches)
        return self.convert_matches_to_user_examples(form=form)

    def convert_matches_to_user_examples(
            self,
            form: Form = None
    ):
        logger = logging.getLogger(__name__)
        # maximum_result_size_reached = False
        if self.number_of_matches > 0:
            logger.info(f"Found {self.number_of_matches} number of rows matching "
                        f"{form.representation} in the {self.pickle.name.title()}")
            examples = []
            count = 1
            for row in self.matches.itertuples(index=False):
                logger.info(row)
                if count < config.riksdagen_max_results_size:
                    if self.number_of_matches > config.riksdagen_max_results_size:
                        logger.info(f"Processing match {count}/{config.riksdagen_max_results_size} "
                                    f"out of a total of {self.number_of_matches} matches")
                    else:
                        logger.info(f"Processing match {count}/{self.number_of_matches} matches")
                    from lexutils.models.riksdagen_record import RiksdagenRecord
                    record = RiksdagenRecord(id=row.id, text=row.sentence)
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
            logger.info(f"Found no rows matching {form.representation} in the {self.pickle.name.title()}")
