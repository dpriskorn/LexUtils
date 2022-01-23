from __future__ import annotations
import logging
import random
from typing import List, TYPE_CHECKING

from wikibaseintegrator.wbi_helpers import execute_sparql_query

from lexutils.config import config, constants
from lexutils.config.enums import SupportedFormPickles
from lexutils.helpers import wdqs, tui, util
from lexutils.helpers.console import console
from lexutils.helpers.handle_pickles import read_from_pickle, add_to_pickle
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.entities import Lexeme
from lexutils.models.wikidata.enums import WikimediaLanguageCode, WikimediaLanguageQID
from lexutils.models.wikidata.form import Form
from lexutils.models.wikisource_usage_examples import WikisourceUsageExamples

if TYPE_CHECKING:
    from lexutils.models.historical_job_ads_usage_examples import HistoricalJobAdsUsageExamples
    from lexutils.models.riksdagen_usage_examples import RiksdagenUsageExamples
    from lexutils.models.dataframe_usage_examples import DataframeUsageExamples


class Lexemes:
    """This class holds all lexemes and forms we currently work on

    We store the dataframes into the attributes to avoid loading
    them more than once"""
    average_number_of_senses_with_P5137_per_lexeme: float = 0.0
    riksdagen_usage_examples: DataframeUsageExamples = None
    forms_without_an_example: List[Form] = None
    forms_with_usage_examples_found: List[Form] = None
    historical_ads_usage_examples: DataframeUsageExamples = None
    language_code: WikimediaLanguageCode = None
    language_qid: WikimediaLanguageQID = None
    lexemes: List[Lexeme] = None
    lexemes_count: int = 0
    number_of_forms_without_an_example: int = 0
    number_of_forms_without_an_example: int = 0
    number_of_senses_with_P5137: int = 0

    def __get_usage_examples_from_apis__(
            self,
            form: Form = None,
    ) -> List[UsageExample]:
        """Find examples and return them as Example objects"""
        if form is None:
            raise ValueError("form was None")
        logger = logging.getLogger(__name__)
        examples = []
        # Europarl corpus
        # Download first if not on disk
        # TODO convert to UsageExample
        # download_data.fetch()
        # europarl_records = europarl.get_records(form)
        # for record in europarl_records:
        #     records[record] = europarl_records[record]
        # logger.debug(f"records in total:{len(records)}")
        if self.language_code == WikimediaLanguageCode.SWEDISH:
            historical_ads_examples = self.historical_ads_usage_examples.find_form_representation_in_the_dataframe(
                form=form)
            if historical_ads_examples is not None:
                examples.extend(historical_ads_examples)
            # print("debug exit")
            # exit()
            riksdagen_examples = self.riksdagen_usage_examples.find_form_representation_in_the_dataframe(form=form)
            if riksdagen_examples is not None:
                examples.extend(riksdagen_examples)
        # ksamsok
        # Disabled because it yields very little of value
        # unfortunately because the data is such low quality overall
        # ksamsok_records = ksamsok.get_records(form)
        # for record in ksamsok_records:
        #     records[record] = ksamsok_records[record]
        # logger.debug(f"records in total:{len(records)}")
        # Wikisource
        if len(examples) < 50:
            # If we already got 50 examples from a better source,
            # then don't fetch from Wikisource
            wikisource_usage_examples = WikisourceUsageExamples(
                form=form,
                lexemes=self
            )
            if wikisource_usage_examples.usage_examples is not None:
                examples.extend(wikisource_usage_examples.usage_examples)
        # Check for nested list
        for example in examples:
            if not isinstance(example, UsageExample):
                raise ValueError("Nested list error")
        if len(examples) > 0:
            logger.debug(f"examples found:{[example.text for example in examples]}")
        return examples

    def __init__(self, language_code: str):
        self.language_code = WikimediaLanguageCode(language_code)
        self.language_qid = WikimediaLanguageQID[self.language_code.name]

    def fetch_forms_without_an_example(self):
        logger = logging.getLogger(__name__)
        # title:Forms that have no example demonstrating them and that have at least
        # one sense with P5137 (item for this sense)
        random_offset = random.randint(20, 1000)
        logger.info(f"random offset:{random_offset}")
        results = execute_sparql_query(f'''
                select ?lexeme ?form ?form_representation ?category  
                (group_concat(distinct ?feature; separator = ",") as ?grammatical_features)
                WHERE {{
                    ?lexeme dct:language wd:{self.language_qid.value};
                            wikibase:lemma ?lemma;
                            wikibase:lexicalCategory ?category;
                            ontolex:lexicalForm ?form;
                            ontolex:sense ?sense.
                    ?sense wdt:P5137 [].
                    ?form ontolex:representation ?form_representation;
                    wikibase:grammaticalFeature ?feature.
                    MINUS {{
                    ?lexeme p:P5831 ?statement.
                    ?statement ps:P5831 ?example;
                             pq:P6072 [];
                             pq:P5830 ?form_with_example.
                    }}
                }}
                group by ?lexeme ?form ?form_representation ?category
                offset {random_offset}
                limit {config.number_of_forms_to_fetch}''',
                                       debug=False)
        self.forms_without_an_example = []
        # pprint(results)
        if "results" in results:
            if "bindings" in results["results"]:
                # logger.debug(f"data:{results['results']['bindings']}")
                forms = results["results"]['bindings']
                logger.info(f"Got {len(forms)} lexemes")
                for entry in forms:
                    # logger.info(f"data:{entry.keys()}")
                    # logging.debug(f"lexeme_json:{entry}")
                    form = Form(entry, language_code=self.language_code)
                    logger.info(f"appending {form} to list of forms")
                    # logger.info("debug exit")
                    # exit(0)
                    self.forms_without_an_example.append(form)
            else:
                raise ValueError("Got no bindings dict from WD")
        else:
            raise ValueError("Got no results dict from WD")
        if len(self.forms_without_an_example) == 0:
            console.print("Got no forms from Wikidata to work on for this language "
                          "if you think this is a bug, please open an issue here "
                          f"{tui.issue_url()}")
            exit()
        else:
            logger.info(f"Got {len(self.forms_without_an_example)} "
                        f"forms from WDQS for language {self.language_code.name.title()}")

    def calculate_statistics(self):
        self.lexemes_count: int = self.count_number_of_lexemes()
        self.number_of_senses_with_P5137: int = self.count_number_of_senses_with_p5137()
        self.calculate_senses_with_p5137_per_lexeme()

    def calculate_senses_with_p5137_per_lexeme(self):
        self.average_number_of_senses_with_P5137_per_lexeme = round(
            self.number_of_senses_with_P5137 / self.lexemes_count, 3
        )

    def count_number_of_lexemes(self):
        """Returns an int"""
        logger = logging.getLogger(__name__)
        result = (execute_sparql_query(f'''
            SELECT
            (COUNT(?l) as ?count)
            WHERE {{
              ?l dct:language wd:{self.language_qid.value}.
            }}'''))
        logger.debug(f"result:{result}")
        count: int = wdqs.extract_count(result)
        logging.debug(f"count:{count}")
        return count

    def count_number_of_senses_with_p5137(self):
        """Returns an int"""
        logger = logging.getLogger(__name__)
        result = (execute_sparql_query(f'''
            SELECT
            (COUNT(?sense) as ?count)
            WHERE {{
              ?l dct:language wd:{self.language_qid.value}.
              ?l ontolex:sense ?sense.
              ?sense skos:definition ?gloss.
              # Exclude lexemes without a linked QID from at least one sense
              ?sense wdt:P5137 [].
            }}'''))
        logger.debug(f"result:{result}")
        count: int = wdqs.extract_count(result)
        logging.debug(f"count:{count}")
        return count

    def count_number_of_forms_without_an_example(self):
        """Returns an int"""
        # TODO fix this to count all senses in a given language
        result = (execute_sparql_query(f'''
            SELECT
            (COUNT(?form) as ?count)
            WHERE {{
              ?l dct:language wd:{self.language_qid.value}.
              ?l ontolex:lexicalForm ?form.
              ?l ontolex:sense ?sense.
              # exclude lexemes that already have at least one example
              MINUS {{?l wdt:P5831 ?example.}}
              # Exclude lexemes without a linked QID from at least one sense
              ?sense wdt:P5137 [].
            }}'''))
        count: int = wdqs.extract_count(result)
        logging.debug(f"count:{count}")
        self.number_of_forms_without_an_example = count

    def count_number_of_forms_with_examples(self):
        pass

    def fetch_usage_examples(self):
        """Fetch usage examples for all forms"""
        if self.forms_without_an_example is None:
            raise ValueError("self.forms_without_an_example was None")
        number_of_forms = len(self.forms_without_an_example)
        if number_of_forms == 0:
            raise ValueError("self.forms_without_an_example was empty")
        logger = logging.getLogger(__name__)
        # console.print(f"Fetching usage examples for {len(self.forms_without_an_example)} forms")
        # console.print(f"Fetching usage examples for all forms")
        # from http://stackoverflow.com/questions/306400/ddg#306417
        # We do this now because we only want to do it once
        # and keep it in memory during the looping through all the forms
        if self.language_code == WikimediaLanguageCode.SWEDISH:
            from lexutils.models.historical_job_ads_usage_examples import HistoricalJobAdsUsageExamples
            from lexutils.models.riksdagen_usage_examples import RiksdagenUsageExamples
            self.historical_ads_usage_examples = HistoricalJobAdsUsageExamples()
            self.riksdagen_usage_examples = RiksdagenUsageExamples()
        self.forms_with_usage_examples_found = []
        count = 1
        approved_forms = []
        if config.require_form_confirmation:
            for form in self.forms_without_an_example:
                if util.yes_no_question(tui.work_on(form=form)):
                    approved_forms.append(form)
                else:
                    logger.info("Adding form to declined pickle")
                    add_to_pickle(pickle=SupportedFormPickles.DECLINED_FORMS,
                                  form_id=form.id)
        else:
            # Approve all forms
            approved_forms.extend(self.forms_without_an_example)
        for form in approved_forms:
            finished = read_from_pickle(pickle=SupportedFormPickles.FINISHED_FORMS,
                                        form_id=form.id)
            declined = read_from_pickle(pickle=SupportedFormPickles.DECLINED_FORMS,
                                        form_id=form.id)
            if not finished and not declined:
                with console.status(f"Processing form {count}/{number_of_forms}"):
                    if form.lexeme_id is None:
                        raise ValueError("lexeme_id on form was None")
                    # fetch usage examples
                    # Fetch sentence data from all APIs
                    form.usage_examples: List[UsageExample] = self.__get_usage_examples_from_apis__(
                        form=form,
                    )
                    form.number_of_examples_found = len(form.usage_examples)
                    if form.number_of_examples_found > 0:
                        self.forms_with_usage_examples_found.append(form)
            count += 1

    def orthohin_url(self):
        return f"{constants.orthohin}add/{self.language_code.value}"

    def print_overview(self):
        print(f"{self.language_code.name} has "
              f"{self.number_of_senses_with_P5137} senses with linked QID in "
              f"total on {self.lexemes_count} lexemes "
              f"which is {self.average_number_of_senses_with_P5137_per_lexeme} per lexeme.")

