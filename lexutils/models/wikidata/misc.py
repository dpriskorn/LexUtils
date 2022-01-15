from __future__ import annotations

from typing import TYPE_CHECKING

from wikibaseintegrator import wbi_config

from lexutils.config import config

if TYPE_CHECKING:
    pass

wbi_config.config['USER_AGENT'] = config.user_agent

# class ForeignID:
#     id: str
#     prop_nr: str  # This is the prop_nr with type ExternalId
#     source_item_id: str  # This is the Q-item for the source
#
#     def __init__(self,
#                  id: str = None,
#                  prop_nr: str = None,
#                  source_item_id: str = None):
#         self.id = id
#         self.prop_nr = str(EntityID(prop_nr))
#         self.source_item_id = str(EntityID(source_item_id))
