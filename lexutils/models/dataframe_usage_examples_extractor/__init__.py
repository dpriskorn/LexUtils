import logging
from abc import abstractmethod
from os.path import exists
from typing import List, Optional

import pandas as pd  # type: ignore
from pandas import DataFrame  # type: ignore
from pydantic import BaseModel

from lexutils.enums import SupportedPicklePaths
from lexutils.exceptions import DataNotFoundException
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.lexutils_form import LexutilsForm

logger = logging.getLogger(__name__)


class DataframeUsageExamplesExtractor(BaseModel):
    """This is an abstract class that contains code
    to help extract from any dataframe"""

    dataframe: DataFrame = None
    matches: DataFrame = None
    number_of_matches: int = 0
    pickle_path: SupportedPicklePaths  # mandatory
    pickle_url: str = ""
    pickle_path_str: str = ""
    dataframe_loaded: bool = False
    testing: bool = False

    class Config:
        arbitrary_types_allowed = True
        extra = "forbid"

    @property
    def number_of_dataframe_rows(self):
        return len(self.dataframe)

    def __check_and_load__(self):
        self.__setup_pickle_path__()
        self.__check_if_the_pickle_exist__()
        self.__load_into_memory__()

    def __check_if_the_pickle_exist__(self):
        # logger = logging.getLogger(__name__)
        # test
        # pickle_filename = "test.pkl.gz"
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
        logger.info(f"Loaded dataframe with {len(self.dataframe)} rows into memory")
        self.dataframe_loaded = True

    def find_form_representation_in_the_dataframe(
        self, form: LexutilsForm = None
    ) -> Optional[List[UsageExample]]:
        logger.debug("find_form_representation_in_the_dataframe: running")
        if not self.dataframe_loaded:
            self.__check_and_load__()
        if self.dataframe is None or self.number_of_dataframe_rows == 0:
            raise ValueError("dataframe was None or empty")
        if form is None:
            raise ValueError("form was None")
        logger.info(f"Searching dataframe with {self.number_of_dataframe_rows} rows")
        target_column = "sentence"
        # First we create a boolean series to filter the dataframe with
        # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.str.contains.html
        boolean_series = self.dataframe[target_column].str.contains(
            f" {form.localized_representation} ", case=False
        )
        # This returns a dataframe with the matching rows using the boolean series as filter
        # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.loc.html
        self.matches = self.dataframe.loc[boolean_series]
        print(self.matches.info())
        self.number_of_matches = len(self.matches)
        logger.info(f"Found {self.number_of_matches} matches")
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

    @property
    def number_of_dataframe_rows(self):
        return len(self.dataframe)
