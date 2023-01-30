import logging
import time
from typing import List, Optional, Union

from pydantic import BaseModel

import config
from lexutils.enums import ReturnValue, SupportedExampleSources, SupportedFormPickles
from lexutils.exceptions import MissingInformationError
from lexutils.helpers import tui, util
from lexutils.helpers.console import console
from lexutils.helpers.handle_pickles import add_to_pickle
from lexutils.models.historical_ads.historical_job_ads_record import HistoricalJobAd
from lexutils.models.lexemes import Lexemes
from lexutils.models.record import Record
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.lexutils_form import LexutilsForm
from lexutils.models.wikidata.lexutils_sense import LexutilsSense

logger = logging.getLogger(__name__)


class UsageExamples(BaseModel):
    """This is an abstract class that has 2 subclasses:
    APIUsageExamples and DataframeUsageExamples"""

    form: Optional[LexutilsForm] = None
    lexemes: Optional[Lexemes] = None
    records: List[Record] = []
    # usage_examples: List[UsageExample] = []
    number_of_presented_usage_examples: int = 0
    testing: bool = False

    class Config:
        arbitrary_types_allowed = True

    @property
    def number_of_usage_examples(self):
        if not self.form:
            raise MissingInformationError()
        return len(self.form.usage_examples)

    def number_of_found_sentences(self):
        print(
            "Found {} suitable sentences for {} with id "
            "{} and the grammatical features: {}".format(
                self.number_of_usage_examples,
                self.form.localized_representation,
                self.form.id,
                " ".join(self.form.grammatical_features),
            )
        )

    def __found_sentence__(self, usage_example: UsageExample):
        # FIXME add grammatical features here
        if not self.form:
            raise MissingInformationError()
        return (
            f"Found the following sentence with {usage_example.number_of_words} "
            + "words. Is it suitable as a usage example "
            + f"for the {self.form.lexeme_category} form '{self.form.localized_representation}'? \n"
            + f"'{usage_example.text}'"
        )

    def __process_usage_examples__(
        self,
    ) -> Optional[ReturnValue]:
        """Go through each usage example and present it"""
        if not self.form:
            raise MissingInformationError()
        if not self.form.usage_examples:
            raise MissingInformationError()
        # Sort so that the shortest sentence is first
        # Sort the usage examples by word count
        # https://stackoverflow.com/questions/403421/how-to-sort-a-list-of-objects-based-on-an-attribute-of-the-objects
        self.__sort_usage_examples_()
        tui.print_separator()
        print(self.form.presentation)
        # Loop through usage examples
        for example in self.form.usage_examples:
            self.__present_sentence__(
                example=example,
            )
            result: ReturnValue = self.__handle_usage_example__(usage_example=example)
            logger.info(f"process_result: result: {result}")
            self.number_of_presented_usage_examples += 1
            if result == ReturnValue.SKIP_USAGE_EXAMPLE:
                continue
            elif (
                result == ReturnValue.SKIP_FORM
                or result == ReturnValue.USAGE_EXAMPLE_ADDED
            ):
                # please mypy
                return result
        return None

    def fetch_and_present_usage_examples(self):
        """This method is the entry for the TUI"""
        # disabled for now
        # begin = introduction()
        begin = True
        if begin:
            choosen_language: WikimediaLanguageCode = tui.select_language_menu()
            # TODO store lexuse_introduction_read=True to e.g. settings.pkl
            with console.status(
                f"Fetching {config.number_of_forms_to_fetch} "
                f"lexeme forms to work on for "
                f"{choosen_language.name.title()}"
            ):
                self.lexemes = Lexemes(lang=choosen_language.value)
                self.lexemes.__convert_str_to_enums__()
                self.lexemes.fetch_forms_without_an_example()
            console.print(
                f"Fetching usage examples to work on. " f"This might take some minutes."
            )
            start = time.time()
            self.lexemes.fetch_usage_examples()
            end = time.time()
            total_number_of_examples = sum(
                [
                    form.number_of_examples_found
                    for form in self.lexemes.forms_with_usage_examples_found
                ]
            )
            if total_number_of_examples == 0:
                console.print("Found no usage examples for any of the forms.")
            else:
                console.print(
                    f"Found {total_number_of_examples} "
                    f"usage examples for a total of "
                    f"{len(self.lexemes.forms_with_usage_examples_found)} forms "
                    f"in {round(end - start)} seconds"
                )
            if len(self.lexemes.forms_with_usage_examples_found) > 0:
                for form in self.lexemes.forms_with_usage_examples_found:
                    form.lexemes = self.lexemes
                    result = self.__process_usage_examples__()
                    # Save the results to persistent memory
                    if result == ReturnValue.SKIP_FORM:
                        add_to_pickle(
                            pickle=SupportedFormPickles.DECLINED_FORMS,
                            form_id=form.id_,
                        )
                        continue
                    if result == ReturnValue.USAGE_EXAMPLE_ADDED:
                        add_to_pickle(
                            pickle=SupportedFormPickles.FINISHED_FORMS,
                            form_id=form.id_,
                        )
                tui.print_run_again_text()

    def __handle_usage_example__(
        self, usage_example: UsageExample = None
    ) -> Union[ReturnValue, LexutilsSense]:
        """This function presents the usage example sentence and
        ask the user to choose a sense that fits if any"""
        if not self.form:
            raise MissingInformationError()
        if usage_example is None:
            raise ValueError("usage_example was None")
        result: ReturnValue = util.yes_no_skip_question(
            self.__found_sentence__(usage_example=usage_example)
        )
        if result is ReturnValue.ACCEPT_USAGE_EXAMPLE:
            # The sentence was accepted
            # form.fetch_senses(usage_example=usage_example)
            if len(self.form.senses) == 0:
                return ReturnValue.SKIP_USAGE_EXAMPLE
            else:
                for sense in self.form.senses:
                    logging.info(sense)
                # raise NotImplementedError("Update to OOP")
                handler_result = self.__choose_sense_handler__(
                    usage_example=usage_example
                )
                return handler_result
        else:
            # Return the choice
            return result

    def __choose_sense_handler__(
        self, usage_example: UsageExample = None
    ) -> Union[ReturnValue, ReturnValue]:
        """Helper to choose a suitable sense for
        the example in question"""
        if not self.form:
            raise MissingInformationError()
        if usage_example is None:
            raise ValueError("usage_example was None")
        number_of_senses = len(self.form.senses)
        logging.info(f"number_of_senses:{number_of_senses}")
        if number_of_senses == 0:
            raise ValueError(
                "Error. Zero senses. this should never be reached "
                + "if the SPARQL result was sane"
            )
        elif number_of_senses == 1:
            sense_choice = self.__prompt_single_sense__()
        else:
            sense_choice = self.__prompt_multiple_senses__()
        # sense_choice: Union[Sense, ReturnValues] = sense_approval_handler(
        #     usage_example=usage_example,
        #     senses=senses,
        #     form=form
        # )
        if isinstance(sense_choice, LexutilsSense):
            logger.info("We got a sense that was accepted")
            if not self.form.lexeme:
                raise MissingInformationError()
            # Prepare
            # if isinstance(usage_example.record, RiksdagenRecord):
            #     usage_example.record.lookup_qid()
            #     if usage_example.record.document_qid is None:
            #         # TODO lookup publication date via the Riksdagen API
            #         # lookup using id
            #         rd = Riksdagen()
            #         dokumentlista: Dokumentlista = rd.lookup_document_metadata_by_id(
            #             usage_example.record.id
            #         )
            #         if dokumentlista:
            #             if len(dokumentlista.dokument) > 0:
            #                 # pick first and hope for the best
            #                 first: Dokument = dokumentlista.dokument[0]
            #                 date = first.date
            #                 logger.info(f"Found Riksdagen date: {date}")
            #                 usage_example.record.date = date
            #             else:
            #                 raise ValueError(
            #                     f"Found no documents with the id "
            #                     f"'{usage_example.record.id}' in the Riksdagen API"
            #                 )
            #         else:
            #             raise ValueError(
            #                 "Could not lookup publication date via the Riksdagen API"
            #             )
            sense = sense_choice
            if usage_example.record.source == SupportedExampleSources.RIKSDAGEN:
                logger.info("Looking up the QID for the source document")
                usage_example.record.lookup_qid()
            # Add
            result = self.form.add_usage_example(
                sense=sense, usage_example=usage_example
            )
            if result is not None:
                logger.info(f"wbi:{sense_choice}")
                print(
                    "Successfully added usage example "
                    + f"{self.form.lexeme.usage_example_url()}"
                )
                # logger.info("debug exit")
                # exit(0)
                # json_cache.save_to_exclude_list(usage_example)
                return ReturnValue.USAGE_EXAMPLE_ADDED
            else:
                # No result from WBI, what does that mean?
                raise Exception("Error. WBI returned None.")
        else:
            # Pass on return value
            return sense_choice

    def __prompt_single_sense__(self) -> Union[ReturnValue, LexutilsSense]:
        if not self.form:
            raise MissingInformationError()
        # TODO add fallback glosses
        if config.show_sense_urls:
            question = (
                "Found only one sense. "
                + "Does this example fit the following "
                + f"gloss?\n{self.form.senses[0].url()}\n'{self.form.senses[0].localized_gloss}'"
            )
        else:
            question = (
                "Found only one sense. "
                + "Does this example fit the following "
                + f"gloss?\n'{self.form.senses[0].localized_gloss}'"
            )
        if util.yes_no_question(question):
            sense: LexutilsSense = self.form.senses[0]
            return sense
        else:
            self.form.print_cancel_sentence_text()
            time.sleep(config.sleep_time)
            return ReturnValue.SKIP_USAGE_EXAMPLE

    def __prompt_multiple_senses__(self) -> Union[ReturnValue, LexutilsSense]:
        """Prompt and enable user to choose between multiple senses"""
        if not self.form:
            raise MissingInformationError()
        if not self.form.lexeme:
            raise MissingInformationError()
        print(f"Found {self.form.number_of_senses} senses.")
        # TODO check that all senses has a gloss matching the language of
        # the example
        chosen_sense: Union[LexutilsSense, None] = self.form.lexeme.choose_sense_menu()
        if chosen_sense is not None:
            logging.info("a sense was accepted")
            return chosen_sense
        else:
            self.form.print_cancel_sentence_text()
            time.sleep(config.sleep_time)
            return ReturnValue.SKIP_USAGE_EXAMPLE

    def __present_sentence__(self, example: UsageExample = None):
        """We present a sentence and count of how many we have presented until now."""
        if example is None:
            raise ValueError("example was None")
        if example.record is None:
            raise ValueError("record was None")
        # if isinstance(example.record, RiksdagenRecord):
        #     console.print(
        #         (
        #             "Presenting sentence "
        #             + f"{count}/{form.number_of_examples_found} "
        #             + "from {} from {}".format(
        #                 example.record.date,
        #                 example.record.human_readable_url(),
        #             )
        #         )
        #     )
        if isinstance(example.record, HistoricalJobAd):
            console.print(
                "Presenting sentence "
                + f"{self.number_of_presented_usage_examples}/{self.number_of_usage_examples} "
                + "with id {} from {}".format(
                    example.record.id,
                    example.record.url,
                )
            )
        else:
            console.print(
                "Presenting sentence "
                + f"{self.number_of_presented_usage_examples}/{self.number_of_usage_examples} "
                + "from {}".format(
                    example.record.human_readable_url(),
                )
            )

    def __sort_usage_examples_(self):
        self.form.usage_examples.sort(key=lambda x: x.word_count, reverse=False)
