import logging
import os
import sys
from typing import List
from abc import ABC, abstractmethod

import pandas as pd
import requests
from pandas import DataFrame

from lexutils.config.enums import SupportedPickles
from lexutils.models.usage_example import UsageExample
from lexutils.models.usage_examples import UsageExamples
from lexutils.models.wikidata.form import Form


class DataframeUsageExamples(UsageExamples, ABC):
    dataframe: DataFrame = None
    matches: DataFrame = None
    number_of_matches: int = 0
    pickle: SupportedPickles = None
    pickle_url: str = None
    usage_examples: List[UsageExample] = None

    def __init__(self):
        self.__download_the_pickle__()
        self.__load_into_memory__()

    def __download_the_pickle__(self):
        # logger = logging.getLogger(__name__)
        # test
        # pickle_filename = "test.pkl.gz"
        pickle_filename = self.pickle.value
        if os.path.isfile(pickle_filename):
            logging.info(f"Data from {self.pickle.name.title()} has "
                         "already been downloaded and converted.")
        else:
            print("Downloading ~8 MB data from Riksdagen")
            with open(pickle_filename, 'wb') as output_file:
                response = requests.get(self.pickle_url, stream=True)
                total_length = response.headers.get('content-length')
                if total_length is None:
                    # no content length header
                    output_file.write(response.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        output_file.write(data)
                        done = int(50 * dl / total_length)
                        sys.stdout.write(
                            "\r[%s%s]" % ('=' * done, ' ' * (50 - done))
                        )
                        sys.stdout.flush()
                    print('\nDownload Completed!!!')

    def __load_into_memory__(self):
        logger = logging.getLogger(__name__)
        logger.info(f"Loading the {self.pickle.name.title()} dataframe into memory")
        # return pd.read_pickle("test.pkl.gz")
        self.dataframe = pd.read_pickle(self.pickle.value)

    @abstractmethod
    def find_form_representation_in_the_dataframe(
            self,
            form: Form = None
    ) -> None:
        pass
