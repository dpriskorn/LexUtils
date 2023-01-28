from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lexutils.models.record import Record


class UsageExample:
    # This contains the example, usually a single text
    text: str
    record: Record
    word_count: int = None

    def __init__(self,
                 text: str = None,
                 record: Record = None):
        """This models a usage example.

        Note we pass both the text and the record,
        because the record.text can contain more text
        than the text we found in it"""
        if text is not None:
            self.text = text
            self.word_count = len(self.text.split(" "))
        else:
            raise Exception("Missing text")
        if record is not None:
            self.record = record
        else:
            raise Exception("Missing record")

    def __str__(self):
        return f"{self.text} (from {self.record.id} at {self.record.source.name.title()})"
