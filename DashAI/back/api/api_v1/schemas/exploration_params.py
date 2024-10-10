from datetime import datetime

from pydantic import BaseModel


class ExplorationBase(BaseModel):
    name: str
    description: str


class ExplorationCreate(ExplorationBase):
    dataset_id: int


class Exploration(ExplorationBase):
    id: int
    dataset_id: int
    created: datetime
    last_modified: datetime
