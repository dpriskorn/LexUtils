from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING

from wikibaseintegrator import wbi_config, wbi_login, WikibaseIntegrator
from wikibaseintegrator.datatypes import ExternalID, Form as WBIForm, Sense as WBISense, Time, MonolingualText, Item, \
    URL, String
from wikibaseintegrator.wbi_enums import ActionIfExists
from wikibaseintegrator.wbi_helpers import execute_sparql_query

from lexutils.config import config
from lexutils.config.enums import SupportedExampleSources
from lexutils.helpers import wdqs
from lexutils.helpers.console import console
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.enums import WikidataNamespaceLetters

if TYPE_CHECKING:
    from lexutils.models.wikidata.form import Form
    from lexutils.models.wikidata.sense import Sense

wbi_config.config['USER_AGENT'] = config.user_agent


class EntityID:
    letter: WikidataNamespaceLetters
    # This can be e.g. "32698-F1" in the case of a lexeme
    rest: str

    def __init__(self,
                 entity_id: str):
        logger = logging.getLogger(__name__)
        if entity_id is not None:
            # Remove prefix if found
            if config.wd_prefix in entity_id:
                logger.debug("Removing prefix")
                entity_id = entity_id.replace(config.wd_prefix, "")
            if len(entity_id) > 1:
                logger.debug(f"entity_id:{entity_id}")
                self.letter = WikidataNamespaceLetters(entity_id[0])
                self.rest = entity_id[1:]
            else:
                raise ValueError("Entity ID was too short.")
        else:
            raise ValueError("Entity ID was None")

    def __str__(self):
        return f"{self.letter.value}{self.rest}"

    # def extract_wdqs_json_entity_id(self, json: Dict, sparql_variable: str):
    #     self.__init__(json[sparql_variable]["value"].replace(
    #         config.wd_prefix, ""
    #     ))


