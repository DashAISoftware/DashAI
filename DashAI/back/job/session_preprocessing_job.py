import logging
import os
import shutil
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from kink import inject
from sqlalchemy import exc

from DashAI.back.converters.execution import (
    apply_session_converters,
    fitted_converters_path,
    save_fitted_converters,
)
from DashAI.back.dependencies.database.models import ModelSession
from DashAI.back.job.base_job import BaseJob, JobError
from DashAI.back.job.dataset_split_utils import (
    NO_OUTPUT_PLACEHOLDER_COLUMN,
    load_dataset_and_splitter,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def merge_input_output_columns(
    x_partition: "DashAIDataset", y_partition: "DashAIDataset"
) -> "DashAIDataset":
    """Combine a partition's input and output columns into a single dataset,
    so it can be saved/loaded as one unit with `save_dataset`/`load_dataset`
    (the same "one combined dataset" shape the raw dataset already has)."""
    from DashAI.back.dataloaders.classes.dashai_dataset import modify_table

    return modify_table(
        x_partition,
        {col: y_partition.arrow_table[col] for col in y_partition.column_names},
        types={col: y_partition.types[col] for col in y_partition.column_names},
    )


def resolve_final_columns(
    atoms: List[dict],
    group_registry: Dict[Tuple[str, int], Dict[int, List[str]]],
    partition_index: int,
) -> List[str]:
    """Resolve the session's own final input/output atom selection
    (`model_session.input_columns`/`output_columns`) to real column names
    for one specific partition, using the same group registry
    `apply_session_converters` built while fitting the converters
    themselves (see the design spec, section E).

    Plain strings are also accepted alongside `{"kind": "column", ...}`
    atoms, for the same backward-compatibility reason
    `dataset_split_utils._atom_names_if_all_columns`/
    `get_real_input_output_columns` already tolerate them: the DB column is
    untyped JSON, and some callers (tests, older persisted sessions) still
    store flat `List[str]`. A bare string is unambiguously a raw-column
    reference.

    Raises
    ------
    JobError
        If a `group` atom's `(converter_id, slot)` never produced any
        columns for this partition index — a typo'd id, a legacy converter
        config missing its own `"id"`, or a converter that produced
        nothing for this fold (e.g. an optional output that isn't
        enabled). Silently falling through to "no columns" here would
        otherwise reach `select_columns([])`, producing a silently
        zero-column dataset with no error — the same gap
        `execution.py`'s `resolve_input_scope` already guards against for
        a converter's own `input_scope`.
    """
    resolved: List[str] = []
    for atom in atoms:
        if isinstance(atom, str):
            resolved.append(atom)
            continue
        if atom["kind"] == "column":
            resolved.append(atom["name"])
        else:
            key = (atom["converter_id"], atom["slot"])
            per_partition = group_registry.get(key, {})
            atom_columns = per_partition.get(partition_index, [])
            if not atom_columns:
                raise JobError(
                    f"Session's final column selection references "
                    f"converter_id={atom['converter_id']!r} "
                    f"slot={atom['slot']!r}, but that group produced no "
                    f"columns for partition index {partition_index}. This "
                    f"usually means a typo'd converter id, a legacy "
                    f'converter config missing its own "id", or a '
                    f"converter that produced nothing for this partition."
                )
            resolved.extend(atom_columns)
    return resolved


def load_preprocessed_session_data(model_session: ModelSession) -> Tuple[Any, Any]:
    """Load the partitions written by `SessionPreprocessingJob.run()` back
    into the `(x, y)` shape `BaseEvaluationStrategy.execute()` expects — a
    single `DatasetDict` for holdout, or a list of `DatasetDict` (one per
    fold, plus a final `full_dataset` entry) for cross-validation.

    Lives alongside the code that writes this layout so both stay in sync.

    Parameters
    ----------
    model_session : ModelSession
        Must have a non-empty `preprocessed_path` (i.e. preprocessing has
        already finished for this session).

    Raises
    ------
    JobError
        If `preprocessed_path` is unset, or a partition can't be loaded.
    """
    from datasets import DatasetDict

    from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

    session_dir = model_session.preprocessed_path
    if not session_dir:
        raise JobError(
            f"Model session {model_session.id} has no preprocessed_path; "
            "preprocessing may not have run yet."
        )

    def _load_partition(path: str):
        x = load_dataset(os.path.join(path, "x"))
        y = load_dataset(os.path.join(path, "y"))
        return x, y

    if os.path.isdir(os.path.join(session_dir, "train")):
        x, y = {}, {}
        for split_name in ("train", "validation", "test"):
            part_path = os.path.join(session_dir, split_name)
            if os.path.isdir(part_path):
                x[split_name], y[split_name] = _load_partition(part_path)
        return DatasetDict(x), DatasetDict(y)

    fold_names = sorted(
        (d for d in os.listdir(session_dir) if d.startswith("fold_")),
        key=lambda d: int(d.split("_")[1]),
    )

    x_list, y_list = [], []
    for fold_name in [*fold_names, "full_dataset"]:
        x_fold, y_fold = {}, {}
        for split_name in ("train", "test"):
            part_path = os.path.join(session_dir, fold_name, split_name)
            if os.path.isdir(part_path):
                x_fold[split_name], y_fold[split_name] = _load_partition(part_path)
        x_list.append(DatasetDict(x_fold))
        y_list.append(DatasetDict(y_fold))

    return x_list, y_list


def get_reference_partition_path(model_session: ModelSession) -> Optional[str]:
    """Path to the single partition that best represents a session's
    current preprocessed state: `full_dataset/train` for cross-validation,
    `train` for holdout.

    Returns None if the session has no `preprocessed_path`, or the
    partition isn't on disk.
    """
    if not model_session.preprocessed_path:
        return None
    is_cv = model_session.evaluation_strategy == "CrossValidationEvaluationStrategy"
    relative = os.path.join("full_dataset", "train") if is_cv else "train"
    partition_path = os.path.join(model_session.preprocessed_path, relative)
    return partition_path if os.path.isdir(partition_path) else None


def load_preprocessed_reference_dataset(
    model_session: ModelSession,
) -> "DashAIDataset":
    """Load the combined (input+output columns together) reference
    partition, the session's actual training data, including any column a
    converter added or renamed. Internally the partition is stored as two
    separate files (`x`/`y`, see `SessionPreprocessingJob.run()`); this
    function re-merges them so its own external contract (one combined
    dataset) stays unchanged for `ModelJob`.
    """
    from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

    partition_path = get_reference_partition_path(model_session)
    if not partition_path:
        raise JobError(
            f"Model session {model_session.id} has no usable preprocessed "
            "reference partition."
        )
    x = load_dataset(os.path.join(partition_path, "x"))
    y = load_dataset(os.path.join(partition_path, "y"))
    return merge_input_output_columns(x, y)


def get_real_input_output_columns(
    model_session: ModelSession,
) -> Tuple[List[str], List[str]]:
    """Real column names for the session's finalized input/output atom
    selection. If the session has converters (so `preprocessed_path` is
    set), these are read directly off the already-saved reference
    partition's separate `x`/`y` files (see `run()`), the single
    production resolution, prediction/explanation never need a per-fold
    one. If the session has no converters at all, every atom is
    necessarily a literal `column` atom (nothing could have produced a
    `group`), so the real names are just each atom's own `name`.
    """
    from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

    if model_session.preprocessed_path:
        partition_path = get_reference_partition_path(model_session)
        if not partition_path:
            raise JobError(
                f"Model session {model_session.id} has no usable preprocessed "
                "reference partition."
            )
        x = load_dataset(os.path.join(partition_path, "x"))
        y = load_dataset(os.path.join(partition_path, "y"))
        real_output_columns = list(y.column_names)
        if real_output_columns == [NO_OUTPUT_PLACEHOLDER_COLUMN]:
            # Defense in depth: if the placeholder path was ever legitimately
            # reached (e.g. no output column chosen yet), the saved `y` file
            # carries only this sentinel, never a real target. Handing it
            # back as if it were a usable column name would let
            # `model_job.py`/`predict_job.py`/`explainer_job.py` select it
            # as a real target, producing a confusing `KeyError` deep in
            # unrelated code instead of a clear, immediate error here.
            raise JobError(
                f"Model session {model_session.id} has no real output "
                "column configured; cannot predict, explain, or train on "
                "it yet."
            )
        return list(x.column_names), real_output_columns

    # Plain strings are also accepted alongside `{"kind": "column", ...}`
    # atoms: some callers (tests building a `ModelSession` directly, older
    # persisted sessions) still store `input_columns`/`output_columns` as
    # flat `List[str]`, since the DB column itself is untyped JSON — same
    # backward-compatible reading `dataset_split_utils._atom_names_if_all_columns`
    # already does. A bare string is unambiguously a raw-column reference.
    def _atom_name(atom):
        return atom if isinstance(atom, str) else atom["name"]

    input_columns = [_atom_name(atom) for atom in model_session.input_columns]
    output_columns = [_atom_name(atom) for atom in model_session.output_columns]
    return input_columns, output_columns


class SessionPreprocessingJob(BaseJob):
    """Fits/transforms a ModelSession's converters once, ahead of any Run.

    Splits the raw dataset the same way `ModelJob` would (holdout partitions,
    or cross-validation folds), applies `apply_session_converters` (fit only
    on each partition's train, transform the rest — never re-fit), and
    persists every resulting partition to disk under the session's own
    storage folder, plus the fitted converters used for the final model.
    """

    @inject
    def set_status_as_delivered(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the session preprocessing as delivered."""
        model_session_id = self.kwargs["model_session_id"]

        with session_factory() as db:
            model_session = db.get(ModelSession, model_session_id)
            if model_session is None:
                raise JobError(
                    f"ModelSession with id {model_session_id} does not exist in DB."
                )
            try:
                model_session.set_preprocessing_status_as_delivered()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)
                raise JobError(
                    "Error setting session preprocessing status as delivered"
                ) from e

    @inject
    def set_status_as_error(
        self, session_factory: "sessionmaker" = lambda di: di["session_factory"]
    ) -> None:
        """Set the status of the session preprocessing as error."""
        model_session_id = self.kwargs.get("model_session_id")
        if model_session_id is None:
            return

        with session_factory() as db:
            model_session = db.get(ModelSession, model_session_id)
            if model_session is None:
                return
            try:
                model_session.set_preprocessing_status_as_error()
                db.commit()
            except exc.SQLAlchemyError as e:
                log.exception(e)

    @inject
    def get_job_name(self) -> str:
        """Get a descriptive name for the job."""
        model_session_id = self.kwargs.get("model_session_id")
        if not model_session_id:
            return "Session Preprocessing Job"

        from kink import di

        session_factory = di["session_factory"]

        try:
            with session_factory() as db:
                model_session = db.get(ModelSession, model_session_id)
                if model_session and model_session.name:
                    return f"Preprocessing: {model_session.name}"
        except Exception as e:
            log.exception(f"Error getting job name: {e}")

        return f"Session Preprocessing Job #{model_session_id}"

    @inject
    def run(
        self,
    ) -> None:
        from kink import di

        from DashAI.back.dataloaders.classes.dashai_dataset import save_dataset

        component_registry = di["component_registry"]
        session_factory = di["session_factory"]
        config = di["config"]

        model_session_id: int = self.kwargs["model_session_id"]

        with session_factory() as db:
            model_session: ModelSession = db.get(ModelSession, model_session_id)
            if not model_session:
                raise JobError(
                    f"ModelSession with id {model_session_id} does not exist in DB."
                )

            try:
                model_session.set_preprocessing_status_as_started()
                db.commit()

                # A session's own `output_columns` must always be a
                # literal `column` atom, never a `group` atom: the raw
                # dataset has to be split into train/test *before* any
                # converter runs, so a converter-produced target value
                # genuinely cannot exist yet at split time. There is no
                # way to make this work without deeper restructuring, so
                # it's rejected here, loudly, rather than silently
                # persisting a placeholder target (see
                # `NO_OUTPUT_PLACEHOLDER_COLUMN`). `input_columns` is not
                # restricted this way — group atoms remain fully
                # supported there, the main use case this feature exists
                # for (using a converter's generated features as input).
                if any(
                    not isinstance(atom, str) and atom.get("kind") == "group"
                    for atom in model_session.output_columns or []
                ):
                    raise JobError(
                        "output_columns cannot reference a converter's "
                        "group output; the target column must be an "
                        "original dataset column."
                    )

                self.report_progress(0.1, "Loading dataset")
                X, Y, splitter, _task, _prepared_dataset = load_dataset_and_splitter(
                    model_session, db, component_registry
                )

                self.report_progress(0.2, "Splitting dataset")
                x, y, _splits = splitter.split(X, Y)

                self.report_progress(0.4, "Fitting converters")
                x, y, fitted_converters, group_registry = apply_session_converters(
                    x, y, model_session.converters, component_registry
                )

                self.report_progress(0.7, "Saving preprocessed partitions")
                session_dir = os.path.join(
                    str(config["MODEL_SESSIONS_PATH"]), str(model_session.id)
                )
                # Clear any stale content first (e.g. a re-run, or a reused
                # session id after a previous session was deleted) so old
                # partitions from a different split shape never linger
                # alongside the new ones.
                if os.path.isdir(session_dir):
                    shutil.rmtree(session_dir)
                stale_converters_path = fitted_converters_path(session_dir)
                if os.path.exists(stale_converters_path):
                    os.remove(stale_converters_path)

                # `y` carries only the `NO_OUTPUT_PLACEHOLDER_COLUMN`
                # placeholder (see `dataset_split_utils.py`) whenever no
                # real output was available to split on — either no output
                # column has been chosen yet (the wizard's Preprocessing
                # step comes before its Columns step), or one was chosen
                # but doesn't resolve against the raw dataset (a converter
                # produced it, e.g. `LabelEncoder` appending `le_<col>`).
                # Checking `y` itself (not `model_session.output_columns`)
                # is what actually matches what's about to be merged below
                # — a converter-produced output column falls into the same
                # "no real output to merge" case even though
                # `output_columns` is set.
                first_y_partition = (
                    next(iter(y[0].values()))
                    if isinstance(y, list)
                    else next(iter(y.values()))
                )
                has_output_columns = (
                    NO_OUTPUT_PLACEHOLDER_COLUMN not in first_y_partition.column_names
                )

                if isinstance(x, list):
                    last_index = len(x) - 1
                    for i, (x_fold, y_fold) in enumerate(zip(x, y, strict=True)):
                        fold_name = "full_dataset" if i == last_index else f"fold_{i}"
                        for split_name, x_part in x_fold.items():
                            if len(x_part) == 0:
                                continue
                            input_names = resolve_final_columns(
                                model_session.input_columns, group_registry, i
                            )
                            x_selected = x_part.select_columns(input_names)
                            save_dataset(
                                x_selected,
                                os.path.join(session_dir, fold_name, split_name, "x"),
                            )
                            if has_output_columns:
                                output_names = resolve_final_columns(
                                    model_session.output_columns, group_registry, i
                                )
                                y_selected = y_fold[split_name].select_columns(
                                    output_names
                                )
                                save_dataset(
                                    y_selected,
                                    os.path.join(
                                        session_dir, fold_name, split_name, "y"
                                    ),
                                )
                            else:
                                save_dataset(
                                    y_fold[split_name],
                                    os.path.join(
                                        session_dir, fold_name, split_name, "y"
                                    ),
                                )
                else:
                    for split_name, x_part in x.items():
                        if len(x_part) == 0:
                            continue
                        input_names = resolve_final_columns(
                            model_session.input_columns, group_registry, 0
                        )
                        x_selected = x_part.select_columns(input_names)
                        save_dataset(
                            x_selected, os.path.join(session_dir, split_name, "x")
                        )
                        if has_output_columns:
                            output_names = resolve_final_columns(
                                model_session.output_columns, group_registry, 0
                            )
                            y_selected = y[split_name].select_columns(output_names)
                            save_dataset(
                                y_selected, os.path.join(session_dir, split_name, "y")
                            )
                        else:
                            save_dataset(
                                y[split_name],
                                os.path.join(session_dir, split_name, "y"),
                            )

                save_fitted_converters(session_dir, fitted_converters)

                model_session.preprocessed_path = session_dir
                model_session.set_preprocessing_status_as_finished()
                db.commit()
            except Exception as e:
                log.exception(e)
                model_session.set_preprocessing_status_as_error()
                db.commit()
                raise JobError(
                    f"Error preprocessing session {model_session_id}: {e}"
                ) from e
