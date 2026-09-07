from typing import List

from pydantic import BaseModel


class ModelSessionParams(BaseModel):
    dataset_id: int
    task_name: str
    name: str
    input_columns: List[str]
    output_columns: List[str]
    train_metrics: List[str]
    validation_metrics: List[str]
    test_metrics: List[str]
    evaluation_strategy: str
    splits: str


class ColumnsValidationParams(BaseModel):
    task_name: str
    dataset_id: int
    inputs_columns: List[str]
    outputs_columns: List[str]


class ModelSessionBulkDeleteParams(BaseModel):
    ids: List[int]
