from lexutils.models.record import Record


class UsageExample:
    # This contains the example, usually a single sentence
    text: str
    record: Record
    word_count: int = None

    def __init__(self, sentence: str, record: Record):
        try:
            self.text = sentence
            self.word_count = len(self.text.split(" "))
        except:
            raise Exception("Missing sentence")
        try:
            self.record = record
        except:
            raise Exception("Missing record")
