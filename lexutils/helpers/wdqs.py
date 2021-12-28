import logging
from typing import Dict, List

# We get the URL for the Wikibase from here
from lexutils.config import config


def extract_the_first_wikibase_value_from_a_wdqs_result_set(json: Dict = None, sparql_variable: str = None) -> str:
    """Extract a value from a sparql-variable defined in SELECT"""
    logger = logging.getLogger(__name__)
    if json is None:
        raise Exception("Missing json")
    if type(json) == List:
        raise Exception("The json was a list, expected a dict")
    if sparql_variable is None:
        raise Exception("Missing sparql variable to look for")
    if len(json["results"]["bindings"]) > 0:
        # We pick only the first
        return json["results"]["bindings"][0][sparql_variable]["value"].replace(
            config.wd_prefix, ""
        )
    else:
        logger.info("No QID found for this record")

def extract_count(json: Dict) -> int:
    """Extract count from queries that only return a count-variable"""
    if "count" in json["head"]["vars"]:
        return int(json["results"]["bindings"][0]["count"]["value"])
    else:
        raise Exception(f"Count variable was not found among the variables. Got {json}")