from dataclasses import dataclass
from datetime import datetime
from typing import List
from urllib.parse import quote

from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.form import Form


@dataclass
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

    # def __init__(
    #         self,
    #         id: str = None,
    #         text: str = None
    # ):
    #     if id is None:
    #         raise ValueError("id was None")
    #     if text is None:
    #         raise ValueError("text was None")
    #     self.text = text
    #     self.id = id

    def find_usage_examples_from_summary(
            self,
            form: Form = None,
    ) -> List[UsageExample]:
        pass

    def lookup_qid(self):
        pass

    def url(self):
        if self.base_url is None:
            raise ValueError(f"base_url was None for {self.source.name.title()}")
        return f"{self.base_url}{quote(self.id)}"

    def human_readable_url(self):
        return self.url()