# def count_number_of_forms(self):
#     pass

# def fetch_lexemes(self):
#     # TODO port to use the Lexeme class instead of heavy dataframes which we don't need
#     raise Exception("This is deprecated.")
#     # results = execute_sparql_query(f'''
#     # SELECT DISTINCT
#     # ?entity_lid ?form ?word (?categoryLabel as ?category)
#     # (?grammatical_featureLabel as ?feature) ?sense ?gloss
#     # WHERE {{
#     #   ?entity_lid a ontolex:LexicalEntry; dct:language wd:{self.language_qid.value}.
#     #   VALUES ?excluded {{
#     #     # exclude affixes and interfix
#     #     wd:Q62155 # affix
#     #     wd:Q134830 # prefix
#     #     wd:Q102047 # suffix
#     #     wd:Q1153504 # interfix
#     #   }}
#     #   MINUS {{?entity_lid wdt:P31 ?excluded.}}
#     #   ?entity_lid wikibase:lexicalCategory ?category.
#     #
#     #   # We want only lexemes with both forms and at least one sense
#     #   ?entity_lid ontolex:lexicalForm ?form.
#     #   ?entity_lid ontolex:sense ?sense.
#     #
#     #   # Exclude lexemes without a linked QID from at least one sense
#     #   ?sense wdt:P5137 [].
#     #   ?sense skos:definition ?gloss.
#     #   # Get only the swedish gloss, exclude otherwise
#     #   FILTER(LANG(?gloss) = "{self.language_code.value}")
#     #
#     #   # This remove all lexemes with at least one example which is not
#     #   # ideal
#     #   MINUS {{?entity_lid wdt:P5831 ?example.}}
#     #   ?form wikibase:grammaticalFeature ?grammatical_feature.
#     #   # We extract the word of the form
#     #   ?form ontolex:representation ?word.
#     #   SERVICE wikibase:label
#     #   {{ bd:serviceParam wikibase:language "{self.language_code.value},en". }}
#     # }}
#     # limit {config.sparql_results_size}
#     # offset {config.sparql_offset}
#     # ''')
#     # self.lexemes = []
#     # for lexeme_json in results:
#     #     logging.debug(f"lexeme_json:{lexeme_json}")
#     #     l = Lexeme.parse_wdqs_json(lexeme_json)
#     #     self.lexemes.append(l)
#     # logging.info(f"Got {len(self.lexemes)} lexemes from "
#     #              f"WDQS for language {self.language_code.name}")
