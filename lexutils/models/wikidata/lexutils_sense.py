from typing import Optional

from wikibaseintegrator.models import Sense  # type: ignore

import config
from lexutils.exceptions import MissingInformationError
from lexutils.models.wikidata.enums import WikimediaLanguageCode


class LexutilsSense(Sense):
    language_code: Optional[WikimediaLanguageCode] = None

    def __str__(self):
        """Return the id and the localized gloss and two fallback glosses"""
        return (
            f"{self.id}, glosses: {self.localized_gloss} ({self.language_code.value}),  "
            f"{self.localized_gloss_fallback_one} ({config.sense_gloss_fallback_language_one}),  "
            f"{self.localized_gloss_fallback_two} ({config.sense_gloss_fallback_language_two})"
        )

    @property
    def localized_gloss(self) -> str:
        if not self.language_code:
            raise MissingInformationError()
        return str(self.glosses.get(language=self.language_code.value))

    @property
    def localized_gloss_fallback_one(self) -> str:
        if not config.sense_gloss_fallback_language_one:
            raise MissingInformationError()
        gloss = self.glosses.get(language=config.sense_gloss_fallback_language_one)
        if gloss:
            return str(gloss)
        else:
            return ""

    @property
    def localized_gloss_fallback_two(self) -> str:
        if not config.sense_gloss_fallback_language_two:
            raise MissingInformationError()
        gloss = self.glosses.get(language=config.sense_gloss_fallback_language_two)
        if gloss:
            return str(gloss)
        else:
            return ""
