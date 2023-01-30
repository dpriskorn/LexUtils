import logging

from lexutils.enums import (
    BaseURLs,
    LanguageStyle,
    ReferenceType,
    SupportedExampleSources,
)
from lexutils.models.record import Record
from lexutils.models.wikidata.enums import WikimediaLanguageCode

logger = logging.getLogger(__name__)


class HistoricalJobAd(Record):
    base_url = BaseURLs.ARBETSFORMEDLINGEN_HISTORICAL_ADS.value
    language_style = LanguageStyle.FORMAL
    type_of_reference = ReferenceType.WRITTEN
    source = SupportedExampleSources.HISTORICAL_ADS
    # TODO is not present in the dataset unfortunately but we check during preprocessing
    # so the number of english sentences should be very few
    language_code = WikimediaLanguageCode.SWEDISH

    def url(self):
        """This shadows the function in Record
        We don't have a URL formatter for the ids in Historical Ads.
        The url to the dumpfile is the least bad we have"""
        return self.base_url
