from typing import Optional
from unittest import TestCase

from lexutils.enums import LanguageStyle, ReferenceType, SupportedExampleSources
from lexutils.models.record import Record
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.lexutils_form import LexutilsForm


class TestRecord(TestCase):
    example_form: Optional[LexutilsForm] = None

    def setUp(self) -> None:
        self.__setup_example_form__()

    def __setup_example_form__(self):
        # skrutits
        form = LexutilsForm(form_id="L38817-F9")
        form.language_code = WikimediaLanguageCode.SWEDISH
        form.setup_lexeme()
        self.example_form = form

    # def test_get_usage_example_if_representation_could_be_found_too_short(self):
    #     record = Record(
    #         id="1",
    #         text=" skrutits ",
    #         language_code=WikimediaLanguageCode.SWEDISH,
    #         language_style=LanguageStyle.INFORMAL,
    #         source=SupportedExampleSources.HISTORICAL_ADS_2020,
    #         type_of_reference=ReferenceType.WRITTEN,
    #         form=self.example_form,
    #     )
    #     assert record.get_usage_example_if_representation_could_be_found is None
    #
    # def test_get_usage_example_if_representation_could_be_found_too_long(self):
    #     record = Record(
    #         id="1",
    #         text=" skrutits skrutits skrutits skrutits skrutits skrutits skrutits "
    #         "skrutits skrutits skrutits skrutits skrutits skrutits skrutits skrutits skrutits ",
    #         language_code=WikimediaLanguageCode.SWEDISH,
    #         language_style=LanguageStyle.INFORMAL,
    #         source=SupportedExampleSources.HISTORICAL_ADS_2020,
    #         type_of_reference=ReferenceType.WRITTEN,
    #         form=self.example_form,
    #     )
    #     assert record.get_usage_example_if_representation_could_be_found is None
    #
    # def test_get_usage_example_if_representation_could_be_found_valid(self):
    #     record = Record(
    #         id="1",
    #         text=" skrutits skrutits skrutits skrutits "
    #         "skrutits skrutits skrutits skrutits skrutits skrutits skrutits skrutits skrutits ",
    #         language_code=WikimediaLanguageCode.SWEDISH,
    #         language_style=LanguageStyle.INFORMAL,
    #         source=SupportedExampleSources.HISTORICAL_ADS_2020,
    #         type_of_reference=ReferenceType.WRITTEN,
    #         form=self.example_form,
    #     )
    #     usage_example = record.get_usage_example_if_representation_could_be_found
    #     assert isinstance(usage_example, UsageExample)
    #     assert usage_example.text == (
    #         " skrutits skrutits skrutits skrutits skrutits skrutits skrutits skrutits "
    #         "skrutits skrutits skrutits skrutits skrutits "
    #     )

    # def test_lookup_qid(self):
    #     assert False
    #
    def test_url_no_baseurl(self):
        record = Record(
            id="1",
            text=" skrutits skrutits skrutits skrutits "
            "skrutits skrutits skrutits skrutits skrutits skrutits skrutits skrutits skrutits ",
            language_code=WikimediaLanguageCode.SWEDISH,
            language_style=LanguageStyle.INFORMAL,
            source=SupportedExampleSources.HISTORICAL_ADS_2020,
            type_of_reference=ReferenceType.WRITTEN,
        )
        with self.assertRaises(ValueError):
            assert record.url == ""

    def test_url_with_baseurl(self):
        record = Record(
            base_url="test",
            id="1",
            text=" skrutits skrutits skrutits skrutits "
            "skrutits skrutits skrutits skrutits skrutits skrutits skrutits skrutits skrutits ",
            language_code=WikimediaLanguageCode.SWEDISH,
            language_style=LanguageStyle.INFORMAL,
            source=SupportedExampleSources.HISTORICAL_ADS_2020,
            type_of_reference=ReferenceType.WRITTEN,
        )
        assert record.url == "test1"

    #
    # def test_human_readable_url(self):
    #     assert False

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
