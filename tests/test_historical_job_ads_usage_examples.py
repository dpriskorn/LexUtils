from typing import Optional
from unittest import TestCase

import pandas as pd  # type: ignore

from lexutils.models.historical_ads.historical_job_ads_usage_examples import (
    HistoricalJobAdsUsageExamples,
)
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.lexutils_form import LexutilsForm


class TestHistoricalJobAdsUsageExamples(TestCase):
    object: HistoricalJobAdsUsageExamples = HistoricalJobAdsUsageExamples(
        form=None, lexemes=None
    )
    object.dataframe = pd.DataFrame(data=[dict(id="testid", sentence="test")])
    example_form: Optional[LexutilsForm] = None

    def setUp(self) -> None:
        self.__setup_example_form__()

    def __setup_example_form__(self):
        form = LexutilsForm(form_id="L38817-F9")
        form.language_code = WikimediaLanguageCode.SWEDISH
        form.setup_lexeme()
        self.example_form = form

    def test_check_and_load(self):
        hjaue = HistoricalJobAdsUsageExamples(testing=True)
        hjaue.check_and_load()

    def test_find_form_representation_in_the_dataframe(self):
        self.object.find_form_representation_in_the_dataframe(form=self.example_form)
        # pprint(self.object.matches)
        if len(self.object.matches) == 0:
            self.fail()
