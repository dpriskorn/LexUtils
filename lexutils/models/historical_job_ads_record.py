from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Any, List, TYPE_CHECKING

from spacy.lang.sv import Swedish

from lexutils.config import config
from lexutils.config.enums import LanguageStyle, ReferenceType, SupportedExampleSources
from lexutils.models.record import Record
from lexutils.models.usage_example import UsageExample
from lexutils.models.wikidata.enums import WikimediaLanguageCode
from lexutils.models.wikidata.form import Form

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class HistoricalJobAd(Record):
    base_url = "https://data.jobtechdev.se/annonser/historiska/2021_first_6_months.zip"
    language_style = LanguageStyle.FORMAL
    type_of_reference = ReferenceType.WRITTEN
    source = SupportedExampleSources.HISTORICAL_ADS
    # TODO is not present in the dataset unfortunately
    language_code = WikimediaLanguageCode.SWEDISH

    def __init__(self, json_data: Any = None):
        if json_data is None:
            raise ValueError("json_data was None")
        else:
            # logger.info("Parsing ad")
            data = json.loads(json_data)
            self.id = data["id"]
            self.date = datetime.strptime(data["publication_date"], "%Y-%m-%dT%H:%M:%S")
            description = data["description"]
            if "text" in description:
                self.text = description["text"]
                # TODO detect language
                # logger.info("Detecting the language")
                # self.language_code = WikimediaLanguageCode(langdetect.detect(self.text))
                # logger.info(f"Detected: {self.language_code.name.title()}")
            else:
                logger.warning("found no text in this ad")

    # TODO improve preprocessing of the dataframe so that we
    #  already have sentences like for the riksdagen data
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
        logger.debug("Splitting the sentences using spaCy")
        nlp = Swedish()
        nlp.add_pipe('sentencizer')
        doc = nlp(self.text)
        sentences = set()
        raw_sentences = list(doc.sents)
        logger.info(f"Got {len(raw_sentences)} sentences from spaCy")
        for sentence in raw_sentences:
            # logger.info(sentence.text)
            # This is a very crude test for relevancy, we lower first to improve matching
            cleaned_sentence = sentence.text.lower()
            punctations = [".", ",", "!", "?", "„", "“", "\n"]
            for punctation in punctations:
                if punctation in cleaned_sentence:
                    cleaned_sentence = cleaned_sentence.replace(punctation, " ")
            logger.debug(f"cleaned sentence:{cleaned_sentence}")
            if f" {form.representation.lower()} " in f" {cleaned_sentence} ":
                # Add to the set first to avoid duplicates
                sentences.add(sentence.text.replace("\n", "").strip())
        logger.info(f"Found {len(sentences)} sentences which contained {form.representation}")
        examples = []
        count_discarded = 0
        for sentence in sentences:
            sentence_length = len(sentence.split(" "))
            if (
                    config.min_word_count < sentence_length < config.max_word_count
            ):
                examples.append(UsageExample(text=sentence, record=self))
            else:
                count_discarded += 1
        if count_discarded > 0:
            logger.info(f"{count_discarded} sentence was discarded based on length")
        # print("debug exit")
        # exit(0)
        return examples

    def url(self):
        """This shadows the function in Record
        We don't have a URL formatter for the ids in Historical Ads.
        The url to the dumpfile is the least bad we have"""
        return self.base_url


