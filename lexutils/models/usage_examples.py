from __future__ import annotations
from abc import ABCMeta
from typing import List, TYPE_CHECKING

from lexutils.models.record import Record
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.form import Form

if TYPE_CHECKING:
    from lexutils.models.lexemes import Lexemes


class UsageExamples(metaclass=ABCMeta):
    """This is an abstract class that has 2 subclasses:
    APIUsageExamples and DataframeUsageExamples"""
    form: Form = None,
    lexemes: Lexemes = None
    records: List[Record] = None
    usage_examples: List[UsageExample] = None


