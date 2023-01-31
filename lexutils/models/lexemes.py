import logging
import random
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, validate_arguments
from wikibaseintegrator.wbi_helpers import execute_sparql_query  # type: ignore

import config
from lexutils import constants
from lexutils.enums import SupportedFormPickles
from lexutils.exceptions import MissingInformationError
from lexutils.helpers import tui, util
from lexutils.helpers.console import console
from lexutils.helpers.handle_pickles import add_to_pickle, can_read_from_pickle
from lexutils.models.wikidata.enums import WikimediaLanguageCode, WikimediaLanguageQID
from lexutils.models.wikidata.lexutils_lexeme import LexutilsLexeme

logger = logging.getLogger(__name__)


class Lexemes(BaseModel):
    """This class holds all lexemes and forms we currently work on

    We store the dataframes in the attributes to avoid loading
    it more than once because it causes a little delay"""

    # riksdagen_usage_examples: Optional[Any] = None
    forms_without_an_example_in_wikidata: List[Any] = []
    forms_with_possible_matching_usage_examples_found: List[Any] = []
    historical_ads_usage_examples: Optional[Any] = []
    lang: str  # this is mandatory
    language_code: Optional[WikimediaLanguageCode] = None
    language_qid: Optional[WikimediaLanguageQID] = None
    lexemes: List[LexutilsLexeme] = []
    approved_forms: List[Any] = []
    sparql_results: Dict[str, Any] = {}
    testing: bool = False

    class Config:
        arbitrary_types_allowed = True
        extra = "forbid"

    @validate_arguments
    def __is_finished_or_declined__(self, form: Any):
        finished = can_read_from_pickle(
            pickle=SupportedFormPickles.FINISHED_FORMS, form_id=form.id
        )
        declined = can_read_from_pickle(
            pickle=SupportedFormPickles.DECLINED_FORMS, form_id=form.id
        )
        if not finished and not declined:
            return False
        else:
            return True

    @property
    def number_of_forms_without_an_example(self) -> int:
        return len(self.forms_without_an_example_in_wikidata)

    @property
    def orthohin_url(self):
        if not self.language_code:
            raise MissingInformationError()
        return f"{constants.orthohin}add/{self.language_code.value}"

    @property
    def number_of_approved_forms(self):
        return len(self.approved_forms)

    @property
    def __build_query__(self):
        random_offset = random.randint(20, 1000)
        logger.info(f"random offset:{random_offset}")
        return f"""
                select ?form
                WHERE {{
                    ?lexeme dct:language wd:{self.language_qid.value};
                            wikibase:lemma ?lemma;
                            wikibase:lexicalCategory [];
                            ontolex:lexicalForm ?form;
                            ontolex:sense [].
                    # ?form ontolex:representation ?form_representation;
                    # wikibase:grammaticalFeature ?feature.
                    MINUS {{
                    ?lexeme p:P5831 ?statement.
                    ?statement ps:P5831 ?example;
                             pq:P6072 [];
                             pq:P5830 ?form_with_example.
                    }}
                }}
                offset {random_offset}
                limit {config.number_of_forms_to_fetch}"""

    def __get_usage_examples_from_supported_sources__(
        self,
        form: Any = None,
    ) -> List[Any]:
        """Find examples and return them as UsageExample objects"""
        logger.debug("__get_usage_examples_from_supported_sources__: running")
        if not self.language_code:
            raise MissingInformationError()
        if form is None:
            raise ValueError("form was None")
        from lexutils.models.wikidata.lexutils_form import LexutilsForm

        if not isinstance(form, LexutilsForm):
            raise ValueError("not a Lexutilsform")
        examples = []
        # Europarl corpus
        # Download first if not on disk
        # download_data.fetch()
        # europarl_records = europarl.get_records(form)
        # for record in europarl_records:
        #     records[record] = europarl_records[record]
        # logger.debug(f"records in total:{len(records)}")
        if self.language_code == WikimediaLanguageCode.SWEDISH:
            if not self.historical_ads_usage_examples:
                raise MissingInformationError()
            logger.info("Trying to find usage examples in the dataframes")
            historical_ads_examples = self.historical_ads_usage_examples.get_usage_examples(
                form=form
            )
            if historical_ads_examples is not None:
                examples.extend(historical_ads_examples)
            # print("debug exit")
            # exit()
            # riksdagen_examples = (
            #     self.riksdagen_usage_examples.find_form_representation_in_the_dataframe(
            #         form=form
            #     )
            # )
            # if riksdagen_examples is not None:
            #     examples.extend(riksdagen_examples)
        # ksamsok
        # Disabled because it yields very little of value
        # unfortunately because the data is such low quality overall
        # ksamsok_records = ksamsok.get_records(form)
        # for record in ksamsok_records:
        #     records[record] = ksamsok_records[record]
        # logger.debug(f"records in total:{len(records)}")
        # Wikisource
        # if len(examples) < 50:
        #     # If we already got 50 examples from a better source,
        #     # then don't fetch from Wikisource
        #     wikisource = WikisourceUsageExamples(form=form, lexemes=self)
        #     wikisource_usage_examples = wikisource.process_records_into_usage_examples()
        #     if wikisource_usage_examples is not None:
        #         examples.extend(wikisource_usage_examples)
        # Check for nested list
        for example in examples:
            from lexutils.models.usage_example import UsageExample

            if not isinstance(example, UsageExample):
                raise ValueError("Nested list error")
        if len(examples) > 0:
            logger.debug(f"examples found:{[example.text for example in examples]}")
        return examples

    def __convert_str_to_enums__(self):
        self.language_code = WikimediaLanguageCode(self.lang)
        self.language_qid = WikimediaLanguageQID[self.language_code.name]

    def fetch_forms_without_an_example(self) -> None:
        """This fetches forms and their lexemes and store them in an attribute"""
        logger.debug("fetch_forms_without_an_example: running")
        # title:LexutilsForms that have no example demonstrating them and that have at least
        # one sense
        if not self.language_code:
            raise MissingInformationError()
        if not self.language_qid:
            raise MissingInformationError()
        self.__get_results_from_sparql__()
        self.__parse_results_into_lexutils_forms__()
        if len(self.forms_without_an_example_in_wikidata) == 0:
            console.print(
                "Got no forms from Wikidata to work on for this language "
                "if you think this is a bug, please open an issue here "
                f"{tui.issue_url()}"
            )
            exit()
        else:
            logger.info(
                f"Got {len(self.forms_without_an_example_in_wikidata)} "
                f"forms from WDQS for language {self.language_code.name.title()}"
            )

    def __parse_results_into_lexutils_forms__(self):
        logger.debug("__parse_results_into_lexutils_forms__: running")

        # self.forms_without_an_example: List[LexutilsForm] = []
        # pprint(results)
        if "results" in self.sparql_results:
            if "bindings" in self.sparql_results["results"]:
                # logger.debug(f"data:{results['results']['bindings']}")
                forms = self.sparql_results["results"]["bindings"]
                logger.info(f"Got {len(forms)} forms")
                for entry in forms:
                    # logger.info(f"data:{entry.keys()}")
                    logging.debug(f"lexeme_json:{entry}")
                    form_id = entry["form"]["value"]
                    form_id = self.clean_id(form_id)
                    logger.debug(f"extracted form id: {form_id}")
                    from lexutils.models.wikidata.lexutils_form import LexutilsForm

                    form = LexutilsForm(form_id=form_id)
                    form.language_code = self.language_code
                    form.setup_lexeme()
                    logger.info(
                        f"appending {form.localized_representation} to list of forms"
                    )
                    # logger.info("debug exit")
                    # exit(0)
                    self.forms_without_an_example_in_wikidata.append(form)
            else:
                raise ValueError("Got no bindings dict from WD")

    def fetch_usage_examples(self):
        """Fetch usage examples for all forms fetched"""
        if self.number_of_forms_without_an_example == 0:
            raise ValueError("self.forms_without_an_example was empty")
        # console.print(f"Fetching usage examples for {len(self.forms_without_an_example)} forms")
        # console.print(f"Fetching usage examples for all forms")
        # from http://stackoverflow.com/questions/306400/ddg#306417
        # We do this now because we only want to do it once
        # and keep it in memory during the looping through all the forms
        if self.language_code == WikimediaLanguageCode.SWEDISH:
            self.__setup_swedish_sources__()
        from lexutils.models.wikidata.lexutils_form import LexutilsForm

        self.forms_with_possible_matching_usage_examples_found: List[LexutilsForm] = []
        self.__get_approved_forms__()
        self.__iterate_approved_forms_and_fetch_examples__()

    @staticmethod
    def clean_id(form_id):
        """Clean away the prefix form WDQS"""
        return form_id.replace("http://www.wikidata.org/entity/", "")

    def __setup_swedish_sources__(self):
        logger.info("Loading Swedish dataframes now")
        from lexutils.models.dataframe_usage_examples_extractor.historical_job_ads import (
            HistoricalJobAdsUsageExamplesExtractor,
        )

        # from lexutils.models.disabled.riksdagen_usage_examples import RiksdagenUsageExamples

        self.historical_ads_usage_examples = HistoricalJobAdsUsageExamplesExtractor(
            testing=self.testing
        )
        # self.riksdagen_usage_examples = RiksdagenUsageExamples()

    def __get_approved_forms__(self):
        logger.debug("__get_approved_forms__: running")
        from lexutils.models.wikidata.lexutils_form import LexutilsForm

        self.approved_forms: List[LexutilsForm] = []
        if config.require_form_confirmation:
            for form in self.forms_without_an_example_in_wikidata:
                console.print(form)
                if util.yes_no_question(form.work_on_text):
                    self.approved_forms.append(form)
                else:
                    logger.info("Adding form to declined pickle_path")
                    add_to_pickle(
                        pickle=SupportedFormPickles.DECLINED_FORMS,
                        form_id=form.id,
                    )
        else:
            # Approve all forms
            self.approved_forms.extend(self.forms_without_an_example_in_wikidata)

    def __iterate_approved_forms_and_fetch_examples__(self):
        logger.debug("__iterate_approved_forms_and_fetch_examples__: running")
        count = 1
        for form in self.approved_forms:
            if self.__is_not_finished_or_declined__(form=form):
                with console.status(
                    f"Processing form {count}/"
                    f"{self.number_of_forms_without_an_example}"
                ):
                    if form.lexeme_id is None:
                        raise ValueError("lexeme_id on form was None")
                    # fetch usage examples
                    # Fetch sentence data from all APIs
                    form.usage_examples = (
                        self.__get_usage_examples_from_supported_sources__(
                            form=form,
                        )
                    )
                    logger.info(
                        f"Found {form.number_of_usage_examples_found} usage examples for '{form.localized_representation}'"
                    )
                    if form.number_of_usage_examples_found > 0:
                        self.forms_with_possible_matching_usage_examples_found.append(
                            form
                        )
            count += 1

    def __get_results_from_sparql__(self):
        self.sparql_results = execute_sparql_query(self.__build_query__)
        if not self.sparql_results:
            raise MissingInformationError("Got no results dict from WD")
