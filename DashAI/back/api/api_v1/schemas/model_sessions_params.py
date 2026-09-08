from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, field_validator


class ColumnAtom(BaseModel):
    """A selectable unit in the session wizard: either a literal column of
    the raw dataset, or the whole output group (one declared slot) of a
    converter already configured earlier in the same converters list.

    A `group` atom always selects the entire slot: there is no way to pick
    a subset of a slot's real columns, since their exact names/count are
    not known until the real fit runs (see the design spec, section B).
    """

    kind: Literal["column", "group"]
    name: Optional[str] = None
    converter_id: Optional[str] = None
    slot: Optional[int] = None


def _coerce_atom(value: Any) -> Any:
    """Coerce a bare column-name string into a literal `column` atom.

    Kept for backward compatibility: callers that predate the atom-based
    column scope (e.g. `input_columns=["SepalLengthCm"]`) still POST plain
    strings. Anything that isn't a string (a dict, or an already-built
    `ColumnAtom`) is passed through unchanged for pydantic to validate
    normally.
    """
    if isinstance(value, str):
        return ColumnAtom(kind="column", name=value)
    return value


class SessionConverterParams(BaseModel):
    id: str
    converter: str
    params: Dict[str, Any] = {}
    input_scope: List[ColumnAtom] = []
    target_column: Optional[str] = None

    @field_validator("input_scope", mode="before")
    @classmethod
    def _coerce_input_scope(cls, value: Any) -> Any:
        if isinstance(value, list):
            return [_coerce_atom(item) for item in value]
        return value


class UpdateConvertersParams(BaseModel):
    converters: List[SessionConverterParams] = []


class ModelSessionParams(BaseModel):
    dataset_id: int
    task_name: str
    name: str
    input_columns: List[ColumnAtom] = []
    output_columns: List[ColumnAtom] = []
    train_metrics: List[str]
    validation_metrics: List[str]
    test_metrics: List[str]
    evaluation_strategy: str
    splits: str
    converters: List[SessionConverterParams] = []

    @field_validator("input_columns", "output_columns", mode="before")
    @classmethod
    def _coerce_columns(cls, value: Any) -> Any:
        if isinstance(value, list):
            return [_coerce_atom(item) for item in value]
        return value


class ColumnsValidationParams(BaseModel):
    task_name: str
    dataset_id: int
    inputs_columns: List[str]
    outputs_columns: List[str]
    model_session_id: Optional[int] = None


class ModelSessionBulkDeleteParams(BaseModel):
    ids: List[int]
