from typing import Dict, List

# We get the URL for the Wikibase from here
from lexutils import config


def extract_wikibase_value_from_result(json: Dict = None, sparql_variable: str = None) -> str:
    """Extract a value from a sparql-variable defined in SELECT"""
    if json is None:
        raise Exception("Missing json")
    if type(json) == List:
        raise Exception("The json was a list, expected a dict")
    if sparql_variable is None:
        raise Exception("Missing sparql variable to look for")
    return json["results"][sparql_variable]["value"].replace(
        config.wd_prefix, ""
    )


def extract_count(json: Dict) -> int:
    """Extract count from queries that only return a count-variable"""
    if "count" in json["head"]["vars"]:
        return int(json["results"]["bindings"][0]["count"]["value"])
    else:
        raise Exception(f"Count variable was not found among the variables. Got {json}")