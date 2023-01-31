import logging

# Add your botpassword and login here:
from lexutils.models.wikidata.enums import WikimediaLanguageCode

username = ""
password = ""

# Global settings
sleep_time = 5
wd_prefix = "http://www.wikidata.org/entity/"
user_agent = f"LexUtils"

# Global settings
loglevel = logging.INFO

# Settings for UsageExamples
sense_gloss_fallback_language_one = "nb"
sense_gloss_fallback_language_two = "en"
require_form_confirmation = True
fast_nlp_languages = [WikimediaLanguageCode.SWEDISH, WikimediaLanguageCode.ENGLISH]
number_of_forms_to_fetch = 20
ksamsok_max_results_size = 500  # keep to multiples of 50
riksdagen_max_results_size = 500  # keep to multiples of 20
wikisource_max_results_size_fast_nlp = 50
wikisource_max_results_size_slow_nlp = 20
historical_ads_max_results_size = 200
min_word_count = 5
max_word_count = 15
show_sense_urls = True  # Useful for improving the gloss in WD
show_lexeme_urls = True  # Useful for improving the lexeme in WD
exclude_list = "exclude_list.json"

# Global variables
login_instance = None

# Debug
debug_summaries = False
