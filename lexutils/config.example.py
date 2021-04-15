import os

# Add your botpassword and login here:
username = ""
password = ""

# Global settings
version = "0.1"  # Don't touch this.
sleep_time = 5

# Settings for LexUse
use_dataframes = False
sparql_results_size = 40
sparql_offset = 1000
riksdagen_max_results_size = 500  # keep to multiples of 20
ksamsok_max_results_size = 500  # keep to multiples of 50
language = "swedish"
language_code = "sv"
language_qid = "Q9027"
min_word_count = 5
max_word_count = 15
show_sense_urls = True  # Useful for improving the gloss in WD
show_lexeme_urls = True  # Useful for improving the lexeme in WD
exclude_list = "exclude_list.json"

# Debug settings
debug = False
debug_duplicates = False
debug_excludes = False
debug_exclude_list = False
debug_json = False
debug_riksdagen = False
debug_senses = False
debug_sentences = False
debug_summaries = False

# Global variables
login_instance = None
loglevel = None
