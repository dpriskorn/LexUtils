import os

# Add your credentials from the botpasswords page to your ~/.bashrc or below as
# strings:
username = os.environ['LEXUTILS_USERNAME']
password = os.environ['LEXUTILS_PASSWORD']

# Settings for LexUse
sparql_results_size = 10
sparql_offset = 1000
riksdagen_max_results_size = 500  # keep to multiples of 20
ksamsok_max_results_size = 500  # keep to multiples of 50
language = "swedish"
language_code = "sv"
language_qid = "Q9027"
min_word_count = 5
max_word_count = 15
show_sense_urls = True
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
