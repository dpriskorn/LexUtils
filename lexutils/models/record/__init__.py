import logging
from datetime import datetime
from typing import Any, List, Optional
from urllib.parse import quote

from pydantic import BaseModel

from lexutils.enums import LanguageStyle, ReferenceType, SupportedExampleSources
from lexutils.models.wikidata.enums import WikimediaLanguageCode

logger = logging.getLogger(__name__)


class Record(BaseModel):
    base_url: str = ""
    id: str = ""
    date: Optional[datetime] = None
    # Used for Riksdagen records
    document_qid: str = ""
    # exact_hit: bool = False
    # inexact_hit: bool = False
    language_code: WikimediaLanguageCode
    language_style: LanguageStyle
    # This is needed for the europarl source
    line_number: int = 0
    source: SupportedExampleSources
    text: str = ""
    type_of_reference: ReferenceType
    filename: str = ""
    # cleaned_sentence: str = ""
    # words: List[str] = []

    class Config:
        extra = "forbid"

    # @property
    # def __found_localized_representation__(self) -> bool:
    #     if self.form.localized_representation.lower() in self.words:
    #         logger.info(
    #             f"The form '{self.form.localized_representation}' was found in the cleaned sentence. :)"
    #         )
    #         return True
    #     else:
    #         return False

    # @property
    # def get_usage_example_if_representation_could_be_found(
    #     self,
    # ) -> Optional[Any]:
    #     logger.debug("extract_usage_example_if_suitable: running")
    #     from lexutils.models.wikidata.lexutils_form import LexutilsForm
    #
    #     print(self.form)
    #     if not isinstance(self.form, LexutilsForm):
    #         raise ValueError("form not a LexutilsForm")
    #     self.__clean_sentence__()
    #     example = self.__find_representation_and_extract_usage_example__()
    #     from lexutils.models.usage_example import UsageExample
    #     if isinstance(example, UsageExample):
    #         return example
    #     else:
    #         return None

    @property
    def number_of_words(self):
        return len(self.text.split())

    # def lookup_qid(self):
    #     pass

    @property
    def url(self):
        if not self.base_url:
            raise ValueError(f"base_url was None for {self.source.name.title()}")
        return f"{self.base_url}{quote(self.id)}"

    # @property
    # def human_readable_url(self):
    #     return f"{self.base_url}{quote(self.id)}"

    # def __clean_sentence__(self):
    #     logger.debug("__clean_sentence__: running")
    #     # This is a very crude test for relevancy, we lower first to improve matching
    #     logger.debug(f"Sentence before cleaning: {self.text}")
    #     cleaned_sentence = self.text.lower()
    #     punctuations = [
    #         ".",
    #         ",",
    #         "!",
    #         "?",
    #         "„",
    #         "“",
    #         "\n",
    #         ":",
    #         ";",
    #         "`",
    #         "´",
    #         "$",
    #         "€",
    #     ]
    #     for punctuation in punctuations:
    #         if punctuation in cleaned_sentence:
    #             cleaned_sentence = cleaned_sentence.replace(punctuation, " ")
    #     logger.debug(f"cleaned sentence: {cleaned_sentence}")
    #     self.cleaned_sentence = cleaned_sentence
    #
    # def __find_representation_and_extract_usage_example__(
    #     self,
    # ) -> Optional[Any]:
    #     logger.debug("__find_representation_and_extract_usage_example__: running")
    #     self.__extract_words__()
    #     return self.__get_usage_example__()
    #
    # def __extract_words__(self):
    #     # split on any whitespace
    #     self.words = self.cleaned_sentence.split()
    #
    # def __get_usage_example__(self) -> Optional[Any]:
    #     if self.__found_localized_representation__:
    #         logger.debug("found localized representation in the sentence")
    #         if config.min_word_count < self.number_of_words < config.max_word_count:
    #             from lexutils.models.usage_example import UsageExample
    #             return UsageExample(record=self)
    #         else:
    #             logger.debug(f"{self.cleaned_sentence} was discarded based on length")
    #             return None
    #     else:
    #         logger.debug(
    #             f"could not find localized representation in {self.cleaned_sentence}"
    #         )
    #         return None
