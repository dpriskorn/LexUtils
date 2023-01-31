from typing import Optional
from unittest import TestCase

from lexutils.enums import LanguageStyle, ReferenceType, SupportedExampleSources
from lexutils.models.record import Record
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.lexutils_form import LexutilsForm


class TestUsageExample(TestCase):
    example_form: Optional[LexutilsForm] = None

    def setUp(self) -> None:
        self.__setup_example_form__()

    def __setup_example_form__(self):
        # skrutits
        form = LexutilsForm(form_id="L38817-F9")
        form.language_code = WikimediaLanguageCode.SWEDISH
        form.setup_lexeme()
        self.example_form = form

    def test_str(self):
        record = Record(
            id="1",
            language_code=WikimediaLanguageCode.SWEDISH,
            language_style=LanguageStyle.INFORMAL,
            source=SupportedExampleSources.HISTORICAL_ADS_2020,
            type_of_reference=ReferenceType.WRITTEN,
            text="test",
        )
        usage_example = UsageExample(record=record, form=self.example_form)
        assert str(usage_example) == "test (from 1 at Historical_Ads_2020)"

    def test_number_of_words(self):
        record = Record(
            id="1",
            language_code=WikimediaLanguageCode.SWEDISH,
            language_style=LanguageStyle.INFORMAL,
            source=SupportedExampleSources.HISTORICAL_ADS_2020,
            type_of_reference=ReferenceType.WRITTEN,
            text="test",
        )
        usage_example = UsageExample(record=record, form=self.example_form)
        assert usage_example.number_of_words == 1
