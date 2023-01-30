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

    def test_check_and_load(self):
        hjaue = HistoricalJobAdsUsageExamples()
        hjaue.check_and_load()

    def test_find_form_representation_in_the_dataframe(self):
        form = LexutilsForm()
        form.language_code = WikimediaLanguageCode.SWEDISH
        self.object.find_form_representation_in_the_dataframe(form=form)
        # pprint(self.object.matches)
        if len(self.object.matches) == 0:
            self.fail()
