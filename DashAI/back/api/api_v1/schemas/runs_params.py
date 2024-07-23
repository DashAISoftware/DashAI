from typing import Union

from pydantic import BaseModel


class RunParams(BaseModel):
    experiment_id: int
    model_name: str
    name: str
    parameters: dict
    optimizer_name: str
    optimizer_parameters: dict
    description: Union[str, None] = None
