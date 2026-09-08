from typing import Literal

from pydantic import BaseModel, ConfigDict


class JobParams(BaseModel):
    model_config = ConfigDict(extra="allow")

    job_type: Literal[
        "ModelJob",
        "ModelVisualizationJob",
        "ExplainerJob",
        "PredictJob",
        "DatasetJob",
        "ExplorerJob",
        "ConverterJob",
        "GenerativeJob",
        "PipelineJob",
        "RAGJob",
    ]
    kwargs: dict
