import os

# Add your botpassword and login here:
username = ""
password = ""

# Global settings
version = "0.2-alpha"  # Don't touch this.
sleep_time = 5
wd_prefix = "http://www.wikidata.org/entity/"
user_agent = f"LexUtils/{version}"

# Settings for UsageExamples
number_of_forms_to_fetch = 50
sparql_results_size = 40
sparql_offset = 1000
ksamsok_max_results_size = 500  # keep to multiples of 50
riksdagen_max_results_size = 500  # keep to multiples of 20
wikisource_max_results_size = 25
min_word_count = 5
max_word_count = 15
show_sense_urls = True  # Useful for improving the gloss in WD
show_lexeme_urls = True  # Useful for improving the lexeme in WD
exclude_list = "exclude_list.json"

# Global variables
login_instance = None

# Debug
debug_summaries = False