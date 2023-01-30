import logging
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import quote

from wikibaseintegrator import WikibaseIntegrator, wbi_config, wbi_login  # type: ignore
from wikibaseintegrator.datatypes import URL, ExternalID  # type: ignore
from wikibaseintegrator.datatypes import Form as FormDT  # type: ignore
from wikibaseintegrator.datatypes import Item, MonolingualText  # type: ignore
from wikibaseintegrator.datatypes import Sense as SenseDT  # type: ignore
from wikibaseintegrator.datatypes import String, Time  # type: ignore
from wikibaseintegrator.entities import ItemEntity, LexemeEntity  # type: ignore
from wikibaseintegrator.models import Form  # type: ignore
from wikibaseintegrator.wbi_enums import ActionIfExists  # type: ignore

import config
from lexutils import constants
from lexutils.enums import SupportedExampleSources
from lexutils.exceptions import MissingInformationError
from lexutils.helpers.console import console
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.lexutils_lexeme import LexutilsLexeme
from lexutils.models.wikidata.lexutils_sense import LexutilsSense

logger = logging.getLogger(__name__)


class LexutilsForm(Form):
    """
    Model for a Wikibase form
    """

    language_code: WikimediaLanguageCode
    # We store these on the form because they are needed
    # to determine if an example fits or not
    usage_examples: List[UsageExample] = []
    # The lexeme has the data about senses
    lexeme: Optional[LexutilsLexeme] = None

    @property
    def clean_id(self) -> str:
        return str(self.id).replace("http://www.wikidata.org/entity/", "")

    @property
    def number_of_examples_found(self):
        return len(self.usage_examples)

    @property
    def number_of_senses(self):
        return len(self.senses)

    @property
    def localized_lexeme_category(self) -> str:
        # TODO implement caching of this locally
        if not self.lexeme:
            raise MissingInformationError()
        if not self.language_code:
            raise MissingInformationError()
        return str(
            ItemEntity()
            .get(entity_id=self.lexeme.lexical_category)
            .labels.get(self.language_code.value)
        )

    @property
    def lexeme_category(self) -> str:
        """This returns a QID"""
        if not self.lexeme:
            raise MissingInformationError("no lexeme")
        return str(self.lexeme.lexical_category)

    @property
    def lexeme_id(self) -> str:
        """This returns a LID based on self.id"""
        return self.clean_id.split("-")[0]

    @property
    def senses(self):
        """Helper method"""
        logger.debug("senses: running")
        if not self.lexeme:
            raise MissingInformationError("no lexeme")
        return self.lexeme.lexutils_senses

    @property
    def form(self):
        """This contains all the data from Wikidata, like grammatical features"""
        if not self.lexeme:
            raise MissingInformationError()
        return self.lexeme.forms.get(id=self.id)

    @property
    def localized_grammatical_features(self) -> List[str]:
        logger.debug("localized_grammatical_features: running")
        names: List[str] = []
        " "
        for feature_qid in self.form.grammatical_features:
            logger.debug(f"found feature_qid: {feature_qid}")
            name = str(
                ItemEntity()
                .get(entity_id=feature_qid)
                .labels.get(language=self.language_code.value)
            )
            if name:
                names.append(name)
        return names

    @property
    def localized_representation(self) -> str:
        """Get the representation we need"""
        return str(self.form.representations.get(language=self.language_code.value))

    @property
    def work_on_text(self):
        return (
            "Work on {} ({}) with the features: {}".format(
                self.localized_representation,
                self.localized_lexeme_category,
                ", ".join(self.localized_grammatical_features),
            )
            + f"\n{self.hangor_url}"
        )

    @property
    def presentation(self):
        return (
            f"[bold green]{self.localized_representation}[/bold green]\n"
            f"category: {self.lexeme_category}\n"
            f"features: {', '.join(self.localized_grammatical_features)}"
        )

    def __str__(self):
        return f"{self.id} / {self.localized_representation}"

    @property
    def url(self):
        return f"{config.wd_prefix}{self.id}"

    @property
    def hangor_url(self):
        return f"{constants.hangor}lex/{self.language_code.value}/{quote(self.localized_representation)}"

    @property
    def orthohin_url(self):
        return f"{constants.orthohin}add/{self.language_code.value}"

    @property
    def wikidata_search_url(self):
        # quote to guard against äöå and the like
        return (
            "https://www.wikidata.org/w/index.php?"
            + f"search={quote(self.localized_representation)}&title=Special%3ASearch&"
            + "profile=advanced&fulltext=0&"
            + "advancedSearch-current=%7B%7D&ns0=1"
        )

    def print_cancel_sentence_text(self):
        console.print(
            "Cancelled adding sentence as it does not match the "
            + "sense(s) currently present. \n"
            "[bold]List of recommended tools to improve the lexemes:[/bold]\n"
            f"* [bold]Hangor[/bold]: tool to add senses to this "
            f"form manually {self.hangor_url}\n"
            f"* [bold]MachtSinn[/bold]: tool to match lexemes with QIDs "
            f"{constants.machtsinn} Warning: This tool is neither well "
            f"maintained nor updated so if be very careful when using it.\n"
            f"* [bold]Orthohin[/bold]: tool to add senses manually "
            f"to any lexeme in a certain language {self.orthohin_url}\n"
        )

    def setup_lexeme(self):
        logger.debug("setup_lexeme: running")
        if not self.language_code:
            raise MissingInformationError()
        # get and prepare the lexeme
        self.lexeme = LexutilsLexeme().from_json(
            json_data=LexemeEntity().get(entity_id=self.lexeme_id).get_json()
        )
        self.lexeme.language_code = self.language_code
        self.lexeme.get_lexutils_senses()

    def add_usage_example(
        self, sense: LexutilsSense = None, usage_example: UsageExample = None
    ) -> LexemeEntity:
        """This adds a usage example to the current lexeme
        This only has side effects"""
        if not sense:
            raise MissingInformationError("sense was None")
        if not usage_example:
            raise MissingInformationError("usage_example was None")
        if not usage_example.record:
            raise MissingInformationError
        # reference = None
        logger.info("Adding usage example with WBI")
        # Use WikibaseIntegrator aka wbi to upload the changes in one edit
        link_to_form = FormDT(
            prop_nr="P5830",
            value=self.id,
        )
        link_to_sense = SenseDT(prop_nr="P6072", value=sense.id)
        language_style_qualifier = Item(
            prop_nr="P6191", value=usage_example.record.language_style.value
        )
        type_of_reference_qualifier = Item(
            prop_nr="P3865", value=usage_example.record.type_of_reference.value
        )
        # retrieved_date = Time(
        #     prop_nr="P813",  # Fetched today
        #     time=datetime.utcnow()
        #     .replace(tzinfo=timezone.utc)
        #     .replace(
        #         hour=0,
        #         minute=0,
        #         second=0,
        #     )
        #     .strftime("+%Y-%m-%dT%H:%M:%SZ"),
        # )
        # if usage_example.record.source == SupportedExampleSources.RIKSDAGEN:
        #     logger.info("Riksdagen record detected")
        #     if usage_example.record.date is not None:
        #         if (
        #             usage_example.record.date.day == 1
        #             and usage_example.record.date.month == 1
        #         ):
        #             logger.info("Detected year precision on the date")
        #             publication_date = Time(
        #                 prop_nr="P577",  # Publication date
        #                 time=usage_example.record.date.strftime("+%Y-%m-%dT00:00:00Z"),
        #                 # Precision is year if the date is 1/1
        #                 precision=9,
        #             )
        #         else:
        #             publication_date = Time(
        #                 prop_nr="P577",  # Publication date
        #                 time=usage_example.record.date.strftime("+%Y-%m-%dT00:00:00Z"),
        #                 precision=11,
        #             )
        #     else:
        #         raise ValueError(
        #             f"Publication date of document {usage_example.record.id} "
        #             + "is missing. We have no fallback for that at the moment. "
        #             + "Aborting."
        #         )
        #     if usage_example.record.document_qid is not None:
        #         logger.info(
        #             f"using document QID {usage_example.record.document_qid} as value for P248"
        #         )
        #         stated_in = Item(
        #             prop_nr="P248", value=usage_example.record.document_qid
        #         )
        #         reference = [
        #             stated_in,
        #             retrieved_date,
        #             publication_date,
        #             type_of_reference_qualifier,
        #         ]
        #     else:
        #         stated_in = Item(prop_nr="P248", value="Q21592569")
        #         document_id = ExternalID(
        #             prop_nr="P8433",  # Riksdagen Document ID
        #             value=usage_example.record.id,
        #         )
        #         if publication_date is not None:
        #             reference = [
        #                 stated_in,
        #                 document_id,
        #                 retrieved_date,
        #                 publication_date,
        #                 type_of_reference_qualifier,
        #             ]
        # elif usage_example.record.source == SupportedExampleSources.WIKISOURCE:
        #     logger.info("Wikisource record detected")
        #     usage_example.record.lookup_qid()
        #     if usage_example.record.document_qid is not None:
        #         logger.info(
        #             f"using document QID {usage_example.record.document_qid} as value for P248"
        #         )
        #         stated_in = Item(
        #             prop_nr="P248", value=usage_example.record.document_qid
        #         )
        #         wikimedia_import_url = URL(
        #             prop_nr="P4656", value=usage_example.record.url()
        #         )
        #         reference = [
        #             stated_in,
        #             wikimedia_import_url,
        #             retrieved_date,
        #             type_of_reference_qualifier,
        #         ]
        #     else:
        #         # TODO discuss whether we want to add this, it can rather easily
        #         #  be inferred from the import url and the QID of the work
        #         # search via sparql for english wikisource QID?
        #         # stated_in = Item(
        #         #     prop_nr="P248",
        #         #     value=
        #         # )
        #         wikimedia_import_url = URL(
        #             prop_nr="P4656", value=usage_example.record.url()
        #         )
        #         reference = [
        #             # stated_in,
        #             wikimedia_import_url,
        #             retrieved_date,
        #             type_of_reference_qualifier,
        #         ]
        if usage_example.record.source == SupportedExampleSources.HISTORICAL_ADS:
            logger.info("Historical Ad record detected")
            if not usage_example.record.date:
                raise MissingInformationError()
            stated_in = Item(
                prop_nr="P248", value=SupportedExampleSources.HISTORICAL_ADS.value
            )
            record_number = String(
                prop_nr="P9994", value=str(usage_example.record.id)  # record number
            )
            reference_url = URL(prop_nr="P854", value=usage_example.record.url())
            published_date = Time(
                prop_nr="P577",
                time=usage_example.record.date.strftime("+%Y-%m-%dT00:00:00Z"),
                precision=11
                #     (
                #     # First parse the date string and then output it
                #     usage_example.record.date
                #         .strptime("+%Y-%m-%dT%H:%M:%SZ")
                #         .strftime("+%Y-%m-%dT%H:%M:%SZ")
                # )
            )
            historical_ads_retrieved_date = Time(
                prop_nr="P813",  # Fetched 2021-01-13
                time=datetime.strptime("2021-01-13", "%Y-%m-%d")
                .replace(tzinfo=timezone.utc)
                .replace(
                    hour=0,
                    minute=0,
                    second=0,
                )
                .strftime("+%Y-%m-%dT%H:%M:%SZ"),
            )
            reference = [
                stated_in,
                record_number,
                reference_url,
                historical_ads_retrieved_date,
                published_date,
                type_of_reference_qualifier,
            ]
        # elif source == "europarl":
        #     stated_in = wbi_datatype.ItemID(
        #         prop_nr="P248",
        #         value="Q5412081",
        #         is_reference=True
        #     )
        #     reference = [
        #         stated_in,
        #         wbi_datatype.Time(
        #             prop_nr="P813",  # Fetched today
        #             time=datetime.utcnow().replace(
        #                 tzinfo=timezone.utc
        #             ).replace(
        #                 hour=0,
        #                 minute=0,
        #                 second=0,
        #             ).strftime("+%Y-%m-%dT%H:%M:%SZ"),
        #             is_reference=True,
        #         ),
        #         wbi_datatype.Time(
        #             prop_nr="P577",  # Publication date
        #             time="+2012-05-12T00:00:00Z",
        #             is_reference=True,
        #         ),
        #         wbi_datatype.Url(
        #             prop_nr="P854",  # reference url
        #             value="http://www.statmt.org/europarl/v7/sv-en.tgz",
        #             is_reference=True,
        #         ),
        #         # filename in archive
        #         wbi_datatype.String(
        #             (f"europarl-v7.{config.language_code}" +
        #              f"-en.{config.language_code}"),
        #             "P7793",
        #             is_reference=True,
        #         ),
        #         # line number
        #         wbi_datatype.String(
        #             str(line),
        #             "P7421",
        #             is_reference=True,
        #         ),
        #         type_of_reference_qualifier,
        #     ]
        # elif source == "ksamsok":
        #     # No date is provided unfortunately, so we set it to unknown value
        #     stated_in = wbi_datatype.ItemID(
        #         prop_nr="P248",
        #         value="Q7654799",
        #         is_reference=True
        #     )
        #     document_id = wbi_datatype.ExternalID(
        #         # K-Samsök URI
        #         prop_nr="P1260",
        #         value=document_id,
        #         is_reference=True
        #     )
        #     reference = [
        #         stated_in,
        #         document_id,
        #         wbi_datatype.Time(
        #             prop_nr="P813",  # Fetched today
        #             time=datetime.utcnow().replace(
        #                 tzinfo=timezone.utc
        #             ).replace(
        #                 hour=0,
        #                 minute=0,
        #                 second=0,
        #             ).strftime("+%Y-%m-%dT%H:%M:%SZ"),
        #             is_reference=True,
        #         ),
        #         wbi_datatype.Time(
        #             # We don't know the value of the publication dates unfortunately
        #             prop_nr="P577",  # Publication date
        #             time="",
        #             snak_type="somevalue",
        #             is_reference=True,
        #         ),
        #         type_of_reference_qualifier,
        #     ]
        else:
            raise ValueError(
                f"Did not recognize the source {usage_example.record.source.name.title()}"
            )
        if reference is None:
            raise ValueError("No reference defined, cannot add usage example")
        else:
            # This is the usage example statement
            usage_example_claim = MonolingualText(
                text=usage_example.text,
                prop_nr="P5831",
                language=usage_example.record.language_code.value,
                # Add qualifiers
                qualifiers=[
                    link_to_form,
                    link_to_sense,
                    language_style_qualifier,
                ],
                # Add reference
                references=[reference],
            )
            # if config.debug_json:
            #     logging.debug(f"claim:{claim.get_json_representation()}")
            if config.login_instance is None:
                # Authenticate with WikibaseIntegrator
                with console.status("Logging in with WikibaseIntegrator..."):
                    config.login_instance = wbi_login.Login(
                        auth_method="login",
                        user=config.username,
                        password=config.password,
                        debug=False,
                    )
                    # Set User-Agent
                    wbi_config.config["USER_AGENT_DEFAULT"] = config.user_agent
            wbi = WikibaseIntegrator(login=config.login_instance)
            lexeme = wbi.lexeme.get(self.lexeme_id)
            lexeme.add_claims(
                [usage_example_claim], action_if_exists=ActionIfExists.APPEND_OR_REPLACE
            )
            # if config.debug_json:
            #     print(item.get_json_representation())

            result = lexeme.write(
                summary=("Added usage example " + f"with [[Wikidata:Tools/LexUtils]]")
            )
            # logging.debug(f"result from WBI:{result}")
            # TODO add handling of result from WBI and return True == Success or False
            return result
