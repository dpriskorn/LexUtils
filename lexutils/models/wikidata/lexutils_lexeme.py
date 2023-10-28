import logging
from typing import List, Optional

from consolemenu import SelectionMenu  # type: ignore
from wikibaseintegrator.entities import LexemeEntity  # type: ignore
from wikibaseintegrator.models import Sense  # type: ignore

import config
from lexutils.exceptions import MissingInformationError
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.lexutils_sense import LexutilsSense

logger = logging.getLogger(__name__)


class LexutilsLexeme(LexemeEntity):
    """This extends LexemeEntity from WikibaseIntegrator to make it easy
    to add usage examples using the models in that library"""

    lexutils_senses: List[LexutilsSense] = []
    language_code: WikimediaLanguageCode

    @property
    def url(self):
        return f"{config.wd_prefix}{self.id}"

    @property
    def usage_example_url(self):
        return f"https://www.wikidata.org/wiki/Lexeme:{self.id}#P5831"

    def get_lexutils_senses(self):
        logger.debug("get_lexutils_senses: running")
        if not self.language_code:
            raise MissingInformationError()
        self.lexutils_senses = []
        for sense in self.senses.senses:
            lexutils_sense = LexutilsSense().from_json(sense.get_json())
            lexutils_sense.language_code = self.language_code
            self.lexutils_senses.append(lexutils_sense)

    def choose_sense_menu(self) -> Optional[LexutilsSense]:
        """Returns a dictionary with sense_id -> sense_id
        and gloss -> gloss or False"""
        if self.lexutils_senses is None:
            raise ValueError("senses was None")
        menu = SelectionMenu(self.lexutils_senses, "Select a sense")
        menu.show()
        menu.join()
        index = menu.selected_option
        # logger.debug(f"index:{index}")
        # exit(0)
        if index is not None:
            logger.debug(f"selected:{index}")
            if index > (len(self.lexutils_senses) - 1):
                logger.debug("No sense was chosen")
                return None
            else:
                selected_item: LexutilsSense = self.lexutils_senses[index]
                logger.debug("Returning the chosen sense")
                return selected_item
        else:
            return None
