import logging

from lexutils.helpers.convert_historical_ads_to_pandas import ConvertHistoricalAds

logging.basicConfig(level=logging.INFO, force=True)

cha = ConvertHistoricalAds()
cha.convert()
