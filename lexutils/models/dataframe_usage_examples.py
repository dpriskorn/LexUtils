import logging
from abc import abstractmethod
from os.path import exists
from typing import List, Optional

import pandas as pd
from pandas import DataFrame

from lexutils.config.enums import SupportedPicklePaths
from lexutils.exceptions import DataNotFoundException
from lexutils.models.usage_example import UsageExample
from lexutils.models.usage_examples import UsageExamples
from lexutils.models.wikidata.form import Form


class DataframeUsageExamples(UsageExamples):
    dataframe: DataFrame = None
    matches: DataFrame = None
    number_of_matches: int = 0
    pickle_path: SupportedPicklePaths = None
    pickle_url: str = None
    usage_examples: List[UsageExample] = None

    def __init__(self):
        self.__check_if_the_pickle_exist__()
        self.__load_into_memory__()

    def __check_if_the_pickle_exist__(self):
        # logger = logging.getLogger(__name__)
        # test
        # pickle_filename = "test.pkl.gz"
        pickle_path = self.pickle_path.value
        if not exists(pickle_path):
            raise DataNotFoundException(f"Data from {self.pickle_path.name.title()} "
                                        f"was not found in {pickle_path}.")

    def __load_into_memory__(self):
        logger = logging.getLogger(__name__)
        logger.info(f"Loading the {self.pickle_path.name.title()} dataframe into memory")
        # return pd.read_pickle("test.pkl.gz")
        self.dataframe = pd.read_pickle(self.pickle_path.value)

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

    @abstractmethod
    def convert_matches_to_user_examples(
            self,
            form: Form = None
    ):
        pass
