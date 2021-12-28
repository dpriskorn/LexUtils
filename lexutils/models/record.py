from datetime import datetime

from lexutils.config.enums import SupportedExampleSources, LanguageStyle, ReferenceType
from lexutils.models.wikidata.enums import WikimediaLanguageCode


class Record:
    base_url: str = None
    id: str
    date: datetime
    # Used for Riksdagen records
    document_qid = None
    exact_hit: bool = False
    inexact_hit: bool = False
    language_code: WikimediaLanguageCode = None
    language_style = LanguageStyle
    # This is needed for the europarl source
    line_number: int = None
    source = SupportedExampleSources
    summary: str
    type_of_reference = ReferenceType

    def lookup_qid(self):
        pass

    def url(self):
        if self.base_url is None:
            raise ValueError("base_url was None")
        return f"{self.base_url}{self.id}"
