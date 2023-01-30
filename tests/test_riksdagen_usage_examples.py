# from unittest import TestCase
#
# import pandas as pd
#
# from lexutils.models.disabled.riksdagen_usage_examples import RiksdagenUsageExamples
# from lexutils.models.wikidata.enums import WikimediaLanguageCode
# from lexutils.models.wikidata.lexutils_form import LexutilsForm
#
#
# class TestRiksdagenUsageExamples(TestCase):
#     object: RiksdagenUsageExamples = RiksdagenUsageExamples()
#     object.dataframe = pd.DataFrame(data=[dict(id="testid", sentence="test")])
#
#     def test_find_form_representation_in_the_dataframe(self):
#         form = LexutilsForm(
#             representation="test", language_code=WikimediaLanguageCode.SWEDISH
#         )
#         self.object.find_form_representation_in_the_dataframe(form=form)
#         # pprint(self.object.matches)
#         if len(self.object.matches) == 0:
#             self.fail()
#
#     def test_find_form_representation_in_the_dataframe_with_wrong_representation(self):
#         form = LexutilsForm(
#             representation="test", language_code=WikimediaLanguageCode.SWEDISH
#         )
#         self.object.find_form_representation_in_the_dataframe(form=form)
#         if len(self.object.matches) != 0:
#             self.fail()
#
#     def test_convert_matches_to_user_examples(self):
#         form = LexutilsForm(
#             representation="test", language_code=WikimediaLanguageCode.SWEDISH
#         )
#         self.object.find_form_representation_in_the_dataframe(form=form)
#         # pprint(self.object.usage_examples)
#         if len(self.object.usage_examples) == 0:
#             self.fail()
#         else:
#             for example in self.object.usage_examples:
#                 print(example)
