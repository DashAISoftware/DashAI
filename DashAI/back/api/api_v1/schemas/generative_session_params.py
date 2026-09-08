from typing import List, Union

from pydantic import BaseModel


class GenerativeSessionParams(BaseModel):
    model_name: str
    task_name: str
    parameters: dict
    name: str
    description: Union[str, None] = None


class GenerativeSessionBulkDeleteParams(BaseModel):
    ids: List[int]
