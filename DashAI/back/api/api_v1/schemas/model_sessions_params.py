from typing import List, Optional

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
    # With preprocessing, the type of every input ref is taken from the
    # chain's estimated structure (see infer_structure).
    preprocessing: Optional[List[ConverterStep]] = None


class PreprocessingStructureParams(BaseModel):
    dataset_id: int
    # Original columns the user may feed into the chain.
    candidates: List[str]
    output_columns: List[str]
    steps: List[ConverterStep] = Field(default_factory=list)


class ModelSessionBulkDeleteParams(BaseModel):
    ids: List[int]
