from unittest import TestCase

from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.lexutils_form import LexutilsForm
from lexutils.models.wikidata.lexutils_lexeme import LexutilsLexeme
from lexutils.models.wikidata.lexutils_sense import LexutilsSense


class TestLexutilsLexeme(TestCase):
    example_lexeme: LexutilsLexeme = None

    def setUp(self) -> None:
        self.__setup_example_lexeme__()

    def __setup_example_lexeme__(self):
        form = LexutilsForm(form_id="L38817-F9")
        form.language_code = WikimediaLanguageCode.SWEDISH
        form.setup_lexeme()
        self.example_lexeme = form.lexeme

    def test_url(self):
        assert self.example_lexeme.url == "http://www.wikidata.org/entity/L38817"

    def test_usage_example_url(self):
        assert (
            self.example_lexeme.usage_example_url
            == "https://www.wikidata.org/wiki/Lexeme:L38817#P5831"
        )

    def test_get_lexutils_senses(self):
        self.example_lexeme.get_lexutils_senses()
        for sense in self.example_lexeme.lexutils_senses:
            assert isinstance(sense, LexutilsSense)
        assert len(self.example_lexeme.lexutils_senses) == 1
