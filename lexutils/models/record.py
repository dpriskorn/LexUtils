import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from urllib.parse import quote

from lexutils.config import config
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.form import Form


class Record:
    base_url: str = None
    id: str = None
    date: datetime = None
    # Used for Riksdagen records
    document_qid = None
    exact_hit: bool = False
    inexact_hit: bool = False
    language_code: WikimediaLanguageCode = None
    language_style = LanguageStyle = None
    # This is needed for the europarl source
    line_number: int = None
    source = SupportedExampleSources = None
    text: str = None
    type_of_reference = ReferenceType = None
    filename: str = None

    def __init__(
            self,
            id: str = None,
            text: str = None,
            date: datetime = None,
            filename: str = None
    ):
        if id is None:
            raise ValueError("id was None")
        if text is None:
            raise ValueError("text was None")
        self.text = text
        self.id = id
        # Optional
        if date is not None:
            self.date = date
        if filename is not None:
            self.filename = filename

    def find_usage_examples_from_summary(
            self,
            form: Form = None,
    ) -> List[UsageExample]:
        pass

    def extract_usage_example_if_suitable(
            self,
            form: Form = None,
    ) -> Optional[UsageExample]:
        # check if the form appears by first cleaning
        # away all chars and then split the text into words
        if form is None:
            raise ValueError("form was None")
        logger = logging.getLogger(__name__)
        # This is a very crude test for relevancy, we lower first to improve matching
        logger.debug(f"Sentence before cleaning: {self.text}")
        cleaned_sentence = self.text.lower()
        punctuations = [".", ",", "!", "?", "„", "“", "\n",
                       ":", ";", "`", "´", "$", "€"]
        for punctuation in punctuations:
            if punctuation in cleaned_sentence:
                cleaned_sentence = cleaned_sentence.replace(punctuation, " ")
        logger.debug(f"cleaned sentence: {cleaned_sentence}")
        if form.representation.lower() in cleaned_sentence.split():
            logger.info(f"The form '{form.representation}' was found in the cleaned sentence. :)")
            sentence_length = len(cleaned_sentence.split(" "))
            if (
                    config.min_word_count < sentence_length < config.max_word_count
            ):
                return UsageExample(text=self.text,
                                    record=self)
            else:
                logger.debug(f"{cleaned_sentence} was discarded based on length")

    def lookup_qid(self):
        pass

    def url(self):
        if self.base_url is None:
            raise ValueError(f"base_url was None for {self.source.name.title()}")
        return f"{self.base_url}{quote(self.id)}"

    def human_readable_url(self):
        return self.url()
