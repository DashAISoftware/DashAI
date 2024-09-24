from datetime import datetime
from typing import List, Union

from pydantic import BaseModel

from DashAI.back.core.enums.status import ExplorerStatus


class ExplorerBase(BaseModel):
    columns: List[dict]
    exploration_type: str
    parameters: dict
    name: Union[str, None] = None


class ExplorerCreate(ExplorerBase):
    dataset_id: int


class Explorer(ExplorerBase):
    id: int
    dataset_id: int
    created: datetime
    delivery_time: Union[datetime, None] = None
    start_time: Union[datetime, None] = None
    end_time: Union[datetime, None] = None
    exploration_path: Union[str, None] = None
    status: ExplorerStatus
    pinned: bool
