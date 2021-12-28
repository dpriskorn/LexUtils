from lexutils.config import config
from lexutils.models.wikidata.entities import EntityID


class Sense:
    """
    Model for a Wikibase sense
    """
    id: str
    # For now we only support one gloss
    gloss: str

    # statements: List[statement]

    def __init__(self,
                 id: str = None,
                 gloss: str = None):
        self.id = str(EntityID(id))
        self.gloss = gloss.strip()

    def __str__(self):
        return f"{self.id}: {self.gloss}"

    def url(self):
        return f"{config.wd_prefix}{self.id}"