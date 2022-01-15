from enum import auto, Enum


class SupportedExampleSources(Enum):
    WIKISOURCE = "Q15156406"
    RIKSDAGEN = "Q21592569"
    HISTORICAL_ADS = "Q110544812"


class SupportedFormPickles(Enum):
    """These enable a persitent memory which help
    avoid working on the same form twice"""
    FINISHED_FORMS = "finished_forms.pkl"
    DECLINED_FORMS = "declined_forms.pkl"


class LanguageStyle(Enum):
    FORMAL = "Q104597585"
    INFORMAL = "Q901711"


class ReferenceType(Enum):
    WRITTEN = "Q47461344"
    ORAL = "Q52946"


class ReturnValues(Enum):
    ACCEPT_USAGE_EXAMPLE = auto()
    # Todo improve this by using a custom error type instead
    ERROR = auto()
    SKIP_FORM = auto()
    SKIP_USAGE_EXAMPLE = auto()
    USAGE_EXAMPLE_ADDED = auto()
