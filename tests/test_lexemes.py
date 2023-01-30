from unittest import TestCase

from lexutils.models.lexemes import Lexemes


class TestLexemes(TestCase):
    example_lexemes = Lexemes
    # def test_fetch_forms_without_an_example_20(self):
    #     lex = Lexemes(lang="sv")
    #     lex.__convert_str_to_enums__()
    #     lex.fetch_forms_without_an_example()
    #     assert len(lex.forms_without_an_example) == 20

    def setUp(self):
        self.test_fetch_forms_without_an_example_1()

    def test_fetch_forms_without_an_example_1(self):
        lex = Lexemes(lang="sv")
        lex.__convert_str_to_enums__()
        import config

        config.number_of_forms_to_fetch = 1
        config.require_form_confirmation = False
        lex.fetch_forms_without_an_example()
        assert len(lex.forms_without_an_example) == 1
        self.example_lexemes = lex

    def test_fetch_usage_examples(self):
        assert len(self.example_lexemes.forms_without_an_example) == 1
        self.example_lexemes.fetch_usage_examples()
        # lex.forms_without_an_example: List[LexutilsForm]
        form = self.example_lexemes.forms_without_an_example[0]
        assert form.number_of_examples_found == 0

    def test___get_results_from_sparql__(self):
        lex = Lexemes(lang="sv")
        lex.__convert_str_to_enums__()
        import config

        config.number_of_forms_to_fetch = 1
        lex.__get_results_from_sparql__()
        assert len(lex.results) == 2

    # def test_orthohin_url(self):
    #     assert False

    # def test_print_overview(self):
    #     assert False
