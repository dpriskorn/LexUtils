import logging
from typing import List

from wikibaseintegrator.wbi_helpers import execute_sparql_query

from lexutils.config import config
from lexutils.helpers import tui
from lexutils.models.wikidata.entities import EntityID
from lexutils.models.wikidata.enums import WikidataGrammaticalFeature, WikidataLexicalCategory
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
    lexeme_category: WikidataLexicalCategory = None
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
            self.lexeme_category = WikidataLexicalCategory(
                str(EntityID(json["category"]["value"]))
            )
        except:
            raise ValueError(f'Could not find lexical category from '
                             f'{json["category"]["value"]}')
        try:
            self.grammatical_features = []
            logger.debug(json["grammatical_features"])
            for feature in json["grammatical_features"]["value"].split(","):
                # TODO look up labels of features using WD
                try:
                    feature_string = WikidataGrammaticalFeature(str(EntityID(feature))).name
                except ValueError:
                    logging.error(f"the grammatical feature {feature} was not recognized")
                    feature_string = feature
                self.grammatical_features.append(feature_string)
        except KeyError:
            pass

    def __str__(self):
        return f"{self.id}/{self.lexeme_id}/{self.representation}"

    def fetch_senses(self):
        """Fetch the senses on the lexeme"""
        logger = logging.getLogger(__name__)
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
          FILTER(LANG(?gloss) = "{config.language_code}")
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
                raise ValueError("number of senses was 0")
        else:
            raise ValueError(_("Error. Got None trying to fetch senses. " +
                               "Please report this as an issue."))

    def url(self):
        return f"{config.wd_prefix}{self.id}"
