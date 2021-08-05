from lexutils.models import wikidata


class Example:
    # This contains the example, usually a single sentence
    content: str
    foreign_id: wikidata.ForeignID
