"""Shared "load raw dataset, prepare for task, instantiate splitter" logic.

Used by both `ModelJob` (training a single Run) and `SessionPreprocessingJob`
(fitting/transforming session converters once, ahead of any Run). Kept in its
own module so neither job has to import from the other.
"""

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from DashAI.back.dependencies.database.models import Dataset, ModelSession
from DashAI.back.job.base_job import JobError
from DashAI.back.splitters.base_splitter import BaseSplitter
from DashAI.back.tasks.base_task import BaseTask

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
    from DashAI.back.dependencies.registry import ComponentRegistry

log = logging.getLogger(__name__)


def _atom_names_if_all_columns(atoms) -> Optional[List[str]]:
    """Return the literal names if every atom is a raw-column reference,
    or None if any atom is a group reference (unresolvable before any
    converter has run for real).

    Plain strings are also accepted alongside `ColumnAtom` dicts: some
    callers (tests building a `ModelSession` directly, older persisted
    sessions) still store `input_columns`/`output_columns` as flat
    `List[str]`, since the DB column itself is untyped JSON. A bare string
    is unambiguously a raw-column reference.
    """
    names = []
    for atom in atoms:
        if isinstance(atom, str):
            names.append(atom)
            continue
        if atom.get("kind") != "column":
            return None
        names.append(atom["name"])
    return names


NO_OUTPUT_PLACEHOLDER_COLUMN = "__no_output_placeholder__"
"""Reserved column name used as `Y` when a session has no output columns yet
(the wizard's Preprocessing step comes before its Columns step). A
`DashAIDataset` with zero columns always reports zero rows — a
`datasets.Dataset` quirk, `num_rows` isn't derived from the arrow table's
actual row count once there are no columns — so a genuinely empty `Y` can't
track `X`'s row count through the splitter. Callers that persist a session's
preprocessed partitions (`SessionPreprocessingJob`) must strip this column
back out rather than merge it in as a real output column.
"""


