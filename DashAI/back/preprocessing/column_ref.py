"""Column references used by session-level preprocessing.

A ColumnRef identifies either a real column already present in a dataset
(RawColumnRef) or the not-yet-materialized output of a converter step in a
ConverterSequence (GroupColumnRef). Group references let the Models-module
wizard offer "whatever this converter produces" as an input column before
any fit has happened — the concrete names only exist once the
PreprocessingJob has fit the sequence (see session_preprocessor.py).
"""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, TypeAdapter
from typing_extensions import Annotated


class RawColumnRef(BaseModel):
    kind: Literal["raw"] = "raw"
    name: str


class GroupColumnRef(BaseModel):
    kind: Literal["group"] = "group"
    step: int
    # None (the default) means "every column step produced" — unchanged,
    # backward-compatible behavior. A converter step's real output columns
    # aren't always one homogeneous type (e.g. SimpleImputer with a scope
    # that mixes categorical and numeric columns just preserves each one's
    # own type), so `slot` lets a ref pick out only the columns of one
    # declared type from that step's output, once a real fit has classified
    # them (see SessionPreprocessor._classify_by_type). The slot name is a
    # DashAI type's display_name(), e.g. "Categorical" or "Integer".
    slot: Optional[str] = None


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
    resolved_slots: Optional[Dict[int, Dict[str, List[str]]]] = None,
) -> List[str]:
    """Flatten a list of ColumnRef into concrete column names.

    Parameters
    ----------
    refs : list of RawColumnRef | GroupColumnRef
        References to resolve, in the order they should appear in the result.
    resolved_columns : dict
        Maps a ConverterSequence step index to the concrete column names that
        step produced in one specific fit (see SessionPreprocessor).
    resolved_slots : dict, optional
        Maps a step index to {type_name: [column names]}, the same step
        output classified by real per-column type (see SessionPreprocessor.
        _classify_by_type). Required only if some ref has a non-None `slot`.

    Returns
    -------
    list of str
        Concrete column names, in order. A GroupColumnRef with `slot=None`
        expands to every column its step produced; with a `slot` set, only
        to that step's columns of that declared type.

    Raises
    ------
    KeyError
        If a GroupColumnRef names a step with no entry in resolved_columns
        (or, for a slot ref, no matching entry in resolved_slots) — the step
        has not been fit yet, or produced no column of that type.
    """
    names: List[str] = []
    for ref in refs:
        if ref.kind == "raw":
            names.append(ref.name)
        elif ref.slot is None:
            names.extend(resolved_columns[ref.step])
        else:
            names.extend((resolved_slots or {})[ref.step][ref.slot])
    return names


def parse_column_refs(raw: List[dict]) -> List[Union[RawColumnRef, GroupColumnRef]]:
    """Parse a list of plain dicts (as stored in JSON columns) into ColumnRef."""
    return _ColumnRefListAdapter.validate_python(raw)
