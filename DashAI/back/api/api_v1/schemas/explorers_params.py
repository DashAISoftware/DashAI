from datetime import datetime

from beartype.typing import Any, Dict, List, Union
from pydantic import BaseModel

from DashAI.back.core.enums.status import ExplorerStatus


class ExplorerBase(BaseModel):
    columns: List[Dict[str, Any]]
    parameters: Dict[str, Any]
    name: Union[str, None] = None


class ExplorerCreate(ExplorerBase):
    exploration_id: int
    exploration_type: str


class Explorer(ExplorerBase):
    id: int
    exploration_id: int
    exploration_type: str
    created: datetime
    last_modified: datetime

    delivery_time: Union[datetime, None] = None
    start_time: Union[datetime, None] = None
    end_time: Union[datetime, None] = None
    exploration_path: Union[str, None] = None
    status: ExplorerStatus


class ExplorerResultsOptions(BaseModel):
    options: Union[Dict[str, Any], None] = None
