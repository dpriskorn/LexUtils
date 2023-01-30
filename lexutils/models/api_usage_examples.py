# from __future__ import annotations
#
# from abc import abstractmethod
# from typing import TYPE_CHECKING
#
# from lexutils.exceptions import MissingInformationError
# from lexutils.models.usage_examples import UsageExamples
#
# if TYPE_CHECKING:
#     from lexutils.models.lexemes import Lexemes
#     from lexutils.models.wikidata.lexutils_form import LexutilsForm
#
#
# class APIUsageExamples(UsageExamples):
#     def get_and_process_records(self):
#         if self.form is None:
#             raise MissingInformationError("form was None")
#         if self.lexemes is None:
#             raise MissingInformationError("lexemes was None")
#         self.get_records()
#         self.process_records_into_usage_examples()
#
#     @abstractmethod
#     def get_records(self):
#         pass
#
#     @abstractmethod
#     def process_records_into_usage_examples(self):
#         pass
