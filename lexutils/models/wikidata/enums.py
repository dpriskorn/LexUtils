from enum import Enum


class WikimediaLanguageCode(Enum):
    # TODO this does not scale. Implement lookup and cache
    DANISH = "da"
    SWEDISH = "sv"
    BOKMÅL = "nb"
    NORWEGIAN = "no"
    ENGLISH = "en"
    FRENCH = "fr"
    RUSSIAN = "ru"
    ESTONIAN = "et"
    MALAYALAM = "ml"
    LATIN = "la"
    HEBREW = "he"
    BASQUE = "eu"
    GERMAN = "de"
    BENGALI = "bn"
    CZECH = "cs"
    SPANISH = "es"


class WikimediaLanguageQID(Enum):
    DANISH = "Q9035"
    SWEDISH = "Q9027"
    BOKMÅL = "Q25167"
    ENGLISH = "Q1860"
    FRENCH = "Q150"
    RUSSIAN = "Q7737"
    ESTONIAN = "Q9072"
    MALAYALAM = "Q36236"
    LATIN = "Q397"
    HEBREW = "Q9288"
    BASQUE = "Q8752"
    GERMAN = "Q188"
    BENGALI = "Q9610"
    CZECH = "Q9056"


class WikidataNamespaceLetters(Enum):
    PROPERTY = "P"
    ITEM = "Q"
    LEXEME = "L"
    FORM = "F"
    SENSE = "S"