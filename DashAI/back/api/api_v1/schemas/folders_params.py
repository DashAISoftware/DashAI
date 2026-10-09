from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FolderCreateParams(BaseModel):
    name: str


class FolderUpdateParams(BaseModel):
    name: str


class Folder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created: datetime
    last_modified: datetime
