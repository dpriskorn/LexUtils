from typing import Any

from pydantic import BaseModel


class UsageExample(BaseModel):
    """This models the example, usually a single text

    The text should be cleaned before inserted if necessary"""

    text: str
    record: Any

    def __str__(self):
        from lexutils.models.record import Record

        if not isinstance(self.record, Record):
            raise ValueError()
        return (
            f"{self.text} (from {self.record.id} at {self.record.source.name.title()})"
        )

    @property
    def number_of_words(self):
        # from https://www.pythonpool.com/python-count-words-in-string/
        return len(self.text.strip().split())
