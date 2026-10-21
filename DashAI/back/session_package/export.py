"""Build a ``.dashai`` file from a model session.

The file is a zip with the session recipe and metrics as readable JSON, the
dataset as DashAI stores it and, when asked for, the trained models and the
fitted preprocessing. IDs and absolute paths stay out: importing assigns new
ones, so the recipe can be read and retrained by any later DashAI even when a
pickled model no longer opens.
"""

import hashlib
import json
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from DashAI.back.model_package.export import _zip_directory
from DashAI.back.model_package.manifest import (
    MANIFEST_ENTRY,
    ModelPackageError,
    current_versions,
    plugin_distributions,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

SESSION_EXTENSION = ".dashai"
SESSION_FORMAT_VERSION = 1
KIND_SESSION = "session"
SESSION_ENTRY = "session.json"
# Holds data.arrow and splits.json, like "<dataset>/dataset" on disk.
DATASET_ENTRY = "dataset"
PREPROCESSING_ENTRY = "preprocessing"
RUNS_ENTRY = "runs"
CONTENTS = ["dataset", "session", "runs", "metrics"]
PLOT_FIELDS = (
    "plot_history_path",
    "plot_slice_path",
    "plot_contour_path",
    "plot_importance_path",
)
SESSION_FIELDS = (
    "name",
    "task_name",
    "input_columns",
    "output_columns",
    "input_column_refs",
    "splits",
    "evaluation_strategy",
    "preprocessing",
    "train_metrics",
    "validation_metrics",
    "test_metrics",
)
RUN_FIELDS = (
    "name",
    "description",
    "model_name",
    "parameters",
    "optimizer_name",
    "optimizer_parameters",
    "nested",
    "goal_metric",
    "split_indexes",
    "artifacts",
)


class SessionNotFoundError(ModelPackageError):
    """The session to export does not exist."""


class SessionNotExportableError(ModelPackageError):
    """The chosen runs cannot be exported from this session."""


def session_filename(session_name: str) -> str:
    """Turn a session name into a safe file name with the session extension."""
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", session_name or "").strip("_")
    return f"{base or 'session'}{SESSION_EXTENSION}"


def _in_progress(run) -> bool:
    from DashAI.back.core.enums.status import RunStatus

    return run.status in (RunStatus.DELIVERED, RunStatus.STARTED)


def _finished(run) -> bool:
    from DashAI.back.core.enums.status import RunStatus

    return run.status == RunStatus.FINISHED


def _has_model_file(run) -> bool:
    return bool(run.run_path) and Path(run.run_path).exists()


def _size(path: Optional[str]) -> int:
    if not path or not Path(path).exists():
        return 0
    path = Path(path)
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _copy(source: Path, target: Path) -> None:
    """Copy a file or a folder (HuggingFace models save folders)."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


def _metric_row(metric) -> Dict[str, Any]:
    return {
        "split": metric.split.name,
        "level": metric.level.name,
        "name": metric.name,
        "value": metric.value,
        "std_value": metric.std_value,
        "step": metric.step,
        "fold_index": metric.fold_index,
        "inner_fold_index": metric.inner_fold_index,
        "timestamp": _iso(metric.timestamp),
    }


def export_preview(session_id: int, session_factory: "sessionmaker") -> Dict[str, Any]:
    """What the export dialog shows: runs, what each can carry, and sizes.

    Raises
    ------
    SessionNotFoundError
        If the session does not exist.
    """
    from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
    from DashAI.back.dependencies.database.models import (
        Dataset,
        Metric,
        ModelSession,
        Run,
    )

    with session_factory() as db:
        session = db.get(ModelSession, session_id)
        if session is None:
            raise SessionNotFoundError(f"Session {session_id} does not exist.")
        dataset = db.get(Dataset, session.dataset_id)
        dataset_size = _size(str(Path(dataset.file_path) / DATASET_ENTRY))
        models_size = _size(session.preprocessing_artifacts_path)

        runs = []
        for run in db.query(Run).filter(Run.model_session_id == session_id):
            with_model = _finished(run) and _has_model_file(run)
            goal = (
                db.query(Metric)
                .filter(
                    Metric.run_id == run.id,
                    Metric.name == run.goal_metric,
                    Metric.level == LevelEnum.LAST,
                    Metric.split == SplitEnum.TEST,
                )
                .first()
            )
            if with_model:
                models_size += _size(run.run_path) + sum(
                    _size(getattr(run, field)) for field in PLOT_FIELDS
                )
            runs.append(
                {
                    "id": run.id,
                    "name": run.name,
                    "status": run.status.name,
                    "goal_metric": run.goal_metric,
                    "goal_metric_value": goal.value if goal else None,
                    "in_progress": _in_progress(run),
                    "with_model": with_model,
                    "missing_model_file": _finished(run) and not _has_model_file(run),
                }
            )

        return {
            "session_name": session.name,
            "dataset_name": dataset.name,
            "runs": runs,
            "size_bytes": {
                "with_models": dataset_size + models_size,
                "recipe_only": dataset_size,
            },
        }


def build_session_package(
    session_id: int,
    run_ids: List[int],
    include_trained_models: bool,
    destination: Path,
    session_factory: "sessionmaker",
    component_registry: Any,
) -> Dict[str, Any]:
    """Write a ``.dashai`` file for a session and the chosen runs.

    A chosen run carries its model, plots and metrics only when trained models
    are included, it finished and its model file is still on disk; otherwise
    it travels as a recipe and imports as never trained.

    Returns
    -------
    dict
        The manifest written into the file.

    Raises
    ------
    SessionNotFoundError
        If the session does not exist.
    SessionNotExportableError
        If no run is chosen, or a chosen run belongs to another session or is
        still training.
    """
    from DashAI.back.dependencies.database.models import (
        Dataset,
        Metric,
        ModelSession,
        Run,
    )

    with session_factory() as db:
        session = db.get(ModelSession, session_id)
        if session is None:
            raise SessionNotFoundError(f"Session {session_id} does not exist.")
        if not run_ids:
            raise SessionNotExportableError("Choose at least one run to export.")
        runs = []
        for run_id in run_ids:
            run = db.get(Run, run_id)
            if run is None or run.model_session_id != session_id:
                raise SessionNotExportableError(
                    f"Run {run_id} does not belong to this session."
                )
            if _in_progress(run):
                raise SessionNotExportableError(
                    f"Run '{run.name}' is still training. Wait until it finishes."
                )
            runs.append(run)

        dataset = db.get(Dataset, session.dataset_id)
        dataset_dir = Path(dataset.file_path) / DATASET_ENTRY
        artifacts_path = session.preprocessing_artifacts_path
        recipe_session = {field: getattr(session, field) for field in SESSION_FIELDS}
        recipe_dataset = {
            "name": dataset.name,
            "total_rows": dataset.total_rows,
            "total_columns": dataset.total_columns,
        }
        exported_runs = []
        for run in runs:
            with_model = (
                include_trained_models and _finished(run) and _has_model_file(run)
            )
            metrics = (
                [
                    _metric_row(metric)
                    for metric in db.query(Metric).filter(Metric.run_id == run.id)
                ]
                if with_model
                else []
            )
            exported_runs.append(
                {
                    "recipe": {field: getattr(run, field) for field in RUN_FIELDS},
                    "with_model": with_model,
                    "run_path": run.run_path,
                    "plots": {field: getattr(run, field) for field in PLOT_FIELDS},
                    "created": _iso(run.created),
                    "start_time": _iso(run.start_time),
                    "end_time": _iso(run.end_time),
                    "metrics": metrics,
                }
            )

    steps = (recipe_session["preprocessing"] or {}).get("steps") or []
    provider_classes = [component_registry[recipe_session["task_name"]]["class"]]
    provider_classes += [
        component_registry[run["recipe"]["model_name"]]["class"]
        for run in exported_runs
    ]
    provider_classes += [
        component_registry[step["converter"]]["class"] for step in steps
    ]

    with tempfile.TemporaryDirectory(prefix="dashai-session-") as staging_dir:
        staging = Path(staging_dir)
        shutil.copytree(dataset_dir, staging / DATASET_ENTRY)
        if include_trained_models and artifacts_path and Path(artifacts_path).exists():
            shutil.copytree(artifacts_path, staging / PREPROCESSING_ENTRY)

        recipe_runs = []
        for index, run in enumerate(exported_runs):
            entry = {
                **run["recipe"],
                "status": "FINISHED" if run["with_model"] else "NOT_STARTED",
                "created": run["created"],
                "start_time": run["start_time"] if run["with_model"] else None,
                "end_time": run["end_time"] if run["with_model"] else None,
                "model_entry": None,
                "plots": {},
                "metrics": run["metrics"],
            }
            if run["with_model"]:
                run_dir = f"{RUNS_ENTRY}/{index}"
                entry["model_entry"] = f"{run_dir}/model"
                _copy(Path(run["run_path"]), staging / entry["model_entry"])
                for field, path in run["plots"].items():
                    if path and Path(path).is_file():
                        entry["plots"][field] = f"{run_dir}/{field}.pickle"
                        _copy(Path(path), staging / entry["plots"][field])
            recipe_runs.append(entry)

        recipe = {
            "session": recipe_session,
            "dataset": recipe_dataset,
            "runs": recipe_runs,
        }
        (staging / SESSION_ENTRY).write_text(json.dumps(recipe, indent=2))

        manifest = {
            "format_version": SESSION_FORMAT_VERSION,
            "kind": KIND_SESSION,
            "versions": current_versions(),
            "plugins": plugin_distributions(provider_classes),
            "contents": CONTENTS,
            "dataset_hash": _sha256(staging / DATASET_ENTRY / "data.arrow"),
            "includes_trained_models": include_trained_models,
            "info": {
                "session_name": recipe_session["name"],
                "dataset_name": recipe_dataset["name"],
                "exported_at": datetime.now().isoformat(),
                "run_count": len(recipe_runs),
            },
        }
        (staging / MANIFEST_ENTRY).write_text(json.dumps(manifest, indent=2))
        _zip_directory(staging, Path(destination))

    return manifest
