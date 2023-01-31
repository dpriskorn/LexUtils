from typing import Optional
from unittest import TestCase

from lexutils.models.lexemes import Lexemes
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.lexutils_form import LexutilsForm


class TestLexemes(TestCase):
    example_lexemes: Optional[Lexemes] = []
    example_form: Optional[LexutilsForm] = None

    # def test_fetch_forms_without_an_example_20(self):
    #     lex = Lexemes(lang="sv")
    #     lex.__convert_str_to_enums__()
    #     lex.fetch_forms_without_an_example()
    #     assert len(lex.forms_without_an_example) == 20

    def setUp(self):
        self.__setup_example_form__()
        self.__setup_example_lexemes__()

    def __setup_example_form__(self):
        form = LexutilsForm(form_id="L45469-F1") # arbeta
        form.language_code = WikimediaLanguageCode.SWEDISH
        form.setup_lexeme()
        self.example_form = form

    def __setup_example_lexemes__(self):
        lex = Lexemes(lang="sv", testing=True)
        lex.__convert_str_to_enums__()
        lex.forms_without_an_example_in_wikidata = [self.example_form]
        self.example_lexemes = lex

    def test_fetch_forms_without_an_example_1(self):
        lex = Lexemes(lang="sv", testing=True)
        lex.__convert_str_to_enums__()
        import config

        config.number_of_forms_to_fetch = 1
        config.require_form_confirmation = False
        lex.fetch_forms_without_an_example()
        assert len(lex.forms_without_an_example_in_wikidata) == 1

    def test_fetch_usage_examples(self):
        assert len(self.example_lexemes.forms_without_an_example_in_wikidata) == 1
        self.example_lexemes.fetch_usage_examples()
        # lex.forms_without_an_example: List[LexutilsForm]
        form = self.example_lexemes.forms_without_an_example_in_wikidata[0]
        assert form.number_of_usage_examples_found == 59

    def test___get_results_from_sparql__(self):
        lex = Lexemes(lang="sv")
        lex.__convert_str_to_enums__()
        import config

        config.number_of_forms_to_fetch = 1
        lex.__get_results_from_sparql__()
        assert len(lex.sparql_results) == 2

    # def test_orthohin_url(self):
    #     assert False

    # def test_print_overview(self):
    #     assert False
