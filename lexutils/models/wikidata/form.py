import logging
from time import sleep
from typing import List

from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.models import LanguageValue
from wikibaseintegrator.wbi_helpers import execute_sparql_query
from wikibaseintegrator.entities import Item

from lexutils.config import config
from lexutils.config.config import login_instance
from lexutils.helpers import tui
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.entities import EntityID
from lexutils.models.wikidata.sense import Sense


class Form:
    """
    Model for a Wikibase form
    """
    id: str
    representation: str
    grammatical_features: List[LanguageValue]
    # We store these on the form because they are needed
    # to determine if an example fits or not
    lexeme_id: str
    lexeme_category: LanguageValue = None
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
            wbi = WikibaseIntegrator(login=login_instance)
            item = wbi.item.get(entity_id=str(EntityID(json["category"]["value"])))
            # TODO get the language code from somewhere
            # label = item.labels.get(language=)
            # English is fallback
            label = item.labels.get(language="en")
            logger.info(f"found feature: {label.value}")
            self.lexeme_category = label
        except ValueError:
            logger.error(f'Could not find lexical category from '
                             f'{json["category"]["value"]}')
        try:
            self.grammatical_features = []
            logger.debug(json["grammatical_features"])
            for feature in json["grammatical_features"]["value"].split(","):
                wbi = WikibaseIntegrator(login=login_instance)
                item = wbi.item.get(entity_id=str(EntityID(feature)))
                # TODO get the language code from somewhere
                # label = item.labels.get(language=)
                # English is fallback
                label = item.labels.get(language="en")
                logger.info(f"found feature: {label.value}")
                # print("debug exit")
                # exit(0)
                self.grammatical_features.append(label)
        except KeyError:
            pass

    def __str__(self):
        return f"{self.id}/{self.lexeme_id}/{self.representation}"

    def fetch_senses(self,
                     usage_example: UsageExample = None):
        """Fetch the senses on the lexeme"""
        logger = logging.getLogger(__name__)
        if usage_example is None:
            raise ValueError("usage_example was None")
        # Thanks to Lucas Werkmeister https://www.wikidata.org/wiki/Q57387675 for
        # helping with this query.
        tui.fetching_senses()
        logging.info(f"...from {self.lexeme_id}")
        result = execute_sparql_query(
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
        self.senses = []
        number = 1
        # TODO Move this into the model
        if result is not None:
            # logger.debug(f"result:{result}")
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
                    number += 1
                logging.debug(f"senses found:{self.senses}")
            else:
                logger.warning(f"No senses with a gloss in the current language "
                               f"{usage_example.record.language_code.name.title()} was found. "
                               f"Please go to {self.url()} and improve the glosses if you can.")
                sleep(5)
        else:
            raise ValueError(_("Error. Got None trying to fetch senses. " +
                               "Please report this as an issue."))

    def url(self):
        return f"{config.wd_prefix}{self.id}"