def load_dataset_and_splitter(
    model_session: ModelSession,
    db: Any,
    component_registry: "ComponentRegistry",
    splitted_indexes: Optional[Dict[str, Any]] = None,
) -> Tuple["DashAIDataset", "DashAIDataset", BaseSplitter, BaseTask, "DashAIDataset"]:
    """Load a session's raw dataset, prepare it for its task, and build its
    configured splitter, ready to call `.split(X, Y)`.

    Parameters
    ----------
    model_session : ModelSession
        The session whose `dataset_id`, `task_name`, `input_columns`,
        `output_columns`, and `splits` configuration drive this.
    db : Session
        Database session, used to load the `Dataset` row.
    component_registry : ComponentRegistry
        Used to resolve the task and splitter classes by name.
    splitted_indexes : dict, optional
        Previously computed split indices to reuse (e.g. a `Run`'s
        `split_indexes`) instead of letting the splitter recompute them.
        Defaults to None (always recompute).

    Returns
    -------
    tuple
        `(X, Y, splitter, task, prepared_dataset)`: the input/output column
        datasets and the instantiated splitter, ready for
        `splitter.split(X, Y)` — plus the task instance and the (still
        unsplit) task-prepared dataset, since `ModelJob` needs those to
        compute `n_labels` for its `ModelFactory`.

    Raises
    ------
    JobError
        If the dataset, task, or splitter cannot be loaded/resolved.
    """
    from DashAI.back.dataloaders.classes.dashai_dataset import (
        load_dataset,
        select_columns,
    )

    dataset: Dataset = db.get(Dataset, model_session.dataset_id)
    if not dataset:
        raise JobError(f"Dataset {model_session.dataset_id} does not exist in DB.")

    try:
        loaded_dataset: "DashAIDataset" = load_dataset(f"{dataset.file_path}/dataset")
    except Exception as e:
        log.exception(e)
        raise JobError(f"Can not load dataset from path {dataset.file_path}") from e

    try:
        task: BaseTask = component_registry[model_session.task_name]["class"]()
    except Exception as e:
        log.exception(e)
        raise JobError(
            f"Unable to find Task with name {model_session.task_name} in registry"
        ) from e

    def _build_placeholder_xy():
        # No output column chosen yet (the wizard's Preprocessing step comes
        # before its Columns step) — nothing to validate against the task
        # yet, so skip `prepare_for_task` entirely. Treat the whole dataset
        # as X; Y carries only `NO_OUTPUT_PLACEHOLDER_COLUMN` (see its
        # docstring for why a genuinely empty Y can't work here), so the
        # splitter and `apply_session_converters` keep working uniformly. A
        # `SUPERVISED` converter that needs a real target in this state
        # supplies its own `target_column` (see `fit_transform_on_partition`
        # in `execution.py`), pulled out of X directly.
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import (
            DashAIDataset,
            to_dashai_dataset,
        )

        placeholder_prepared = to_dashai_dataset(loaded_dataset)
        try:
            placeholder_x = placeholder_prepared
            placeholder_y = DashAIDataset(
                table=pa.table(
                    {
                        NO_OUTPUT_PLACEHOLDER_COLUMN: pa.array(
                            [0] * len(placeholder_prepared), type=pa.int64()
                        )
                    }
                )
            )
        except Exception as e:
            log.exception(e)
            raise JobError(f"Error selecting columns from dataset {dataset.id}") from e
        return placeholder_x, placeholder_y, placeholder_prepared

    if model_session.output_columns:
        output_atom_names = _atom_names_if_all_columns(model_session.output_columns)
        if output_atom_names is None:
            # `output_columns` includes a `group` reference (a converter's
            # output slot) rather than a raw-column reference — its real
            # names/count aren't known until a real fit runs, so there's
            # nothing to resolve against the raw dataset yet. In practice
            # this is normally unreachable: `SessionPreprocessingJob.run()`
            # already rejects a `group` atom in `output_columns` outright
            # before any real fit happens (a converter-produced target value
            # cannot exist yet at split time). Kept here only as a
            # defensive fallback for any other caller of this function.
            log.info(
                "Falling back to a placeholder split for session %s: "
                "output_columns includes a converter output group, not "
                "resolvable against the raw dataset before a real fit "
                "runs.",
                model_session.id,
            )
            X, Y, prepared_dataset = _build_placeholder_xy()
        else:
            # `input_columns` is used as-is (its own literal selection)
            # whenever that's actually usable against the raw dataset —
            # the common, already-working case (no converters, or
            # converters that don't rename/replace the selected columns).
            # Only fall back to "every raw column except the resolved
            # output" when the literal selection genuinely can't be used
            # here: either it references a converter's `group` output
            # (`_atom_names_if_all_columns` returns `None` for that — the
            # main use case this whole feature exists for, e.g. "use
            # everything BagOfWords produced" as input features), or every
            # atom is a `column` reference but names a column that doesn't
            # exist in the raw dataset (e.g. a converter-produced name).
            # In both fallback cases the content used here doesn't matter:
            # `SessionPreprocessingJob.run()` fully re-narrows X to the
            # real, correct columns after converters run (via
            # `resolve_final_columns`/the group registry) — splitting only
            # needs X's row count to line up with Y's at this step, never
            # correct column identity. A normal literal selection, on the
            # other hand, must be honored exactly (deselecting a raw
            # column, or excluding one the task can't handle, must stay
            # deselected/excluded — not silently overridden).
            input_atom_names = _atom_names_if_all_columns(
                model_session.input_columns or []
            )
            if input_atom_names is None or not set(input_atom_names) <= set(
                loaded_dataset.column_names
            ):
                input_atom_names = [
                    col
                    for col in loaded_dataset.column_names
                    if col not in output_atom_names
                ]
            try:
                prepared_dataset = task.prepare_for_task(
                    dataset=loaded_dataset,
                    input_columns=input_atom_names,
                    output_columns=output_atom_names,
                )
                X, Y = select_columns(
                    prepared_dataset,
                    input_atom_names,
                    output_atom_names,
                )
            except Exception as e:
                if not model_session.converters:
                    log.exception(e)
                    raise JobError(
                        f"""Can not prepare Dataset {dataset.id}
                        for Task {model_session.task_name}""",
                    ) from e
                # The attempted *input* selection above is what usually
                # fails here, not the output one: when it's the broad
                # "every raw column except the output" fallback, it
                # necessarily drags in every task-incompatible raw column
                # too (a free-text column a `BagOfWordsConverter` exists
                # precisely to consume, say), and `prepare_for_task` rejects
                # the whole call over it. Retry validating the *output*
                # column alone — the same `input_columns=[]` trick
                # `ModelJob` already uses around its own `prepare_for_task`
                # call for the same reason — before giving up: the real,
                # perfectly valid target must not be silently replaced by
                # the all-zero placeholder just because some unrelated raw
                # column can't be a task input in its raw form. `X` is still
                # built from the same column selection, and this function's
                # `X` is only used for row-index bookkeeping when converters
                # are present anyway (see the placeholder note below).
                try:
                    prepared_dataset = task.prepare_for_task(
                        dataset=loaded_dataset,
                        input_columns=[],
                        output_columns=output_atom_names,
                    )
                    X, Y = select_columns(
                        prepared_dataset,
                        input_atom_names,
                        output_atom_names,
                    )
                    log.info(
                        "Session %s: input_columns don't validate against the "
                        "task in their raw form (converters consume them "
                        "separately); kept the real output column and skipped "
                        "raw input validation: %s",
                        model_session.id,
                        e,
                    )
                except Exception as output_only_error:
                    # A converter can rename/replace a raw column in a way
                    # that makes it an invalid task input in its raw form
                    # (e.g. BagOfWords reading free text no task declares as
                    # a valid input type) — this function's result is only
                    # used for row-index bookkeeping in that case; callers
                    # that need the real, typed prepared dataset when
                    # converters are present must load it from the
                    # preprocessed partitions instead (see
                    # `load_preprocessed_reference_dataset` in
                    # `session_preprocessing_job.py`).
                    log.info(
                        "Falling back to a placeholder split for session %s: "
                        "output_columns doesn't resolve against the raw "
                        "dataset (likely converter-produced): %s",
                        model_session.id,
                        output_only_error,
                    )
                    X, Y, prepared_dataset = _build_placeholder_xy()
    else:
        X, Y, prepared_dataset = _build_placeholder_xy()

    try:
        splits_data = json.loads(model_session.splits)
        if splitted_indexes:
            splits_data["splitted_indexes"] = splitted_indexes
    except Exception as e:
        log.exception(e)
        raise JobError(
            f"Can not load splits data from model session {model_session.id}"
        ) from e

    try:
        splitter_name = splits_data.get("splitter_name", None)
        splitter: BaseSplitter = component_registry[splitter_name]["class"](
            splits_data=splits_data,
        )
    except Exception as e:
        log.exception(e)
        raise JobError(
            f"""Unable to find Splitter with name
            {splitter_name} in registry.""",
        ) from e

    return X, Y, splitter, task, prepared_dataset
