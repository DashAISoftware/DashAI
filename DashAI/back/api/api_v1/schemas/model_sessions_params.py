from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from DashAI.back.preprocessing.column_ref import ColumnRef, ConverterStep


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
    preprocessing: List[ConverterStep] = Field(default_factory=list)
    input_column_refs: Optional[List[ColumnRef]] = None


class ColumnsValidationParams(BaseModel):
    task_name: str
    dataset_id: int
    inputs_columns: List[str]
    outputs_columns: List[str]
    input_refs: Optional[List[ColumnRef]] = None
    converter_output_types: Optional[Dict[str, str]] = None


class ModelSessionBulkDeleteParams(BaseModel):
    ids: List[int]
