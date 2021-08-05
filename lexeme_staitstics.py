import logging

from lexutils.models.wikidata import LexemeEngine

logging.basicConfig(level=logging.ERROR)

for language in ["da", "sv", "nb", "en", "fr"]:
    engine = LexemeEngine(language)
    senses = engine.count_number_of_senses_with_P5137()
    lexemes = engine.count_number_of_lexemes()
    print(f"{engine.language_code.name} has "
          f"{senses} senses total on {lexemes} lexemes "
          f"which is {round(senses / lexemes, 2)} senses per lexeme.")
