import logging
import time
from typing import Any, Union

from pydantic import BaseModel, validate_arguments

import config
from lexutils.enums import ReturnValue, SupportedExampleSources
from lexutils.exceptions import MissingInformationError
from lexutils.helpers import util
from lexutils.helpers.console import console
from lexutils.models.record.historical_job_ads import HistoricalJobAd
from lexutils.models.wikidata.lexutils_form import LexutilsForm
from lexutils.models.wikidata.lexutils_sense import LexutilsSense

logger = logging.getLogger(__name__)


class UsageExample(BaseModel):
    """This models the example, the data we need is in the
    attributes form and record"""

    form: LexutilsForm
    record: Any

    class Config:
        arbitrary_types_allowed = True
        extra = "forbid"

    def __str__(self):
        from lexutils.models.record import Record

        if not isinstance(self.record, Record):
            raise ValueError()
        return f"{self.record.text} (from {self.record.id} at {self.record.source.name.title()})"

    @property
    def number_of_words(self):
        # from https://www.pythonpool.com/python-count-words-in-string/
        return self.record.number_of_words

    def __found_sentence_text__(self):
        # FIXME add grammatical features here
        return (
            f"Found the following sentence with {self.number_of_words} "
            + "words. Is it suitable as a usage example "
            + f"for the {self.form.localized_lexeme_category} form '{self.form.localized_representation}'? \n"
            + f"'{self.record.text}'"
        )

    def __validate_usage_example__(self) -> Union[ReturnValue, LexutilsSense]:
        """This function presents the usage example sentence and
        ask the user to choose a sense that fits if any"""
        logger.debug("__validate_usage_example__: running")
        result: ReturnValue = util.yes_no_skip_question(self.__found_sentence_text__)
        if result is ReturnValue.ACCEPT_USAGE_EXAMPLE:
            # The sentence was accepted
            # form.fetch_senses(usage_example=usage_example)
            if len(self.form.senses) == 0:
                return ReturnValue.SKIP_USAGE_EXAMPLE
            else:
                for sense in self.form.senses:
                    logger.info(sense)
                # raise NotImplementedError("Update to OOP")
                handler_result = self.__choose_sense_handler__()
                return handler_result
        else:
            # Return the choice
            return result

    @property
    def number_of_senses(self):
        return self.form.number_of_senses

    def __choose_sense_handler__(self) -> Union[ReturnValue, ReturnValue]:
        """Helper to choose a suitable sense for
        the example in question"""
        logging.info(f"number_of_senses:{self.number_of_senses}")
        if self.number_of_senses == 0:
            raise ValueError(
                "Error. Zero senses. this should never be reached "
                + "if the SPARQL result was sane"
            )
        elif self.number_of_senses == 1:
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
            if self.record.source == SupportedExampleSources.RIKSDAGEN:
                logger.info("Looking up the QID for the source document")
                self.record.lookup_qid()
            # Add
            result = self.form.add_usage_example(sense=sense, usage_example=self)
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

    @validate_arguments
    def __present_sentence__(
        self, number_of_presented_usage_examples: int, number_of_usage_examples: int
    ):
        """We present a sentence and count of how many we have presented until now."""
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
        if isinstance(self.record, HistoricalJobAd):
            console.print(
                "Presenting sentence "
                + f"{number_of_presented_usage_examples}/{number_of_usage_examples} "
                + "with id {} from {}".format(
                    self.record.id,
                    self.record.url,
                )
            )
        # else:
        #     console.print(
        #         "Presenting sentence "
        #         + f"{number_of_presented_usage_examples}/{number_of_usage_examples} "
        #         + "from {}".format(
        #             self.record.url,
        #         )
        #     )
