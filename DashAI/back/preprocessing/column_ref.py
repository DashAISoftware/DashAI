"""Column references used by session-level preprocessing.

A ColumnRef identifies either a real column already present in a dataset
(RawColumnRef) or the not-yet-materialized output of a converter step in a
ConverterSequence (GroupColumnRef). Group references let the Models-module
wizard offer "whatever this converter produces" as an input column before
any fit has happened — the concrete names only exist once the
PreprocessingJob has fit the sequence (see session_preprocessor.py).
"""

from typing import Any, Dict, List, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter
from typing_extensions import Annotated


class RawColumnRef(BaseModel):
    kind: Literal["raw"] = "raw"
    name: str


class GroupColumnRef(BaseModel):
    kind: Literal["group"] = "group"
    step: int


ColumnRef = Annotated[Union[RawColumnRef, GroupColumnRef], Field(discriminator="kind")]

_ColumnRefListAdapter = TypeAdapter(List[ColumnRef])


class ConverterStep(BaseModel):
    converter: str
    params: Dict[str, Any] = Field(default_factory=dict)
    scope: List[ColumnRef] = Field(default_factory=list)


class ConverterSequence(BaseModel):
    steps: List[ConverterStep] = Field(default_factory=list)

    def validate_scopes(self) -> None:
        """Raise ValueError if any step's scope references itself or a later step.

        A step may only reference the output group of a step strictly before
        it — this is what makes chaining acyclic without a separate graph
        structure.
        """
        for index, step in enumerate(self.steps):
            for ref in step.scope:
                if isinstance(ref, GroupColumnRef) and ref.step >= index:
                    raise ValueError(
                        f"Step {index} ('{step.converter}') scope references "
                        f"step {ref.step}, which is not strictly before it."
                    )


def resolve_refs(
    refs: List[Union[RawColumnRef, GroupColumnRef]],
    resolved_columns: Dict[int, List[str]],
) -> List[str]:
    """Flatten a list of ColumnRef into concrete column names.

    Parameters
    ----------
    refs : list of RawColumnRef | GroupColumnRef
        References to resolve, in the order they should appear in the result.
    resolved_columns : dict
        Maps a ConverterSequence step index to the concrete column names that
        step produced in one specific fit (see SessionPreprocessor).

    Returns
    -------
    list of str
        Concrete column names, in order. A GroupColumnRef expands to every
        column its step produced.

    Raises
    ------
    KeyError
        If a GroupColumnRef names a step with no entry in resolved_columns
        (the step has not been fit yet).
    """
    names: List[str] = []
    for ref in refs:
        if ref.kind == "raw":
            names.append(ref.name)
        else:
            names.extend(resolved_columns[ref.step])
    return names


def parse_column_refs(raw: List[dict]) -> List[Union[RawColumnRef, GroupColumnRef]]:
    """Parse a list of plain dicts (as stored in JSON columns) into ColumnRef."""
    return _ColumnRefListAdapter.validate_python(raw)
