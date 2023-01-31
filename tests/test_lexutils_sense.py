import logging
from typing import Optional
from unittest import TestCase

from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.lexutils_form import LexutilsForm
from lexutils.models.wikidata.lexutils_sense import LexutilsSense

logger = logging.getLogger(__name__)


class TestLexutilsSense(TestCase):
    example_sense: Optional[LexutilsSense] = None

    def setUp(self) -> None:
        logger.debug("setUp: running")
        self.__setup_example_sense__()

    def __setup_example_sense__(self):
        logger.debug("__setup_example_sense__: running")
        form = LexutilsForm(form_id="L38817-F9")
        form.language_code = WikimediaLanguageCode.SWEDISH
        form.setup_lexeme()
        assert form.number_of_senses == 1
        self.example_sense = form.senses[0]

    def test_localized_gloss(self):
        assert (
            self.example_sense.localized_gloss
            == "stoltsera över något i avsikt att imponera"
        )

    def test_localized_gloss_fallback_one(self):
        assert self.example_sense.localized_gloss_fallback_one == ""

    def test_localized_gloss_fallback_two(self):
        assert self.example_sense.localized_gloss_fallback_two == ""
