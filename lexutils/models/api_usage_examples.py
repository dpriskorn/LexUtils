from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from lexutils.models.usage_examples import UsageExamples

if TYPE_CHECKING:
    from lexutils.models.lexemes import Lexemes
    from lexutils.models.wikidata.form import Form


class APIUsageExamples(UsageExamples, ABC):
    def __init__(
            self,
            form: Form = None,
            lexemes: Lexemes = None
    ):
        if form is None:
            raise ValueError("form was None")
        if lexemes is None:
            raise ValueError("lexemes was None")
        self.form = form
        self.lexemes = lexemes
        self.get_records()
        self.process_records_into_usage_examples()

    @abstractmethod
    def get_records(self):
        pass

    @abstractmethod
    def process_records_into_usage_examples(self):
        pass
