"""Types describing the estimated structure of a dataset during preprocessing.

The Models-module wizard needs to know which columns (and of which type)
exist at every point of a session's converter chain before anything is
fit. Each converter describes what it does to its scope through
``BaseConverter.infer_output_columns``, which returns a StructureDelta over
these state items; ``infer_structure`` (structure.py) applies the deltas step
by step.

A state item is either a concrete column, whose name is known ahead of any
fit, or a symbolic block: columns whose names (and sometimes count) only
exist once the converter is fit, e.g. one-hot columns, one per category.
"""

from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, Field
from typing_extensions import Annotated


class RowsNotSupportedError(Exception):
    """Raised by a converter that changes the dataset's row count.

    Session preprocessing does not support these converters yet: resampling
    must run on the training partition only and carry the target along,
    which the session preprocessor does not do.
    """


class ColumnItem(BaseModel):
    kind: Literal["column"] = "column"
    name: str
    # A DashAI type's display_name(), e.g. "Integer". None means unknown.
    type: Optional[str] = None
    dtype: Optional[str] = None
    # None for an original dataset column (even after being replaced in
    # place); otherwise the index of the step that created it.
    origin: Optional[int] = None


class BlockItem(BaseModel):
    kind: Literal["block"] = "block"
    # Index of the step that produced the block, filled by infer_structure.
    step: int = -1
    # The slot a GroupColumnRef uses to reference this block. It is fixed
    # when the block is created, while `type` follows later in-place
    # conversions of its columns, mirroring the runtime, where a step's
    # slots are classified once, at that step.
    slot: Optional[str] = None
    label: str = "output"
    type: Optional[str] = None
    dtype: Optional[str] = None
    # Number of columns in the block, or None when it is only known after
    # fit (e.g. one-hot encoding: one column per category).
    count: Optional[int] = None


StateItem = Annotated[Union[ColumnItem, BlockItem], Field(discriminator="kind")]


class StructureMessage(BaseModel):
    # Suffix of the frontend i18n key the message is translated with.
    code: str
    params: Dict[str, Any] = Field(default_factory=dict)


class StructureDelta(BaseModel):
    """What a converter does to the items in its scope.

    Scope items missing from `kept` are removed from the dataset state. A
    kept item keeps its identity (a column's name, a block's step and slot)
    but may carry a new type. `added` are the items the converter creates:
    either all concrete columns or all blocks, never a mix.
    """

    kept: List[StateItem] = Field(default_factory=list)
    added: List[StateItem] = Field(default_factory=list)
    # True for a converter whose output keeps only its scope (e.g. a
    # training-only resampler): every state item outside the scope is gone
    # after the step.
    drops_unscoped: bool = False
    warnings: List[StructureMessage] = Field(default_factory=list)


class StepStructure(BaseModel):
    status: Literal["ok", "error", "blocked"]
    # Dataset state after this step.
    state: List[StateItem] = Field(default_factory=list)
    # Items this step produced.
    added: List[StateItem] = Field(default_factory=list)
    error: Optional[StructureMessage] = None
    warnings: List[StructureMessage] = Field(default_factory=list)


class StructureResult(BaseModel):
    initial: List[StateItem]
    steps: List[StepStructure]
    final: List[StateItem]
    valid: bool


def known_width(items: List[StateItem]) -> Optional[int]:
    """Return how many real columns the items stand for, if that is known.

    A concrete column counts as one; a block counts as its `count`. None
    when any block's size is only known after fit.
    """
    width = 0
    for item in items:
        if isinstance(item, ColumnItem):
            width += 1
        elif item.count is None:
            return None
        else:
            width += item.count
    return width


def type_fields(dashai_type: Any) -> Tuple[Optional[str], Optional[str]]:
    """Return the (display name, dtype) pair the frontend shows for a type.

    Parameters
    ----------
    dashai_type : DashAIDataType or None
        The type to describe.

    Returns
    -------
    tuple of (str or None, str or None)
        The type's display_name() and its storage dtype (e.g. "int64"),
        each None when unknown.
    """
    if dashai_type is None:
        return None, None
    name = (
        dashai_type.display_name()
        if hasattr(dashai_type, "display_name")
        else type(dashai_type).__name__
    )
    dtype = None
    if hasattr(dashai_type, "to_string"):
        description = dashai_type.to_string()
        if isinstance(description, dict):
            dtype = description.get("dtype")
    return name, dtype
