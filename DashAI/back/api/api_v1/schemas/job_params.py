from typing import Literal, Union

from pydantic import BaseModel, ConfigDict


class JobParams(BaseModel):
    model_config = ConfigDict(extra="allow")

    job_type: Union[Literal["ModelJob"], Literal["ConverterJob"]]
    kwargs: dict
