from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict

from DashAI.back.core.enums.status import DatasetStatus


class DatasetParams(BaseModel):
    model_config = ConfigDict(extra="allow")

    dataloader: str
    name: str


class ColumnSpecItemParams(BaseModel):
    type: str
    dtype: str


class ColumnsSpecParams(BaseModel):
    columns: Dict[str, ColumnSpecItemParams]


class DatasetUpdateParams(BaseModel):
    name: str = None
    folder_id: Optional[int] = None


class DatasetBulkDeleteParams(BaseModel):
    ids: List[int]


class DatasetRenameColumnParams(BaseModel):
    old_name: str
    new_name: str


class DatasetUploadFromNotebookParams(BaseModel):
    name: str


class Dataset(BaseModel):
    id: int
    name: str
    created: datetime
    last_modified: datetime
    file_path: str
    status: DatasetStatus
    total_rows: Optional[int] = None
    total_columns: Optional[int] = None
    folder_id: Optional[int] = None


class DatasetCreateParams(BaseModel):
    name: str
    notebook_id: Optional[int] = None


class DatasetColumnEncoderParams(BaseModel):
    encoder: Literal["one_hot", "label"]
