import logging
from enum import Enum
from typing import List, Dict

from wikibaseintegrator import wbi_core, wbi_datatype

# We get the URL for the Wikibase from here
from lexutils import config
from wikibaseintegrator.wbi_functions import execute_sparql_query

from lexutils.modules import wdqs


class WikimediaLanguageCode(Enum):
    DANISH = "da"
    SWEDISH = "sv"
    BOKMÅL = "nb"
    ENGLISH = "en"
    FRENCH = "fr"


class WikimediaLanguageQID(Enum):
    DANISH = "Q9035"
    SWEDISH = "Q9027"
    BOKMÅL = "Q25167"
    ENGLISH = "Q1860"
    FRENCH = "Q150"


class WikidataNamespaceLetters(Enum):
    PROPERTY = "P"
    ITEM = "Q"
    LEXEME = "L"


class EntityID:
    letter: WikidataNamespaceLetters
    number: int

    def __init__(self,
                 entity_id: str):
        if entity_id is not None:
            if len(entity_id) > 1:
                self.letter = WikidataNamespaceLetters[entity_id[0]]
                self.number = int(entity_id[1:])
            else:
                raise Exception("Entity ID was too short.")
        else:
            raise Exception("Entity ID was None")

    def to_string(self):
        return f"{self.letter}{self.number}"

    def extract_wdqs_json_entity_id(self, json: Dict, sparql_variable: str):
        self.__init__(json[sparql_variable]["value"].replace(
            config.wd_prefix, ""
        ))


class ForeignID:
    id: str
    property: str  # This is the property with type ExternalId
    source_item_id: str  # This is the Q-item for the source

    def __init__(self,
                 id: str = None,
                 property: str = None,
                 source_item_id: str = None):
        self.id = id
        self.property = EntityID(property).to_string()
        self.source_item_id = EntityID(source_item_id).to_string()


class Form:
    pass


class Sense:
    pass


class Lexeme:
    id: str
    lemma: str
    lexical_category: EntityID
    forms: List[Form]
    senses: List[Sense]

    def __init__(self,
                 id: str = None,
                 lemma: str = None,
                 lexical_category: str = None):
        self.id = EntityID(id).to_string()
        self.lemma = lemma
        self.lexical_category = EntityID(lexical_category)

    def parse_from_wdqs_json(self, json):
        self.forms = []
        self.senses = []
        for variable in json:
            logging.debug(variable)
            if variable == "form":
                form = Form(variable)
                self.forms.append(form)
            if variable == "sense":
                sense = Sense(variable)
                self.senses.append(sense)
            if variable == "category":
                self.lexical_category = EntityID(wdqs.extract_wikibase_value(variable))


    def url(self):
        return f"{config.wd_prefix}{self.id}"

    def upload_foreign_id_to_wikidata(self,
                                      foreign_id: ForeignID = None):
        """Upload to enrich the wonderful Wikidata <3"""
        logger = logging.getLogger(__name__)
        if foreign_id is None:
            raise Exception("Foreign id was None")
        print(f"Uploading {foreign_id.id} to {self.id}: {self.lemma}")
        statement = wbi_datatype.ExternalID(
            prop_nr=foreign_id.property,
            value=foreign_id.id,
        )
        described_by_source = wbi_datatype.ItemID(
            prop_nr="P1343",  # stated in
            value=foreign_id.source_item_id
        )
        # TODO does this overwrite or append?
        item = wbi_core.ItemEngine(
            data=[statement,
                  described_by_source],
            item_id=self.id
        )
        # debug WBI error
        # print(item.get_json_representation())
        result = item.write(
            config.login_instance,
            edit_summary=f"Added foreign identifier with [[{config.tool_url}]]"
        )
        logger.debug(f"result from WBI:{result}")
        print(self.url())
        # exit(0)

    def count_number_of_senses_with_P5137(self):
        """Returns an int"""
        result = (execute_sparql_query(f'''
        SELECT
        (COUNT(?sense) as ?count)
        WHERE {{
          VALUES ?l {{wd:{self.id}}}.
          ?l ontolex:sense ?sense.
          ?sense skos:definition ?gloss.
          # Exclude lexemes without a linked QID from at least one sense
          ?sense wdt:P5137 [].
        }}'''))
        count: int = wdqs.extract_count(result)
        logging.debug(f"count:{count}")
        return count


class LexemeEngine:
    lexemes: List[Lexeme]
    language_code: WikimediaLanguageCode
    language_qid: WikimediaLanguageQID

    def __init__(self, language_code: str):
        self.language_code = WikimediaLanguageCode(language_code)
        self.language_qid = WikimediaLanguageQID[self.language_code.name]

    def fetch_lexemes(self):
        # TODO port to use the Lexeme class instead of heavy dataframes which we don't need
        results = execute_sparql_query(f'''
        SELECT DISTINCT
        ?entity_lid ?form ?word (?categoryLabel as ?category) (?grammatical_featureLabel as ?feature) ?sense ?gloss
        WHERE {{
          ?entity_lid a ontolex:LexicalEntry; dct:language wd:{self.language_qid.value}.
          VALUES ?excluded {{
            # exclude affixes and interfix
            wd:Q62155 # affix
            wd:Q134830 # prefix
            wd:Q102047 # suffix
            wd:Q1153504 # interfix
          }}
          MINUS {{?entity_lid wdt:P31 ?excluded.}}
          ?entity_lid wikibase:lexicalCategory ?category.

          # We want only lexemes with both forms and at least one sense
          ?entity_lid ontolex:lexicalForm ?form.
          ?entity_lid ontolex:sense ?sense.

          # Exclude lexemes without a linked QID from at least one sense
          ?sense wdt:P5137 [].
          ?sense skos:definition ?gloss.
          # Get only the swedish gloss, exclude otherwise
          FILTER(LANG(?gloss) = "{self.language_code.value}")

          # This remove all lexemes with at least one example which is not
          # ideal
          MINUS {{?entity_lid wdt:P5831 ?example.}}
          ?form wikibase:grammaticalFeature ?grammatical_feature.
          # We extract the word of the form
          ?form ontolex:representation ?word.
          SERVICE wikibase:label
          {{ bd:serviceParam wikibase:language "{self.language_code.value},en". }}
        }}
        limit {config.sparql_results_size}
        offset {config.sparql_offset}
        ''')
        self.lexemes = []
        for lexeme_json in results:
            logging.debug(f"lexeme_json:{lexeme_json}")
            l = Lexeme.parse_wdqs_json(lexeme_json)
            self.lexemes.append(l)
        logging.info(f"Got {len(self.lexemes)} lexemes from WDQS for language {self.language_code.name}")

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

    def count_number_of_senses_with_P5137(self):
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
        return count
