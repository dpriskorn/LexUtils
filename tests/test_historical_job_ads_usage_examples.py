from unittest import TestCase

import pandas as pd

from lexutils.models.historical_job_ads_usage_examples import HistoricalJobAdsUsageExamples
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.form import Form


class TestHistoricalJobAdsUsageExamples(TestCase):
    object: HistoricalJobAdsUsageExamples = HistoricalJobAdsUsageExamples()
    object.dataframe = pd.DataFrame(data=[dict(id="testid", sentence="test")])

    def test_find_form_representation_in_the_dataframe(self):
        form = Form(
            dict(),
            language_code=WikimediaLanguageCode.SWEDISH
        )
        form.representation = "test"
        self.object.find_form_representation_in_the_dataframe(form=form)
        # pprint(self.object.matches)
        if len(self.object.matches) == 0:
            self.fail()
