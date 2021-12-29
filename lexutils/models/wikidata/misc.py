from __future__ import annotations
import logging
import random
from typing import List, TYPE_CHECKING

from wikibaseintegrator import wbi_config
from wikibaseintegrator.wbi_helpers import execute_sparql_query

from lexutils.config import config
from lexutils.helpers import wdqs
from lexutils.models.wikidata.entities import Lexeme, EntityID
from lexutils.models.wikidata.enums import WikimediaLanguageCode, WikimediaLanguageQID

if TYPE_CHECKING:
    from lexutils.models.wikidata.form import Form

wbi_config.config['USER_AGENT'] = config.user_agent


class ForeignID:
    id: str
    prop_nr: str  # This is the prop_nr with type ExternalId
    source_item_id: str  # This is the Q-item for the source

    def __init__(self,
                 id: str = None,
                 prop_nr: str = None,
                 source_item_id: str = None):
        self.id = id
        self.prop_nr = str(EntityID(prop_nr))
        self.source_item_id = str(EntityID(source_item_id))


class LexemeLanguage:
    lexemes: List[Lexeme]
    language_code: WikimediaLanguageCode
    language_qid: WikimediaLanguageQID
    senses_with_P5137_per_lexeme: float
    senses_with_P5137: int
    forms: int
    forms_with_an_example: int
    forms_without_an_example: List[Form]
    number_of_forms_without_an_example: int
    lexemes_count: int

    def __init__(self, language_code: str):
        self.language_code = WikimediaLanguageCode(language_code)
        self.language_qid = WikimediaLanguageQID[self.language_code.name]

    def fetch_forms_missing_an_example(self):
        logger = logging.getLogger(__name__)
        # title:Forms that have no example demonstrating them and that have at least
        # one sense with P5137 (item for this sense)
        random_offset = random.randint(20,1000)
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
                #logger.info(f"data:{entry.keys()}")
                #logging.info(f"lexeme_json:{entry}")
                from lexutils.models.wikidata.form import Form
                form = Form(entry)
                logger.info(f"appending {form} to list of forms")
                #logger.info("debug exit")
                #exit(0)
                self.forms_without_an_example.append(form)
        except KeyError:
            logger.error("Got no results")
        logger.info(f"Got {len(self.forms_without_an_example)} "
                    f"forms from WDQS for language {self.language_code.name}")

    def fetch_lexemes(self):
        # TODO port to use the Lexeme class instead of heavy dataframes which we don't need
        raise Exception("This is deprecated.")
        # results = execute_sparql_query(f'''
        # SELECT DISTINCT
        # ?entity_lid ?form ?word (?categoryLabel as ?category)
        # (?grammatical_featureLabel as ?feature) ?sense ?gloss
        # WHERE {{
        #   ?entity_lid a ontolex:LexicalEntry; dct:language wd:{self.language_qid.value}.
        #   VALUES ?excluded {{
        #     # exclude affixes and interfix
        #     wd:Q62155 # affix
        #     wd:Q134830 # prefix
        #     wd:Q102047 # suffix
        #     wd:Q1153504 # interfix
        #   }}
        #   MINUS {{?entity_lid wdt:P31 ?excluded.}}
        #   ?entity_lid wikibase:lexicalCategory ?category.
        #
        #   # We want only lexemes with both forms and at least one sense
        #   ?entity_lid ontolex:lexicalForm ?form.
        #   ?entity_lid ontolex:sense ?sense.
        #
        #   # Exclude lexemes without a linked QID from at least one sense
        #   ?sense wdt:P5137 [].
        #   ?sense skos:definition ?gloss.
        #   # Get only the swedish gloss, exclude otherwise
        #   FILTER(LANG(?gloss) = "{self.language_code.value}")
        #
        #   # This remove all lexemes with at least one example which is not
        #   # ideal
        #   MINUS {{?entity_lid wdt:P5831 ?example.}}
        #   ?form wikibase:grammaticalFeature ?grammatical_feature.
        #   # We extract the word of the form
        #   ?form ontolex:representation ?word.
        #   SERVICE wikibase:label
        #   {{ bd:serviceParam wikibase:language "{self.language_code.value},en". }}
        # }}
        # limit {config.sparql_results_size}
        # offset {config.sparql_offset}
        # ''')
        # self.lexemes = []
        # for lexeme_json in results:
        #     logging.debug(f"lexeme_json:{lexeme_json}")
        #     l = Lexeme.parse_wdqs_json(lexeme_json)
        #     self.lexemes.append(l)
        # logging.info(f"Got {len(self.lexemes)} lexemes from "
        #              f"WDQS for language {self.language_code.name}")

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

    def count_number_of_forms(self):
        pass

    def calculate_statistics(self):
        self.lexemes_count: int = self.count_number_of_lexemes()
        self.senses_with_P5137: int = self.count_number_of_senses_with_p5137()
        self.calculate_senses_with_p5137_per_lexeme()

    def calculate_senses_with_p5137_per_lexeme(self):
        self.senses_with_P5137_per_lexeme = round(
            self.senses_with_P5137 / self.lexemes_count, 3
        )

    def print(self):
        print(f"{self.language_code.name} has "
              f"{self.senses_with_P5137} senses with linked QID in "
              f"total on {self.lexemes_count} lexemes "
              f"which is {self.senses_with_P5137_per_lexeme} per lexeme.")


class LexemeStatistics:
    total_lexemes: int

    def __init__(self):
        self.calculate_total_lexemes()
        self.rank_languages_based_on_statistics()

    def calculate_total_lexemes(self):
        """Calculate how many lexemes exists in Wikidata"""
        result = (execute_sparql_query(f'''
        SELECT
        (COUNT(?l) as ?count)
        WHERE {{
          ?l a ontolex:LexicalEntry.
        }}'''))
        count: int = wdqs.extract_count(result)
        logging.debug(f"count:{count}")
        self.total_lexemes = count

    def rank_languages_based_on_statistics(self):
        logger = logging.getLogger(__name__)
        language_objects = []
        print("Fetching data...")
        for language_code in WikimediaLanguageCode:
            logger.info(f"Working on {language_code.name}")
            language = LexemeLanguage(language_code)
            language.calculate_statistics()
            language_objects.append(language)
        sorted_by_senses_with_p5137_per_lexeme = sorted(
            language_objects,
            key=lambda language: language.senses_with_P5137_per_lexeme,
            reverse=True
        )
        print("Languages ranked by most senses linked to items:")
        for language in sorted_by_senses_with_p5137_per_lexeme:
            language.print()
        # Generator expression
        total_lexemes_among_supported_languages: int = sum(
            language.lexemes_count for language in language_objects
        )
        # logger.debug(f"total:{total_lexemes_among_supported_languages}")
        percent = round(
            total_lexemes_among_supported_languages * 100 / self.total_lexemes
        )
        print(f"These languages have {total_lexemes_among_supported_languages} "
              f"lexemes out of {self.total_lexemes} in total ({percent}%)")