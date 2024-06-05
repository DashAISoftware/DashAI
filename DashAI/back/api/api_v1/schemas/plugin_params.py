from typing import List

from pydantic import BaseModel

from DashAI.back.core.enums.plugin_tags import PluginTag
from DashAI.back.core.enums.status import PluginStatus


class TagParams(BaseModel):
    name: PluginTag


class PluginParams(BaseModel):
    name: str
    author: str
    tags: List[TagParams]
    summary: str
    description: str
    description_content_type: str


class PluginUpdateParams(BaseModel):
    old_status: PluginStatus
    new_status: PluginStatus
