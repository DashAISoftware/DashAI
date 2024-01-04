from typing import Union, Literal

from pydantic import BaseModel, ConfigDict


class JobParams(BaseModel):
    model_config = ConfigDict(extra="allow")

    job_type: Union[Literal["ModelJob"], Literal["ConverterJob"]]
    kwargs: dict
