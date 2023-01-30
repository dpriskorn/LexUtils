from enum import Enum, auto


class BaseURLs(Enum):
    RIKSDAGEN = "https://data.riksdagen.se/dokument/"
    ARBETSFORMEDLINGEN_HISTORICAL_ADS = (
        "https://data.jobtechdev.se/annonser/historiska/2021.zip"
    )


class SupportedPicklePaths(Enum):
    RIKSDAGEN = "data/sv/riksdagen.pkl.gz"
    ARBETSFORMEDLINGEN_HISTORICAL_ADS = "data/sv/historical_ads.pkl.gz"


class SupportedExampleSources(Enum):
    WIKISOURCE = "Q15156406"
    RIKSDAGEN = "Q21592569"
    HISTORICAL_ADS = "Q110544812"


class SupportedLexutilsFormPickles(Enum):
    """These enable a persistent memory which help
    avoid working on the same form twice"""

    FINISHED_FORMS = "finished_forms.pkl"
    DECLINED_FORMS = "declined_forms.pkl"


class LanguageStyle(Enum):
    FORMAL = "Q104597585"
    INFORMAL = "Q901711"


class ReferenceType(Enum):
    WRITTEN = "Q47461344"
    ORAL = "Q52946"


class ReturnValue(Enum):
    ACCEPT_USAGE_EXAMPLE = auto()
    # Todo improve this by using a custom error type instead
    ERROR = auto()
    SKIP_FORM = auto()
    SKIP_USAGE_EXAMPLE = auto()
    USAGE_EXAMPLE_ADDED = auto()
