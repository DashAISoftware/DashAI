from typing import List

from pydantic import BaseModel


class ExperimentParams(BaseModel):
    dataset_id: int
    task_name: str
    name: str
    input_columns: List[int]
    output_columns: List[int]
    splits: str
