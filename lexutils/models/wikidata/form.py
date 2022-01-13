import logging
from time import sleep
from typing import List, Optional

from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.models import LanguageValue
from wikibaseintegrator.wbi_helpers import execute_sparql_query
from wikibaseintegrator.entities import Item

from lexutils.config import config
from lexutils.config.config import login_instance
from lexutils.helpers import tui
from lexutils.helpers.caching import read_from_cache, add_to_cache
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.entities import EntityID
from lexutils.models.wikidata.sense import Sense


class Form:
    """
    Model for a Wikibase form
    """
    id: str
    representation: str
    grammatical_features: List[str]
    # We store these on the form because they are needed
    # to determine if an example fits or not
    lexeme_id: str
    lexeme_category: str = None
    senses: List[Sense] = None

    def __init__(self, json):
        """Parse the form json"""
        logger = logging.getLogger(__name__)
        try:
            logger.debug(json["lexeme"])
            self.lexeme_id = str(EntityID(json["lexeme"]["value"]))
        except KeyError:
            pass
        try:
            logger.debug(json["form"])
            self.id = str(EntityID(json["form"]["value"]))
        except KeyError:
            pass
        try:
            self.representation: str = json["form_representation"]["value"]
        except KeyError:
            pass
        try:
            qid = str(EntityID(json["category"]["value"]))
            label = read_from_cache(qid=qid)
            logger.debug(f"got {label} from the cache")
            if label is None:
                wbi = WikibaseIntegrator(login=login_instance)
                item = wbi.item.get(entity_id=qid)
                # TODO get the language code from somewhere
                # label = item.labels.get(language=)
                # English is fallback
                label = item.labels.get(language="en")
                logger.debug(f"fetched feature not found in the cache: {label.value}")
                add_to_cache(qid=qid, label=label.value)
            if isinstance(label, LanguageValue):
                self.lexeme_category = label.value
            else:
                self.lexeme_category = label
            #print("debug exit")
            #exit()
        except ValueError:
            logger.error(f'Could not find lexical category from '
                             f'{json["category"]["value"]}')
        try:
            self.grammatical_features = []
            logger.debug(json["grammatical_features"])
            for feature in json["grammatical_features"]["value"].split(","):
                qid = str(EntityID(feature))
                label: Optional[str] = read_from_cache(qid=qid)
                logger.debug(f"got {label} from the cache")
                if label is None:
                    wbi = WikibaseIntegrator(login=login_instance)
                    item = wbi.item.get(entity_id=qid)
                    # TODO get the language code from somewhere
                    # label = item.labels.get(language=)
                    # English is fallback
                    label: LanguageValue = item.labels.get(language="en")
                    logger.debug(f"fetched feature not found in the cache: {label.value}")
                    add_to_cache(qid=qid, label=label.value)
                if isinstance(label, LanguageValue):
                    self.grammatical_features.append(label.value)
                else:
                    self.grammatical_features.append(label)
        except KeyError:
            pass

    def __str__(self):
        return f"{self.id}/{self.lexeme_id}/{self.representation}"

    def fetch_senses(self,
                     usage_example: UsageExample = None):
        """Fetch the senses on the lexeme"""
        def sparql_query(fallback: bool = False):
            if fallback == True:
                # Fall back to English as gloss language
                return execute_sparql_query(
                    f'''
                        SELECT
                        ?sense ?gloss
                        WHERE {{
                          VALUES ?l {{wd:{self.lexeme_id}}}.
                          ?l ontolex:sense ?sense.
                          ?sense skos:definition ?gloss.
                          # Get only the swedish gloss, exclude otherwise
                          FILTER(LANG(?gloss) = "en")
                          # Exclude lexemes without a linked QID from at least one sense
                          # ?sense wdt:P5137 [].
                        }}'''
                    # debug=True
                )
            else:
                return execute_sparql_query(
                    f'''
                        SELECT
                        ?sense ?gloss
                        WHERE {{
                          VALUES ?l {{wd:{self.lexeme_id}}}.
                          ?l ontolex:sense ?sense.
                          ?sense skos:definition ?gloss.
                          # Get only the swedish gloss, exclude otherwise
                          FILTER(LANG(?gloss) = "{usage_example.record.language_code.value}")
                          # Exclude lexemes without a linked QID from at least one sense
                          # ?sense wdt:P5137 [].
                        }}'''
                    # debug=True
                )

        def extract_and_convert_the_result_to_senses(result):
            rows = result["results"]["bindings"]
            number_of_rows = len(rows)
            if number_of_rows > 0:
                for row in rows:
                    logger.debug(f"row:{row}")
                    self.senses.append(
                        Sense(
                            id=row["sense"]["value"],
                            gloss=row["gloss"]["value"]
                        ))
                logging.debug(f"senses found:{self.senses}")

        logger = logging.getLogger(__name__)
        if usage_example is None:
            raise ValueError("usage_example was None")
        # Thanks to Lucas Werkmeister https://www.wikidata.org/wiki/Q57387675 for
        # helping with this query.
        tui.fetching_senses()
        logging.info(f"...from {self.lexeme_id}")
        result = sparql_query()
        self.senses = []
        # TODO Move this into the model
        if result is not None:
            extract_and_convert_the_result_to_senses(result)
            if len(self.senses) == 0:
                logger.warning(f"No senses with a gloss in the  "
                               f"{usage_example.record.language_code.name.title()} was found. "
                               f"Please go to {self.url()} and improve the glosses if you can. "
                               f"Falling back to English as gloss language.")
                result = sparql_query(fallback=True)
                if result is not None:
                    extract_and_convert_the_result_to_senses(result)
                    if len(self.senses) == 0:
                        logger.warning(f"No senses with a gloss in the fallback language English "
                                       f" was found. "
                                       f"Please go to {self.url()} and improve the glosses if you can.")
        else:
            raise ValueError(_("Error. Got None trying to fetch senses. " +
                               "Please report this as an issue."))

    def url(self):
        return f"{config.wd_prefix}{self.id}"
