import logging
import time
from typing import Optional

import config
from lexutils.enums import ReturnValue, SupportedFormPickles
from lexutils.exceptions import MissingInformationError
from lexutils.helpers import tui
from lexutils.helpers.console import console
from lexutils.helpers.handle_pickles import add_to_pickle
from lexutils.models.lexemes import Lexemes
from lexutils.models.wikidata.enums import WikimediaLanguageCode

logger = logging.getLogger(__name__)


class UsageExamplesSession:
    """This models a session where we first chose a language
    then get random forms without examples and then search for usage examples.
    If any are found we present them
    If approved the example is uploaded"""

    # This holds the forms and lexemes they are linked to.
    lexemes: Optional[Lexemes] = None
    choosen_language: Optional[WikimediaLanguageCode]
    usage_example_fetch_duration: int = 0

    @property
    def total_number_of_examples(self):
        return sum(
            [
                form.number_of_usage_examples_found
                for form in self.lexemes.forms_with_possible_matching_usage_examples_found
            ]
        )

    def __fetch_forms__(self):
        if not self.choosen_language:
            raise MissingInformationError()
        with console.status(
            f"Fetching {config.number_of_forms_to_fetch} "
            f"lexeme forms to work on for "
            f"{self.choosen_language.name.title()}"
        ):
            self.lexemes = Lexemes(lang=self.choosen_language.value)
            self.lexemes.__convert_str_to_enums__()
            self.lexemes.fetch_forms_without_an_example()

    def __choose_language__(self):
        self.choosen_language: WikimediaLanguageCode = tui.select_language_menu()

    def __fetch_usage_examples__(self):
        console.print(
            f"Fetching usage examples to work on. " f"This might take some minutes."
        )
        start = time.time()
        self.lexemes.fetch_usage_examples()
        end = time.time()
        self.usage_example_fetch_duration = int(end - start)

    def __inform_user_about_examples_found__(self):
        if self.total_number_of_examples == 0:
            console.print("Found no usage examples for any of the forms.")
        else:
            console.print(
                f"Found {self.total_number_of_examples} "
                f"usage examples for a total of "
                f"{len(self.lexemes.forms_with_possible_matching_usage_examples_found)} forms "
                f"in {self.usage_example_fetch_duration} seconds"
            )

    def __iterate_forms_with_examples_found__(self):
        logger.debug("__iterate_forms_with_examples_found__: running")
        if len(self.lexemes.forms_with_possible_matching_usage_examples_found) > 0:
            for form in self.lexemes.forms_with_possible_matching_usage_examples_found:
                form.lexemes = self.lexemes
                result = form.__iterate_usage_examples_and_present_senses__()
                # If we get none we simply continue the loop
                if result is None:
                    continue
                # Save these results to persistent memory
                if result == ReturnValue.SKIP_FORM:
                    add_to_pickle(
                        pickle=SupportedFormPickles.DECLINED_FORMS,
                        form_id=form.id,
                    )
                    continue
                if result == ReturnValue.USAGE_EXAMPLE_ADDED:
                    add_to_pickle(
                        pickle=SupportedFormPickles.FINISHED_FORMS,
                        form_id=form.id,
                    )
        tui.print_run_again_text()

    def fetch_and_present_usage_examples(self):
        """This method is the entry for the TUI"""
        # disabled for now
        # begin = introduction()
        begin = True
        if begin:
            self.__choose_language__()
            # TODO store lexuse_introduction_read=True to e.g. settings.pkl
            self.__fetch_forms__()
            self.__fetch_usage_examples__()
            self.__inform_user_about_examples_found__()
            self.__iterate_forms_with_examples_found__()
