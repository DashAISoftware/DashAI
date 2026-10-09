"""Estimate the dataset structure along a session's converter chain.

`infer_structure` walks a ConverterSequence without fitting anything: each
step's scope is resolved against the estimated dataset state at that point,
checked against the converter's metadata, and the converter's own
`infer_output_columns` delta is applied the same way SessionPreprocessor
splices real output back into the dataset. The Models-module wizard uses it
to show which columns exist after every step, and session creation uses it
to reject a chain that would reference a column that no longer exists.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from DashAI.back.converters.dataset_columns import plan_new_column_names
from DashAI.back.preprocessing.column_ref import ConverterStep
from DashAI.back.preprocessing.structure_types import (
    BlockItem,
    ColumnItem,
    RowsNotSupportedError,
    StateItem,
    StepStructure,
    StructureDelta,
    StructureMessage,
    StructureResult,
    known_width,
    type_fields,
)
from DashAI.back.splitters.splits_payload import schema_placeholder_defaults


class StructureError(Exception):
    """A chain or ref the estimate rejects, with the message for the frontend."""

    def __init__(self, code: str, **params: Any):
        super().__init__(code)
        self.message = StructureMessage(code=code, params=params)


def _identity(item: StateItem) -> Tuple:
    """What a later delta or ref uses to recognise an item."""
    if isinstance(item, ColumnItem):
        return ("column", item.name)
    return ("block", item.step, item.slot)


def infer_structure(
    dataset_types: Dict[str, Any],
    candidates: List[str],
    target: List[str],
    steps: List[ConverterStep],
    component_registry: Any,
) -> StructureResult:
    """Estimate the dataset state after every step of a converter chain.

    Parameters
    ----------
    dataset_types : dict
        Every dataset column name, in dataset order, mapped to its DashAI
        type.
    candidates : list of str
        The original columns the user may feed into the chain. The initial
        state is these columns, minus the target.
    target : list of str
        The output columns. They never enter the state and no scope may
        reference them.
    steps : list of ConverterStep
        The chain, in order.
    component_registry : ComponentRegistry or mapping
        Resolves a converter name to ``{"class": converter_class}``.

    Returns
    -------
    StructureResult
        The initial state, one entry per step (its status, the state after
        it and what it produced) and the final state. After the first
        invalid step the rest are "blocked" and the final state is the one
        before it.
    """
    target_set = set(target)
    state: List[StateItem] = []
    for name in dataset_types:
        if name in candidates and name not in target_set:
            type_name, dtype = type_fields(dataset_types[name])
            state.append(ColumnItem(name=name, type=type_name, dtype=dtype))
    initial = list(state)
    # The runtime renames a new column against every column of the dataset,
    # not just the candidates, so name clashes are checked against all.
    taken: Set[str] = set(dataset_types)

    results: List[StepStructure] = []
    blocked = False
    for index, step in enumerate(steps):
        if blocked:
            results.append(StepStructure(status="blocked", state=state))
            continue
        try:
            state, added, warnings = _apply_step(
                index, step, state, taken, target_set, component_registry
            )
        except StructureError as e:
            results.append(StepStructure(status="error", state=state, error=e.message))
            blocked = True
            continue
        results.append(
            StepStructure(status="ok", state=state, added=added, warnings=warnings)
        )

    return StructureResult(
        initial=initial,
        steps=results,
        final=state,
        valid=not blocked,
    )


def _apply_step(
    index: int,
    step: ConverterStep,
    state: List[StateItem],
    taken: Set[str],
    target: Set[str],
    component_registry: Any,
) -> Tuple[List[StateItem], List[StateItem], List[StructureMessage]]:
    """Estimate one step. Updates `taken` in place; raises StructureError."""
    try:
        converter_class = component_registry[step.converter]["class"]
    except KeyError as e:
        raise StructureError("unknown_converter", converter=step.converter) from e
    converter = _instantiate(converter_class, step.params)

    scope = resolve_state_refs(step.scope, state, target)
    _check_scope(converter_class, scope)

    warnings: List[StructureMessage] = []
    try:
        delta = converter.infer_output_columns(scope)
    except RowsNotSupportedError as e:
        raise StructureError("rows_not_supported", converter=step.converter) from e
    except ValueError as e:
        # A converter validating its own configuration against the scope
        # (e.g. ColumnArithmetic without a constant for a single column).
        raise StructureError("converter_rejected", detail=str(e)) from e
    except Exception:
        # A converter whose estimate is broken (e.g. an older plugin) falls
        # back to the conservative default: its scope is consumed and its
        # output is one block of unknown size and type.
        delta = StructureDelta(added=[BlockItem()])
        warnings.append(
            StructureMessage(code="inference_fallback", params={"step": index})
        )
    warnings.extend(delta.warnings)
    warnings.extend(_check_bounds(converter_class, converter, scope))
    if delta.drops_unscoped:
        warnings.extend(
            _drop_warnings(
                state, scope, getattr(converter_class, "ROWS_APPLY_TO", None)
            )
        )

    new_state, added = _apply_delta(index, state, scope, delta, taken)
    if delta.drops_unscoped:
        # The runtime replaces the dataset with the step's scope plus the
        # target, so only those names remain taken.
        scope_names = {item.name for item in scope if isinstance(item, ColumnItem)}
        taken.intersection_update(scope_names | target)
    return new_state, added, warnings


def _drop_warnings(
    state: List[StateItem], scope: List[StateItem], rows_apply_to: Optional[str]
) -> List[StructureMessage]:
    """Tell the user where a row-changing step applies and what it drops.

    Used for a step whose output keeps only its scope. A training-only
    resampler ("train") leaves validation, test and prediction rows as they
    are; a row remover ("splits") removes rows on every split but never at
    prediction. Either way every column outside its scope is gone after it.
    """
    first = "train_only" if rows_apply_to == "train" else "rows_removed_in_splits"
    warnings = [StructureMessage(code=first)]
    scope_ids = {_identity(item) for item in scope}
    dropped = [
        item.name if isinstance(item, ColumnItem) else item.label
        for item in state
        if _identity(item) not in scope_ids
    ]
    if dropped:
        warnings.append(
            StructureMessage(code="drops_columns", params={"columns": dropped})
        )
    return warnings


def _instantiate(converter_class: Any, params: Dict[str, Any]) -> Any:
    """Validate the user's params and build the converter with them.

    The params are validated the way the frontend form submits them, with
    every field it seeds from the schema placeholders (as _validate_splits
    does for splitters), but the converter is built from the params exactly
    as given, as SessionPreprocessor builds it, so the estimate describes
    the converter that will really run.
    """
    try:
        schema = getattr(converter_class, "SCHEMA", None)
        if schema is not None:
            schema.model_validate(
                {**schema_placeholder_defaults(converter_class), **params}
            )
        return converter_class(**params)
    except Exception as e:
        raise StructureError("invalid_params", detail=str(e)) from e


def resolve_state_refs(
    refs: List[Any], state: List[StateItem], target: Set[str]
) -> List[StateItem]:
    """Map ColumnRefs to the dataset state items they point at.

    Parameters
    ----------
    refs : list of RawColumnRef | GroupColumnRef
        The refs to resolve, e.g. a step's scope or the model inputs.
    state : list of ColumnItem | BlockItem
        The estimated dataset state to resolve them against.
    target : set of str
        The output columns, which no ref may point at.

    Returns
    -------
    list of ColumnItem | BlockItem
        The items, in ref order, without duplicates.

    Raises
    ------
    StructureError
        With code "target_in_scope" for a ref to the target, or
        "missing_ref" for a ref to something that does not exist (anymore).
    """
    scope: List[StateItem] = []
    seen: Set[Tuple] = set()
    for ref in refs:
        if ref.kind == "raw":
            if ref.name in target:
                raise StructureError("target_in_scope", column=ref.name)
            matches = [
                item
                for item in state
                if isinstance(item, ColumnItem)
                and item.origin is None
                and item.name == ref.name
            ]
            label = ref.name
        elif ref.name is not None:
            matches = [
                item
                for item in state
                if isinstance(item, ColumnItem)
                and item.origin == ref.step
                and item.name == ref.name
            ]
            label = ref.name
        elif ref.slot is not None:
            matches = [
                item
                for item in state
                if isinstance(item, BlockItem)
                and item.step == ref.step
                and item.slot == ref.slot
            ]
            label = f"{ref.step}:{ref.slot}"
        else:
            # Whole group: everything the step produced that still exists.
            matches = [
                item
                for item in state
                if (isinstance(item, ColumnItem) and item.origin == ref.step)
                or (isinstance(item, BlockItem) and item.step == ref.step)
            ]
            label = str(ref.step)
        if not matches:
            raise StructureError("missing_ref", ref=label)
        for item in matches:
            if _identity(item) not in seen:
                seen.add(_identity(item))
                scope.append(item)
    return scope


def _check_scope(converter_class: Any, scope: List[StateItem]) -> None:
    """Apply the converter's declared column restrictions to its scope.

    Mirrors the frontend's evaluateColumnEligibility: empty allow-lists mean
    no restriction. An item of unknown type is let through, since only the
    fit can tell.
    """
    metadata = converter_class.get_metadata()
    allowed_types = metadata.get("allowed_types") or []
    allowed_dtypes = metadata.get("allowed_dtypes") or []
    non_allowed_dtypes = metadata.get("non_allowed_dtypes") or []
    for item in scope:
        if item.type is None:
            continue
        if (
            (allowed_types and item.type not in allowed_types)
            or (allowed_dtypes and item.dtype not in allowed_dtypes)
            or (item.dtype in non_allowed_dtypes)
        ):
            raise StructureError(
                "type_not_allowed",
                column=item.name if isinstance(item, ColumnItem) else item.label,
                type=item.type,
                allowed=allowed_types,
            )

    cardinality = metadata.get("input_cardinality") or {}
    # A block of unknown size holds at least one column.
    at_least = sum(
        1 if isinstance(item, ColumnItem) else (item.count or 1) for item in scope
    )
    exactly = known_width(scope)
    required = cardinality.get("exact")
    minimum = required if required is not None else cardinality.get("min")
    maximum = required if required is not None else cardinality.get("max")
    too_few = minimum is not None and (exactly or at_least) < minimum
    too_many = maximum is not None and exactly is not None and exactly > maximum
    if too_few or too_many:
        raise StructureError(
            "cardinality",
            min=minimum,
            max=maximum,
            selected=exactly if exactly is not None else at_least,
        )


def _check_bounds(
    converter_class: Any, converter: Any, scope: List[StateItem]
) -> List[StructureMessage]:
    """Check `n_components` against the scope width, for projections.

    Only converters flagged N_COMPONENTS_FEATURES_BOUNDED (the PCA family)
    cannot output more components than input columns; kernel approximations
    can.
    """
    n_components = getattr(converter, "n_components", None)
    if not getattr(converter_class, "N_COMPONENTS_FEATURES_BOUNDED", False):
        return []
    if not isinstance(n_components, int) or isinstance(n_components, bool):
        return []
    width = known_width(scope)
    if width is None:
        return [
            StructureMessage(
                code="count_unknown_bound", params={"n_components": n_components}
            )
        ]
    if n_components > width:
        raise StructureError(
            "n_components_exceeds", n_components=n_components, columns=width
        )
    return []


def _apply_delta(
    index: int,
    state: List[StateItem],
    scope: List[StateItem],
    delta: StructureDelta,
    taken: Set[str],
) -> Tuple[List[StateItem], List[StateItem]]:
    """Apply a converter's delta to the state, as the runtime splices output.

    Surviving scope items stay in place (maybe retyped), consumed ones are
    dropped, and new items are appended at the end with runtime names: a
    new column whose name is taken is renamed like
    rebuild_dataset_with_transformed_columns does.
    """
    concrete = [item for item in delta.added if isinstance(item, ColumnItem)]
    blocks = [item for item in delta.added if isinstance(item, BlockItem)]
    if concrete and blocks:
        raise ValueError(
            f"Step {index} mixes concrete columns and blocks in one delta."
        )

    scope_ids = {_identity(item) for item in scope}
    kept = {_identity(item): item for item in delta.kept}
    new_state: List[StateItem] = []
    removed_names: List[str] = []
    for item in state:
        item_id = _identity(item)
        if item_id not in scope_ids:
            if not delta.drops_unscoped:
                new_state.append(item)
        elif item_id in kept:
            new_state.append(kept[item_id])
        elif isinstance(item, ColumnItem):
            removed_names.append(item.name)

    # A step that outputs blocks may keep some consumed columns under their
    # own names (a selector keeps a subset), so their names stay taken.
    if not blocks:
        taken.difference_update(removed_names)

    added: List[StateItem] = []
    if concrete:
        final_names = plan_new_column_names(taken, [item.name for item in concrete])
        for item in concrete:
            added.append(
                item.model_copy(
                    update={"name": final_names[item.name], "origin": index}
                )
            )
        taken.update(final_names.values())
    else:
        # A single block is the step's whole group (a ref with no slot);
        # several are told apart by type, as the runtime classifies them.
        for block in blocks:
            added.append(
                block.model_copy(
                    update={
                        "step": index,
                        "slot": block.type if len(blocks) > 1 else None,
                    }
                )
            )

    return new_state + added, added
