from __future__ import annotations
import logging
from datetime import datetime
import re
from typing import List, TYPE_CHECKING

from wikibaseintegrator.wbi_helpers import execute_sparql_query

from lexutils.config.enums import SupportedExampleSources, LanguageStyle, ReferenceType
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

    def __init__(self, json):
        try:
            self.id = json["id"]
        except KeyError:
            raise KeyError("Could not find id")
        try:
            self.summary = json["summary"]
        except KeyError:
            raise KeyError("Could not find id")
        try:
            # self.date = datetime.strptime(json["datum"], "%d%m%Y")
            self.date = datetime.strptime(json["datum"][0:10], "%Y-%m-%d")
        except KeyError:
            raise KeyError("Could not find id")

    def find_form_representation_in_summary(self, word):
        logger = logging.getLogger(__name__)
        if word in self.summary:
            inexact_hit = True
            if f" {word} " in self.summary or f">{word}<" in self.summary:
                self.exact_hit = True
                if debug_summaries:
                    logging.debug(
                        f"found word_spaces or word_angle_parens in {self.summary}"
                    )
            else:
                if debug_summaries:
                    logging.info("No exact hit in summary. Skipping.")
        # else:
        #     if config.debug_summaries and added is False:
        #         print(f"'{word}' not found as part of a word or a " +
        #               "word in the summary. Skipping")

    def find_usage_examples_from_summary(self, form: Form) -> List[UsageExample]:
        """This tries to find and clean sentences and return the shortest one"""
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

        def clean_summary(summary):
            return summary.replace(
                '<span class="traff-markering">', ""
            ).replace('</span>', "")

        def substitute_common_abbreviations(cleaned_summary):
            # replace abbreviations "t.ex." temporarily to help detect sentence boundaries
            for key in substitutions:
                cleaned_summary = cleaned_summary.replace(
                    substitutions[key], key,
                )
            return cleaned_summary

        def remove_duplicates(cleaned_summary):
            # from https://stackoverflow.com/questions/3549075/
            # regex-to-find-all-sentences-of-text
            # TODO check for near duplicates and remove (fuzzymatch?)
            # TODO flesh out regex sentence detecting to own module
            sentences = re.findall(
                "[A-Z].*?[\.!?]", cleaned_summary, re.MULTILINE | re.DOTALL
            )
            # Remove duplicates naively using sets
            return list(set(sentences))

        def find_suitable_usage_examples(sentences_without_duplicates,
                                    cleaned_summary, form: Form):
            usage_examples = []
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
                        word_count > max_word_count or
                        word_count < min_word_count
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
                            if debug_excludes:
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
                if f" {form.representation} " in sentence and exclude_this_sentence is False:
                    # restore the abbreviations
                    for key in substitutions:
                        cleaned_summary = cleaned_summary.replace(key, substitutions[key])
                    # Last cleaning
                    ellipsis: str = "…"
                    sentence = (sentence
                                .replace("\n", "")
                                # This removes "- " because the data is hyphenated
                                # sometimes
                                .replace("- ", "")
                                .replace(ellipsis, "")
                                .replace("  ", " "))
                    if debug_sentences:
                        logging.debug(f"suitable_sentence:{sentence}")
                    # Append an Example object
                    usage_examples.append(UsageExample(sentence, self))
            return usage_examples

        logger = logging.getLogger(__name__)
        cleaned_summary = clean_summary(self.summary)
        sentences_without_duplicates = remove_duplicates(
            substitute_common_abbreviations(cleaned_summary)
        )
        if debug_duplicates:
            print("Sentences after duplicate removal " +
                  f"{sentences_without_duplicates}")
        return find_suitable_usage_examples(sentences_without_duplicates, cleaned_summary, form)

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