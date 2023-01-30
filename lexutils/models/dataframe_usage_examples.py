import logging
from abc import abstractmethod
from os.path import exists
from typing import List, Optional

import pandas as pd  # type: ignore
from pandas import DataFrame  # type: ignore

from lexutils.enums import SupportedPicklePaths
from lexutils.exceptions import DataNotFoundException
from lexutils.models.usage_example import UsageExample
from lexutils.models.usage_examples import UsageExamples
from lexutils.models.wikidata.lexutils_form import LexutilsForm

logger = logging.getLogger(__name__)


class DataframeUsageExamples(UsageExamples):
    """This is an abstract class"""

    dataframe: DataFrame = None
    matches: DataFrame = None
    number_of_matches: int = 0
    pickle_path: Optional[SupportedPicklePaths] = None
    pickle_url: str = ""
    usage_examples: List[UsageExample] = []
    pickle_path_str: str = ""

    class Config:
        arbitrary_types_allowed = True

    def check_and_load(self):
        self.__check_if_the_pickle_exist__()
        self.__load_into_memory__()

    def __check_if_the_pickle_exist__(self):
        # logger = logging.getLogger(__name__)
        # test
        # pickle_filename = "test.pkl.gz"
        self.__setup_pickle_path__()
        logger.debug(f"searching pickle path: {self.pickle_path_str}")
        if not exists(self.pickle_path_str):
            raise DataNotFoundException(
                f"Data from {self.pickle_path.name.title()} "
                f"was not found in {self.pickle_path_str}."
            )

    def __load_into_memory__(self):
        logger.info(
            f"Loading the {self.pickle_path.name.title()} dataframe into memory"
        )
        self.dataframe = pd.read_pickle(filepath_or_buffer=str(self.pickle_path_str))

    def find_form_representation_in_the_dataframe(
        self, form: LexutilsForm = None
    ) -> Optional[List[UsageExample]]:
        if self.dataframe is None:
            raise ValueError("dataframe was None")
        if form is None:
            raise ValueError("form was None")
        target_column = "sentence"
        self.matches = self.dataframe[
            self.dataframe[target_column].str.contains(form.localized_representation)
        ]
        self.number_of_matches = len(self.matches)
        return self.convert_matches_to_user_examples(form=form)

    @abstractmethod
    def convert_matches_to_user_examples(
        self, form: LexutilsForm = None
    ) -> List[UsageExample]:
        pass

    def __setup_pickle_path__(self):
        if self.testing:
            self.pickle_path_str = "../" + str(self.pickle_path.value)
        else:
            self.pickle_path_str = str(self.pickle_path.value)
