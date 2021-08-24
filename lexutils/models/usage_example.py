from lexutils.models.record import Record


class UsageExample:
    # This contains the example, usually a single sentence
    content: str
    record: Record

    def __init__(self, sentence: str, record: Record):
        try:
            self.content = sentence
        except:
            raise Exception("Missing sentence")
        try:
            self.record = record
        except:
            raise Exception("Missing record")
