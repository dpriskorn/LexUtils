import logging
from typing import List

import requests
from spacy.lang.en import English
from spacy.lang.sv import Swedish

from lexutils.config import config
from lexutils.config.enums import SupportedExampleSources, LanguageStyle, ReferenceType
from lexutils.models.record import Record
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.form import Form
from lexutils.models.wikidata.misc import LexemeLanguage


class WikisourceRecord(Record):
    """Model for a record from Wikisource"""
    # This is based on the riksdagen model
    language_style = LanguageStyle.FORMAL
    type_of_reference = ReferenceType.WRITTEN
    source = SupportedExampleSources.WIKISOURCE
    language_code: WikimediaLanguageCode = None
    document_title = None
    snippet: str = None

    def __init__(self,
                 json=None,
                 lexemelanguage: LexemeLanguage = None):
        try:
            self.document_title = json["title"]["value"]
        except KeyError:
            raise KeyError("Could not find title")
        try:
            self.snippet = json["snippet"]["value"]
        except KeyError:
            raise KeyError("Could not find snippet")
        self.language_code = lexemelanguage.language_code
        # try:
        #     # self.date = datetime.strptime(json["datum"], "%d%m%Y")
        #     self.date = datetime.strptime(json["datum"][0:10], "%Y-%m-%d")
        # except KeyError:
        #     raise KeyError("Could not find id")

    def __str__(self):
        return f"{self.document_title}: {self.snippet}"

    def find_form_representation_in_summary(self, word):
        logger = logging.getLogger(__name__)
        if word in self.summary:
            inexact_hit = True
            if f" {word} " in self.summary or f">{word}<" in self.summary:
                self.exact_hit = True
                if config.debug_summaries:
                    logging.debug(
                        f"found word_spaces or word_angle_parens in {self.summary}"
                    )
            else:
                if config.debug_summaries:
                    logging.info("No exact hit in summary. Skipping.")
        # else:
        #     if config.debug_summaries and added is False:
        #         print(f"'{word}' not found as part of a word or a " +
        #               "word in the summary. Skipping")

    def find_usage_examples_from_summary(
            self,
            form: Form = None,
    ) -> List[UsageExample]:
        """This tries to find and clean sentences and return the shortest one"""
        if form is None:
            raise ValueError("form was None")
        logger = logging.getLogger(__name__)
        examples = []
        # find sentences
        # order in a list by length
        # pick the shortest one where the form representation appears
        if self.language_code == WikimediaLanguageCode.ENGLISH:
            logger.info("using the English spaCy pipeline")
            nlp = English()
            nlp.add_pipe('sentencizer')
        elif self.language_code == WikimediaLanguageCode.SWEDISH:
            nlp = Swedish()
        else:
            raise NotImplementedError(f"Sentence extraction for {self.language_code.name} "
                                      f"is not supported yet, feel free to open an issue at "
                                      f"https://github.com/dpriskorn/LexUtils/issues")
        doc = nlp(self.snippet)
        for sentence in doc.sents:
            logger.info(sentence.text)
            # This is a very crude test for relevancy
            if form.representation in sentence.text:
                examples.append(UsageExample(sentence=sentence.text, record=self))
        #print("debug exit")
        #exit(0)
        return examples

    def lookup_qid(self):
        #  https://stackoverflow.com/questions/37024807/how-to-get-wikidata-id-for-an-wikipedia-article-by-api
        logger = logging.getLogger(__name__)
        if self.language_code is None:
            raise ValueError("language was None")
        if self.document_title is None:
            raise ValueError("document_title was None")
        url = (f"https://{self.language_code.value}.wikisource.org/w/api.php?"
               f"action=query&prop=pageprops&ppprop=wikibase_item&"
               f"redirects=1&titles={self.document_title}")
        response = requests.get(url)
        if response.status_code == 200:
            logger.info(response.text)
        else:
            raise ValueError(f"Got {response.status_code} from the Wikisource API, see {url}")

    def url(self):
        return f"{self.language_code.value}.wikisource.org/wiki/{self.document_title}"