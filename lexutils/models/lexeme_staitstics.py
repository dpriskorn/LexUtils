import logging

from wikibaseintegrator.wbi_helpers import execute_sparql_query

from lexutils.helpers import wdqs
from lexutils.models.lexemes import Lexemes
from lexutils.models.wikidata.enums import WikimediaLanguageCode


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
            language = Lexemes(language_code)
            language.calculate_statistics()
            language_objects.append(language)
        sorted_by_senses_with_p5137_per_lexeme = sorted(
            language_objects,
            key=lambda language: language.average_number_of_senses_with_P5137_per_lexeme,
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