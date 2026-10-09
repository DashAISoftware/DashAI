from datetime import datetime
from typing import List, Union

from pydantic import BaseModel


class NotebookBase(BaseModel):
    name: Union[str, None] = None
    description: Union[str, None] = None


class NotebookCreate(NotebookBase):
    dataset_id: int


class Notebook(NotebookBase):
    id: int
    dataset_id: int
    created: datetime
    last_modified: datetime
    file_path: str


class NotebookUpdateParams(BaseModel):
    name: str = None


class NotebookBulkDeleteParams(BaseModel):
    ids: List[int]
