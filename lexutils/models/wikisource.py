from __future__ import annotations
import logging
from html import unescape
from typing import List, TYPE_CHECKING
from urllib.parse import quote

import requests
import spacy as spacy
from spacy.lang.en import English
from spacy.lang.sv import Swedish

from lexutils.config import config
from lexutils.config.enums import SupportedExampleSources, LanguageStyle, ReferenceType
from lexutils.models.record import Record
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.form import Form

if TYPE_CHECKING:
    from lexutils.models.lexemes import Lexemes


class WikisourceRecord(Record):
    """Model for a record from Wikisource"""
    # This is based on the riksdagen model
    language_style = LanguageStyle.FORMAL
    type_of_reference = ReferenceType.WRITTEN
    source = SupportedExampleSources.WIKISOURCE
    document_title = None

    def __init__(self,
                 json=None,
                 lexemes: Lexemes = None):
        try:
            self.document_title = json["title"]["value"]
        except KeyError:
            raise KeyError("Could not find title")
        try:
            # Remove &quot; and the like from the snippet
            self.text = unescape(json["snippet"]["value"])
        except KeyError:
            raise KeyError("Could not find snippet")
        self.language_code = lexemes.language_code
        # try:
        #     # self.date = datetime.strptime(json["datum"], "%d%m%Y")
        #     self.date = datetime.strptime(json["datum"][0:10], "%Y-%m-%d")
        # except KeyError:
        #     raise KeyError("Could not find id")

    def __str__(self):
        return f"{self.document_title}: {self.text}"

    def find_usage_examples_from_summary(
            self,
            form: Form = None,
    ) -> List[UsageExample]:
        """This tries to find and clean sentences and return the shortest one"""
        if form is None:
            raise ValueError("form was None")
        logger = logging.getLogger(__name__)
        # find sentences
        # order in a list by length
        # pick the shortest one where the form representation appears
        if self.language_code == WikimediaLanguageCode.ENGLISH:
            logger.info("using the English spaCy pipeline")
            nlp = English()
            nlp.add_pipe('sentencizer')
        elif self.language_code == WikimediaLanguageCode.SWEDISH:
            nlp = Swedish()
            nlp.add_pipe('sentencizer')
        elif (
                self.language_code == WikimediaLanguageCode.FRENCH or
                self.language_code == WikimediaLanguageCode.GERMAN or
                self.language_code == WikimediaLanguageCode.BOKMÅL or
                self.language_code == WikimediaLanguageCode.DANISH
        ):
            logger.info(f"using the {self.language_code.name.title()} spaCy pipeline")
            try:
                nlp = spacy.load(f'{self.language_code.value}_core_news_sm')
            except:
                raise ModuleNotFoundError(
                    f"Please install the spacy model for "
                    f"{self.language_code.name.title()} by running: "
                    f"'python -m spacy download "
                    f"{self.language_code.value}_core_news_sm' "
                    f"in the terminal/cmd/powershell"
                )
        else:
            raise NotImplementedError(f"Sentence extraction for {self.language_code.name} "
                                      f"is not supported yet, feel free to open an issue at "
                                      f"https://github.com/dpriskorn/LexUtils/issues")
        doc = nlp(self.text)
        sentences = set()
        for sentence in doc.sents:
            # logger.info(sentence.text)
            # This is a very crude test for relevancy, we lower first to improve matching
            cleaned_sentence = sentence.text.lower()
            punctations = [".", ",", "!", "?", "„", "“"]
            for punctation in punctations:
                if punctation in cleaned_sentence:
                    cleaned_sentence = cleaned_sentence.replace(punctation, " ")
            logger.debug(f"cleaned sentence:{cleaned_sentence}")
            if f" {form.representation.lower()} " in cleaned_sentence:
                # Add to the set first to avoid duplicates
                sentences.add(sentence.text)
        examples = []
        for sentence in sentences:
            sentence_length = len(sentence.split(" "))
            if (
                    sentence_length > config.min_word_count and
                    sentence_length < config.max_word_count
            ):
                examples.append(UsageExample(sentence=sentence, record=self))
        # print("debug exit")
        # exit(0)
        return examples

    def lookup_qid(self):
        def extract_wikidata_qid(json):
            for page_id in json["query"]["pages"].keys():
                page_data = json["query"]["pages"][page_id]
                if "pageprops" in page_data:
                    page_properties = page_data["pageprops"]
                    logger.debug(f'found {page_properties}')
                    if "wikibase_item" in page_properties:
                        self.document_qid = page_properties["wikibase_item"]
                        logger.info(f"Found QID {self.document_qid}")
                        break

        #  https://stackoverflow.com/questions/37024807/how-to-get-wikidata-id-for-an-wikipedia-article-by-api
        logger = logging.getLogger(__name__)
        if self.language_code is None:
            raise ValueError("language was None")
        if self.document_title is None:
            raise ValueError("document_title was None")
        url = (f"https://{self.language_code.value}.wikisource.org/w/api.php?"
               f"action=query&prop=pageprops&ppprop=wikibase_item&"
               f"redirects=1&format=json&titles={quote(self.document_title)}")
        logger.info(f"Looking up {url}")
        response = requests.get(url, headers={"Accept": "application/json"})
        if response.status_code == 200:
            if 'application/json' in response.headers['Content-Type']:
                decoded_result = response.json()
                logger.debug(decoded_result)
                extract_wikidata_qid(decoded_result)
                if self.document_qid is None:
                    # try finding a QID by truncating the title
                    truncated_title = self.document_title.split("/")[0]
                    if self.document_title != truncated_title:
                        logger.info(f"Trying to find QID using the truncated title: {truncated_title}")
                        url = (f"https://{self.language_code.value}.wikisource.org/w/api.php?"
                               f"action=query&prop=pageprops&ppprop=wikibase_item&"
                               f"redirects=1&format=json&titles={quote(truncated_title)}")
                        logger.info(f"Looking up {url}")
                        response = requests.get(url, headers={"Accept": "application/json"})
                        if response.status_code == 200:
                            if 'application/json' in response.headers['Content-Type']:
                                decoded_result = response.json()
                                logger.debug(decoded_result)
                                extract_wikidata_qid(decoded_result)
                                if self.document_qid is None:
                                    logger.info("Found no QID for this page")
                # print("debug exit")
                # exit(0)
            else:
                non_json_result = response.text
                raise ValueError("Got no JSON result from Wikisource")
        else:
            raise ValueError(f"Got {response.status_code} from the Wikisource API, see {url}")
        if self.document_qid is None:
            logger.info("Could not find a QID for this page or work in Wikisource. :/")

    def url(self):
        return f"http://{self.language_code.value}.wikisource.org/wiki/{quote(self.document_title)}"
