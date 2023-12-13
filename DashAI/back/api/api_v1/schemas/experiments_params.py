from typing import List

from pydantic import BaseModel


class ExperimentParams(BaseModel):
    dataset_id: int
    task_name: str
    name: str
    input_columns: str
    output_columns: str
    splits: str


class ColumnsValidationParams(BaseModel):
    task_name: str
    dataset_id: int
    inputs_columns: List[int]
    outputs_columns: List[int]