class Lexeme:
    id: str
    lemma: str
    lexical_category: EntityID
    forms: List[Form]
    senses: List[Sense]

    def __init__(self,
                 id: str = None,
                 lemma: str = None,
                 lexical_category: str = None):
        self.id = str(EntityID(id))
        self.lemma = lemma
        if lexical_category is not None:
            self.lexical_category = EntityID(lexical_category)

    def parse_from_wdqs_json(self, json):
        self.forms = []
        self.senses = []
        for variable in json:
            logging.debug(variable)
            if variable == "form":
                form = Form(variable)
                self.forms.append(form)
            if variable == "sense":
                sense = Sense(variable)
                self.senses.append(sense)
            if variable == "category":
                self.lexical_category = str(EntityID(extract_wikibase_value_from_result(variable)))

    def url(self):
        return f"{config.wd_prefix}{self.id}"

    def usage_example_url(self):
        return f"https://www.wikidata.org/wiki/Lexeme:{self.id}#P5831"

    # def upload_foreign_id_to_wikidata(self,
    #                                   foreign_id: ForeignID = None):
    #     """Upload to enrich the wonderful Wikidata <3"""
    #     logger = logging.getLogger(__name__)
    #     if foreign_id is None:
    #         raise Exception("Foreign id was None")
    #     print(f"Uploading {foreign_id.id} to {self.id}: {self.lemma}")
    #     statement = ExternalID(
    #         prop_nr=foreign_id.prop_nr,
    #         value=foreign_id.id,
    #     )
    #     described_by_source = Item(
    #         prop_nr="P1343",  # stated in
    #         value=foreign_id.source_item_id
    #     )
    #     # TODO does this overwrite or append?
    #     item = ItemEngine(
    #         data=[statement,
    #               described_by_source],
    #         item_id=self.id
    #     )
    #     # debug WBI error
    #     # print(item.get_json_representation())
    #     result = item.write(
    #         config.login_instance,
    #         edit_summary=f"Added foreign identifier with [[{config.tool_url}]]"
    #     )
    #     logger.debug(f"result from WBI:{result}")
    #     print(self.url())
    #     # exit(0)

    def count_number_of_senses_with_P5137(self):
        """Returns an int"""
        result = (execute_sparql_query(f'''
        SELECT
        (COUNT(?sense) as ?count)
        WHERE {{
          VALUES ?l {{wd:{self.id}}}.
          ?l ontolex:sense ?sense.
          ?sense skos:definition ?gloss.
          # Exclude lexemes without a linked QID from at least one sense
          ?sense wdt:P5137 [].
        }}'''))
        count: int = wdqs.extract_count(result)
        logging.debug(f"count:{count}")
        return count

    def add_usage_example(
            self,
            form: Form = None,
            sense: Sense = None,
            usage_example: UsageExample = None
    ):
        """This only has side effects"""
        # TODO convert to use OOP
        logger = logging.getLogger(__name__)
        if form is None:
            raise ValueError("form was None")
        if sense is None:
            raise ValueError("sense was None")
        if usage_example is None:
            raise ValueError("usage_example was None")
        logger.info("Adding usage example with WBI")
        # Use WikibaseIntegrator aka wbi to upload the changes in one edit
        link_to_form = WBIForm(
            prop_nr="P5830",
            # FIXME debug why this is the lexeme id
            value=form.id
        )
        link_to_sense = WBISense(
            prop_nr="P6072",
            value=sense.id
        )
        language_style_qualifier = Item(
            prop_nr="P6191",
            value=usage_example.record.language_style.value
        )
        type_of_reference_qualifier = Item(
            prop_nr="P3865",
            value=usage_example.record.type_of_reference.value
        )
        retrieved_date = Time(
            prop_nr="P813",  # Fetched today
            time=datetime.utcnow().replace(
                tzinfo=timezone.utc
            ).replace(
                hour=0,
                minute=0,
                second=0,
            ).strftime("+%Y-%m-%dT%H:%M:%SZ")
        )
        if usage_example.record.source == SupportedExampleSources.RIKSDAGEN:
            logger.info("Riksdagen record detected")
            if usage_example.record.date is not None:
                if usage_example.record.date.day == 1 and usage_example.record.date.month == 1:
                    logger.info("Detected year precision on the date")
                    publication_date = Time(
                        prop_nr="P577",  # Publication date
                        time=usage_example.record.date.strftime("+%Y-%m-%dT00:00:00Z"),
                        # Precision is year if the date is 1/1
                        precision=9
                    )
                else:
                    publication_date = Time(
                        prop_nr="P577",  # Publication date
                        time=usage_example.record.date.strftime("+%Y-%m-%dT00:00:00Z"),
                        precision=11
                    )
            else:
                raise ValueError(_("Publication date of document {} ".format(usage_example.record.id) +
                               "is missing. We have no fallback for that at the moment. " +
                               "Aborting."))
            if usage_example.record.document_qid is not None:
                logger.info(f"using document QID {usage_example.record.document_qid} as value for P248")
                stated_in = Item(
                    prop_nr="P248",
                    value=usage_example.record.document_qid
                )
                reference = [
                    stated_in,
                    retrieved_date,
                    publication_date,
                    type_of_reference_qualifier,
                ]
            else:
                stated_in = Item(
                    prop_nr="P248",
                    value="Q21592569"
                )
                document_id = ExternalID(
                    prop_nr="P8433",  # Riksdagen Document ID
                    value=usage_example.record.id
                )
                if publication_date is not None:
                    reference = [
                        stated_in,
                        document_id,
                        retrieved_date,
                        publication_date,
                        type_of_reference_qualifier,
                    ]
        elif usage_example.record.source == SupportedExampleSources.WIKISOURCE:
            logger.info("Wikisource record detected")
            usage_example.record.lookup_qid()
            if usage_example.record.document_qid is not None:
                logger.info(f"using document QID {usage_example.record.document_qid} as value for P248")
                stated_in = Item(
                    prop_nr="P248",
                    value=usage_example.record.document_qid
                )
                wikimedia_import_url = URL(
                    prop_nr="P4656",
                    value=usage_example.record.url()
                )
                reference = [
                    stated_in,
                    wikimedia_import_url,
                    retrieved_date,
                    type_of_reference_qualifier,
                ]
            else:
                # TODO discuss whether we want to add this, it can rather easily
                #  be inferred from the import url and the QID of the work
                # search via sparql for english wikisource QID?
                # stated_in = Item(
                #     prop_nr="P248",
                #     value=
                # )
                wikimedia_import_url = URL(
                    prop_nr="P4656",
                    value=usage_example.record.url()
                )
                reference = [
                    # stated_in,
                    wikimedia_import_url,
                    retrieved_date,
                    type_of_reference_qualifier,
                ]
        elif usage_example.record.source == SupportedExampleSources.HISTORICAL_ADS:
            logger.info("Historical Ad record detected")
            stated_in = Item(
                prop_nr="P248",
                value=SupportedExampleSources.HISTORICAL_ADS.value
            )
            # TODO wait for https://www.wikidata.org/wiki/Wikidata:Property_proposal/Swedish_Historical_Job_Ads_ID to be approved
            record_number = String(
                prop_nr="P9994",  #  record number
                value=usage_example.record.id
            )
            reference_url = URL(
                prop_nr="P854",
                value=usage_example.record.url()
            )
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
                time=datetime.strptime("2021-01-13", "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                ).replace(
                    hour=0,
                    minute=0,
                    second=0,
                ).strftime("+%Y-%m-%dT%H:%M:%SZ")
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
            raise ValueError(f"Did not recognize the source {usage_example.record.source.name.title()}")
        if reference is None:
            raise ValueError(_("No reference defined, cannot add usage example"))
        else:
            # This is the usage example statement
            claim = MonolingualText(
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
                        auth_method='login',
                        user=config.username,
                        password=config.password,
                        debug=False
                    )
                    # Set User-Agent
                    wbi_config.config["USER_AGENT_DEFAULT"] = config.user_agent
            wbi = WikibaseIntegrator(login=config.login_instance)
            lexeme = wbi.lexeme.get(form.lexeme_id)
            lexeme.add_claims(
                [claim],
                action_if_exists=ActionIfExists.APPEND
            )
            # if config.debug_json:
            #     print(item.get_json_representation())

            result = lexeme.write(
                summary=("Added usage example " +
                         "with [[Wikidata:Tools/LexUtils]] v{}".format(config.version))
            )
            # logging.debug(f"result from WBI:{result}")
            # TODO add handling of result from WBI and return True == Success or False
            return result
