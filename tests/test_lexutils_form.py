from unittest import TestCase

from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.lexutils_form import LexutilsForm


class TestLexutilsForm(TestCase):
    example_form: LexutilsForm = None

    def setUp(self) -> None:
        self.__setup_example_form__()

    def __setup_example_form__(self):
        form = LexutilsForm(form_id="L38817-F9")
        form.language_code = WikimediaLanguageCode.SWEDISH
        form.setup_lexeme()
        self.example_form = form

    def test_number_of_examples_found(self):
        self.example_form.usage_examples = []
        assert self.example_form.number_of_examples_found == 0

    def test_number_of_senses(self):
        print(self.example_form.senses)
        assert self.example_form.number_of_senses == 1

    def test_localized_lexeme_category(self):
        assert self.example_form.localized_lexeme_category == "verb"

    def test_lexeme_category(self):
        assert self.example_form.lexeme_category == "Q24905"

    def test_lexeme_id(self):
        assert self.example_form.lexeme_id == "L38817"

    def test_senses(self):
        assert isinstance(self.example_form.senses, list)

    def test_localized_grammatical_features(self):
        assert self.example_form.localized_grammatical_features == [
            "passivum",
            "supinum",
        ]

    def test_localized_representation(self):
        assert self.example_form.localized_representation == "skrutits"

    def test_presentation(self):
        assert self.example_form.presentation == (
            "[bold green]skrutits[/bold green]\n"
            "category: Q24905\n"
            "features: passivum, supinum"
        )

    def test_url(self):
        assert self.example_form.url == "http://www.wikidata.org/entity/L38817-F9"
