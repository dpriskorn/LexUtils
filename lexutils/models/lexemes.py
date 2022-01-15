import logging
import random
from typing import List, Optional

from pandas import DataFrame
from wikibaseintegrator.wbi_helpers import execute_sparql_query

from lexutils.config import config
from lexutils.config.enums import SupportedFormPickles
from lexutils.helpers import wdqs, tui
from lexutils.helpers.console import console
from lexutils.helpers.handle_pickles import read_from_pickle
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.entities import Lexeme
from lexutils.models.wikidata.enums import WikimediaLanguageCode, WikimediaLanguageQID
from lexutils.models.wikidata.form import Form
from lexutils.modules import historical_job_ads, wikisource, riksdagen


class Lexemes:
    """This class holds all lexemes and forms we currently work on"""
    average_number_of_senses_with_P5137_per_lexeme: float
    forms_without_an_example: List[Form]
    forms_with_usage_examples_found: List[Form]
    historical_ads_dataframe: DataFrame = None
    language_code: WikimediaLanguageCode
    language_qid: WikimediaLanguageQID
    lexemes: List[Lexeme]
    lexemes_count: int
    number_of_forms_without_an_example: int
    number_of_forms_without_an_example: int
    number_of_senses_with_P5137: int

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
            limit {config.number_of_forms_to_fetch}''')
        self.forms_without_an_example = []
        logger.info("Got the data")
        logger.info(f"data:{results.keys()}")
        try:
            # logger.info(f"data:{results['results']['bindings']}")
            for entry in results["results"]['bindings']:
                # logger.info(f"data:{entry.keys()}")
                # logging.info(f"lexeme_json:{entry}")
                from lexutils.models.wikidata.form import Form
                form = Form(entry)
                logger.info(f"appending {form} to list of forms")
                # logger.info("debug exit")
                # exit(0)
                self.forms_without_an_example.append(form)
        except KeyError:
            logger.error("Got no results")
        if len(self.forms_without_an_example) == 0:
            console.print("Got no forms from Wikidata to work on for this language "
                          "if you think this is a bug, please open an issue here "
                          f"{tui.issue_url()}")
            exit()
        else:
            logger.info(f"Got {len(self.forms_without_an_example)} "
                        f"forms from WDQS for language {self.language_code.name.title()}")

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

    # def count_number_of_forms(self):
    #     pass

    def calculate_statistics(self):
        self.lexemes_count: int = self.count_number_of_lexemes()
        self.number_of_senses_with_P5137: int = self.count_number_of_senses_with_p5137()
        self.calculate_senses_with_p5137_per_lexeme()

    def calculate_senses_with_p5137_per_lexeme(self):
        self.average_number_of_senses_with_P5137_per_lexeme = round(
            self.number_of_senses_with_P5137 / self.lexemes_count, 3
        )

    def print(self):
        print(f"{self.language_code.name} has "
              f"{self.number_of_senses_with_P5137} senses with linked QID in "
              f"total on {self.lexemes_count} lexemes "
              f"which is {self.average_number_of_senses_with_P5137_per_lexeme} per lexeme.")

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
            historical_job_ads_examples: Optional[List[UsageExample]] = \
                historical_job_ads.find_form_representation_in_the_dataframe(
                    dataframe=self.historical_ads_dataframe,
                    form=form
                )
            if historical_job_ads_examples:
                examples.extend(historical_job_ads_examples)
            # print("debug exit")
            # exit()
            # Riksdagen API is slow, only use it if we don't have a lot of sentences already
            if len(examples) < 25:
                riksdagen_examples: List[UsageExample] = riksdagen.get_records(
                    form=form,
                    lexemes=self
                )
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
            with console.status(
                    f"Fetching usage examples from the {self.language_code.name.title()} Wikisource..."):
                examples.extend(wikisource.get_records(
                    form=form,
                    lexemes=self
                ))
        # Check for nested list
        for example in examples:
            if not isinstance(example, UsageExample):
                raise ValueError("Nested list error")
        if len(examples) > 0:
            logger.debug(f"examples found:{[example.text for example in examples]}")
        return examples

    def fetch_usage_examples(self):
        """Fetch usage examples for all forms"""
        if self.forms_without_an_example is None:
            raise ValueError("self.forms_without_an_example was None")
        if len(self.forms_without_an_example) == 0:
            raise ValueError("self.forms_without_an_example was empty")
        logger = logging.getLogger(__name__)
        console.print(f"Fetching usage examples for {len(self.forms_without_an_example)} forms")
        console.print(f"Fetching usage examples for all forms")
        # from http://stackoverflow.com/questions/306400/ddg#306417
        # We do this now because we only want to do it once
        # and keep it in memory during the looping through all the forms
        if self.language_code.SWEDISH:
            self.historical_ads_dataframe = historical_job_ads.download_and_load_into_memory()
        self.forms_with_usage_examples_found = []
        for form in self.forms_without_an_example:
            finished = read_from_pickle(pickle=SupportedFormPickles.FINISHED_FORMS,
                                        form_id=form.id)
            declined = read_from_pickle(pickle=SupportedFormPickles.DECLINED_FORMS,
                                        form_id=form.id)
            if not finished and not declined:
                logging.info(f"processing:{form.representation}")
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
