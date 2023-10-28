#!/usr/bin/env python3
import logging

from lexutils.enums import ReturnValue

logger = logging.getLogger(__name__)


def yes_no_skip_question(message: str) -> ReturnValue:
    # https://www.quora.com/
    # I%E2%80%99m-new-to-Python-how-can-I-write-a-yes-no-question
    # this will loop forever
    while True:
        answer = input(f"{message} [(Y)es/(n)o/(s)kip this form]: ")
        if len(answer) == 0 or answer[0].lower() in ("y", "n", "s"):
            if len(answer) == 0:
                return ReturnValue.ACCEPT_USAGE_EXAMPLE
            elif answer[0].lower() == "s":
                return ReturnValue.SKIP_FORM
            else:
                # the == operator just returns a boolean,
                if answer[0].lower() == "y":
                    return ReturnValue.ACCEPT_USAGE_EXAMPLE
                else:
                    return ReturnValue.SKIP_USAGE_EXAMPLE


def yes_no_question(message: str):
    # https://www.quora.com/
    # I%E2%80%99m-new-to-Python-how-can-I-write-a-yes-no-question
    # this will loop forever
    while True:
        answer = input(f"{message} [Y/n]: ")
        if len(answer) == 0 or answer[0].lower() in ("y", "n"):
            if len(answer) == 0:
                return True
            else:
                # the == operator just returns a boolean,
                return answer[0].lower() == "y"


# async def async_fetch_from_url(url):
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#         return response


# def add_to_watchlist(lid: str):
#     """This add a lexeme to the users watchlist"""
#     # TODO use WBI for this instead
#     # Get session from WBI, it cannot be None because this comes after adding an
#     # usage example with WBI.
#     session = config.login_instance.get_session()
#     if session is None:
#         logging.error(("Error. Failed to add lexeme {lid} ".format(lid)+
#                         "to your watchlist. Please report an issue"))
#     # adapted from https://www.mediawiki.org/wiki/API:Watch
#     url = "https://www.wikidata.org/w/api.php"
#     params_token = {
#         "action": "query",
#         "meta": "tokens",
#         "type": "watch",
#         "format": "json"
#     }
#     result = session.get(url=url, params=params_token)
#     data = result.json()
#     csrf_token = data["query"]["tokens"]["watchtoken"]
#     params_watch = {
#         "action": "watch",
#         "titles": "Lexeme:" + lid,
#         "format": "json",
#         "formatversion": "2",
#         "token": csrf_token,
#     }
#     result = session.post(
#         url, data=params_watch
#     )
#     #logging.debug(result.text)
#     print(("Added {} to your watchlist".format(lid)))


# def in_exclude_list(data: dict):
#     # Check if in exclude_list
#     if os.path.isfile('exclude_list.json'):
#         if config.debug_exclude_list:
#             logging.debug("Looking up in exclude list")
#         # Read the file
#         with open('exclude_list.json', 'r', encoding='utf-8') as myfile:
#             json_data = myfile.read()
#             # parse file
#             exclude_list = json.loads(json_data)
#             lid = data["lid"]
#             for form_id in exclude_list:
#                 form_data = exclude_list[form_id]
#                 if config.debug_exclude_list:
#                     logging.debug(f"found:{form_data}")
#                 if (
#                         # TODO check the date also
#                         lid == form_id
#                         and config.language_code == form_data["lang"]
#                 ):
#                     logging.debug("Match found")
#                     return True
#         # Not found in exclude_list
#         return False
#     else:
#         # No exclude_list
#         return False
