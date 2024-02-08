from typing import List

from pydantic import BaseModel

from DashAI.back.core.enums.plugin_tags import PluginTag


class TagParams(BaseModel):
    name: PluginTag


class PluginParams(BaseModel):
    name: str
    author: str
    tags: List[TagParams]
    summary: str
    description: str
    description_content_type: str
