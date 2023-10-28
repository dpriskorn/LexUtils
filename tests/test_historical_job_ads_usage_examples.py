from typing import Optional
from unittest import TestCase

import pandas as pd  # type: ignore

from lexutils.models.dataframe_usage_examples_extractor.historical_job_ads import (
    HistoricalJobAdsUsageExamplesExtractor,
)
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.lexutils_form import LexutilsForm


class TestHistoricalJobAdsUsageExamples(TestCase):
    example_form: Optional[LexutilsForm] = None

    def setUp(self) -> None:
        self.__setup_example_form__()

    def __setup_example_form__(self):
        form = LexutilsForm(form_id="L45469-F1")
        form.language_code = WikimediaLanguageCode.SWEDISH
        form.setup_lexeme()
        self.example_form = form

    def test_check_and_load(self):
        hjaue = HistoricalJobAdsUsageExamplesExtractor(testing=True)
        hjaue.__check_and_load__()

    def test_get_usage_examples(self):
        hjaue = HistoricalJobAdsUsageExamplesExtractor(testing=True)
        usage_examples = hjaue.get_usage_examples(form=self.example_form)
        assert len(hjaue.matches) > 5000
        print(hjaue.matches.info())
        assert len(usage_examples) == 59
        print(usage_examples[0])
