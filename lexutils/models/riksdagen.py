from __future__ import annotations
import logging
from datetime import datetime
import re
from typing import List, TYPE_CHECKING

import langdetect
from langdetect import LangDetectException
from wikibaseintegrator.wbi_helpers import execute_sparql_query

from lexutils.config import config
from lexutils.config.enums import SupportedExampleSources, LanguageStyle, ReferenceType
from lexutils.models.lexemes import Lexemes
from lexutils.models.usage_example import UsageExample
from lexutils.models.record import Record
from lexutils.helpers import util
from lexutils.helpers.wdqs import extract_the_first_wikibase_value_from_a_wdqs_result_set

if TYPE_CHECKING:
    from lexutils.models.wikidata.form import Form


class RiksdagenRecord(Record):
    base_url = "https://data.riksdagen.se/dokument/"
    language_style = LanguageStyle.FORMAL
    type_of_reference = ReferenceType.WRITTEN
    source = SupportedExampleSources.RIKSDAGEN
    swedish_text: bool = False

    def __init__(self,
                 json,
                 lexemes: Lexemes = None):
        try:
            self.id = json["id"]
        except KeyError:
            raise KeyError("Could not find id")
        try:
            self.text = json["summary"]
            self.detect_if_swedish_or_not()
        except KeyError:
            raise KeyError("Could not find summary")
        try:
            # self.date = datetime.strptime(json["datum"], "%d%m%Y")
            self.date = datetime.strptime(json["datum"][0:10], "%Y-%m-%d")
        except KeyError:
            raise KeyError("Could not find datum")
        self.language_code = lexemes.language_code

    def detect_if_swedish_or_not(self):
        """Use langdetect to detect if we got a swedish record"""
        logger = logging.getLogger(__name__)
        try:
            if langdetect.detect(self.text) == "sv":
                logger.debug("Swedish record detected")
                self.swedish_text = True
            else:
                logger.debug("Non-Swedish record detected")
        except LangDetectException:
            logger.error(f"Could not detect language of {self.text}")

    def find_form_representation_in_the_text(self, word):
        logger = logging.getLogger(__name__)
        if word in self.text:
            inexact_hit = True
            if f" {word} " in self.text or f">{word}<" in self.text:
                self.exact_hit = True
                if config.debug_summaries:
                    logging.debug(
                        f"found word_spaces or word_angle_parens in {self.text}"
                    )
            else:
                if config.debug_summaries:
                    logging.info("No exact hit in text. Skipping.")
        # else:
        #     if config.debug_summaries and added is False:
        #         print(f"'{word}' not found as part of a word or a " +
        #               "word in the text. Skipping")

    def find_usage_examples_from_summary(self, form: Form) -> List[UsageExample]:
        """This tries to find and clean sentences and return the shortest one"""
        # TODO use NLP
        substitutions = dict(
            xxx="t.ex.",
            yyy="m.m.",
            zzz="dvs.",
            qqq="bl.a.",
            wwww="ang.",
            eeee="kl.",
            aaaa="s.k.",
            bbbb="resp.",
            cccc="prop.",
            dddd="skr.",
        )

        def clean_text(text):
            """This cleans the html formatting that the API adds automatically.
            It cannot be turned of == bad API design"""
            return text.replace(
                '<span class="traff-markering">', ""
            ).replace('</span>', "")

        def substitute_common_abbreviations(cleaned_text):
            # replace abbreviations "t.ex." temporarily to help detect sentence boundaries
            for key in substitutions:
                cleaned_text = cleaned_text.replace(
                    substitutions[key], key,
                )
            return cleaned_text

        def remove_duplicates(cleaned_text):
            # from https://stackoverflow.com/questions/3549075/
            # regex-to-find-all-sentences-of-text
            # TODO check for near duplicates and remove (fuzzymatch?)
            # TODO flesh out regex sentence detecting to own module
            sentences = re.findall(
                "[A-Z].*?[\.!?]", cleaned_text, re.MULTILINE | re.DOTALL
            )
            # Remove duplicates naively using sets
            return list(set(sentences))

        def find_suitable_usage_examples(sentences_without_duplicates,
                                         cleaned_text, form: Form):
            # FIXME refactor for increased readability
            usage_examples = []
            sentences = set()
            for sentence in sentences_without_duplicates:
                """For each sentence we first try to exclude it, 
                then look for a match"""
                exclude_this_sentence = False
                #########################################
                # Exclude
                #########################################
                # Exclude based on length of the sentence
                word_count = util.count_words(sentence)
                if (
                        word_count > config.max_word_count or
                        word_count < config.min_word_count
                ):
                    exclude_this_sentence = True
                    # Exclude by breaking out of the iteration early
                    break
                else:
                    # Exclude based on weird words that are very rarely suitable sentences
                    excluded_words = [
                        # "SAMMANFATTNING",
                        # "BETÄNKANDE",
                        # "UTSKOTT",
                        # "MOTION",
                        # " EG ",
                        # " EU ",
                        # "RIKSDAGEN",
                    ]
                    for excluded_word in excluded_words:
                        result = sentence.upper().find(excluded_word)
                        if result != -1:
                            if config.debug_summaries:
                                sentence = sentence.replace("\n", "")
                                # .replace("-", "")
                                # .replace(ellipsis, ""))
                                logging.debug(
                                    f"Found excluded word {excluded_word} " +
                                    f"in {sentence}. Skipping",
                                )
                            exclude_this_sentence = True
                            break
                ####################################################
                # Find sentences with a match
                ####################################################
                # Add spaces to match better
                if sentence.find(f" {form.representation} ") != -1 and exclude_this_sentence is False:
                    # restore the abbreviations
                    # TODO does this do anything?
                    for key in substitutions:
                        cleaned_text = cleaned_text.replace(key, substitutions[key])
                    # Last cleaning
                    ellipsis: str = "…"
                    sentence = (sentence
                                .replace("\n", "")
                                # This removes "- " because the data is hyphenated
                                # sometimes
                                .replace("- ", "")
                                .replace(ellipsis, "")
                                .replace("  ", " "))
                    logging.debug(f"suitable_sentence:{sentence}")
                    sentences.add(sentence)
            for sentence in sentences:
                # Append an Example object
                usage_examples.append(UsageExample(sentence=sentence, record=self))
            return usage_examples

        logger = logging.getLogger(__name__)
        cleaned_text = clean_text(self.text)
        sentences_without_duplicates = remove_duplicates(
            substitute_common_abbreviations(cleaned_text)
        )
        # logger.debug("Sentences after duplicate removal " +
        #              f"{sentences_without_duplicates}")
        return find_suitable_usage_examples(sentences_without_duplicates, cleaned_text, form)

    def lookup_qid(self):
        # Given a docuemnt id lookup the QID if any
        result = execute_sparql_query(
            f"""
            SELECT ?item
            WHERE 
            {{
              ?item wdt:P8433 "{self.id}".
            }}
            """
        )
        logging.info(f"result:{result}")
        self.document_qid = extract_the_first_wikibase_value_from_a_wdqs_result_set(result, "item")
        logging.info(f"document_qid:{self.document_qid}")
