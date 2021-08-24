from datetime import datetime


class Record:
    id: str
    summary: str
    date: datetime
    inexact_hit: bool = False
    exact_hit: bool = False
    line_number = None
    # TODO refactor these to Enum
    language_style = None
    type_of_reference = None
    source = None
