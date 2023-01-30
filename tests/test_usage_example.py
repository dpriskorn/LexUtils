from lexutils.enums import LanguageStyle, ReferenceType, SupportedExampleSources
from lexutils.models.record import Record
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.enums import WikimediaLanguageCode


class TestUsageExample:
    def test_str(self):
        record = Record(
            id="1",
            language_code=WikimediaLanguageCode.SWEDISH,
            language_style=LanguageStyle.INFORMAL,
            source=SupportedExampleSources.HISTORICAL_ADS,
            type_of_reference=ReferenceType.WRITTEN,
        )
        usage_example = UsageExample(
            text="test",
            record=record,
        )
        assert str(usage_example) == ""

    def test_number_of_words(self):
        record = Record(
            id="1",
            language_code=WikimediaLanguageCode.SWEDISH,
            language_style=LanguageStyle.INFORMAL,
            source=SupportedExampleSources.HISTORICAL_ADS,
            type_of_reference=ReferenceType.WRITTEN,
        )
        usage_example = UsageExample(
            text="test",
            record=record,
        )
        assert usage_example.number_of_words == 1
