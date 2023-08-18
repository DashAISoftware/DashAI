from pydantic import BaseModel


class ExperimentParams(BaseModel):
    dataset_id: int
    task_name: str
    name: str
