from typing import Union

from pydantic import BaseModel


class GenerativeProcessParams(BaseModel):
    model_name: str
    input_data: str
    parameters: dict
    name: str
    description: Union[str, None] = None
