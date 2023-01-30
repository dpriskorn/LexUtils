from typing import Optional
from unittest import TestCase

import pandas as pd  # type: ignore

from lexutils.models.historical_ads.historical_job_ads_usage_examples import (
    HistoricalJobAdsUsageExamples,
)
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.lexutils_form import LexutilsForm


class TestHistoricalJobAdsUsageExamples(TestCase):
    # object: HistoricalJobAdsUsageExamples = HistoricalJobAdsUsageExamples(
    #     form=None, lexemes=None, testing=True
    # )
    # object.dataframe = pd.DataFrame(data=[dict(id="testid", sentence="test")])
    example_form: Optional[LexutilsForm] = None

    def setUp(self) -> None:
        self.__setup_example_form__()

    def __setup_example_form__(self):
        form = LexutilsForm(form_id="L45469-F1")
        form.language_code = WikimediaLanguageCode.SWEDISH
        form.setup_lexeme()
        self.example_form = form

    def test_check_and_load(self):
        hjaue = HistoricalJobAdsUsageExamples(testing=True)
        hjaue.__check_and_load__()

    def test_find_form_representation_in_the_dataframe(self):
        hjaue = HistoricalJobAdsUsageExamples(testing=True)
        usage_examples = hjaue.find_form_representation_in_the_dataframe(
            form=self.example_form
        )
        assert len(hjaue.matches) > 5000
        print(hjaue.matches.info())
        assert len(usage_examples) == 59
        print(usage_examples[0])
