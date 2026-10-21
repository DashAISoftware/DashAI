"""Import a ``.dashai`` file as a new model session.

Importing never opens a pickle: it checks the manifest and the recipe, copies
files into the DashAI folders and creates new rows. The models only run code
when they are used. Nothing that already exists is changed: names that clash
get a number, and a failure halfway removes every row and file it created.
"""

import json
import os
import shutil
import tempfile
import uuid
import warnings
import zipfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Union

from DashAI.back.model_package.manifest import (
    MANIFEST_ENTRY,
    MissingPluginError,
    ModelPackageError,
    check_manifest,
)
from DashAI.back.session_package.export import (
    CONTENTS,
    DATASET_ENTRY,
    KIND_SESSION,
    PLOT_FIELDS,
    PREPROCESSING_ENTRY,
    RUN_FIELDS,
    SESSION_ENTRY,
    SESSION_FIELDS,
    SESSION_FORMAT_VERSION,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker

NOT_A_SESSION = "{path} is not a DashAI session file"
# The file names the training job gives each plot, with the run id appended.
PLOT_PREFIXES = {
    "plot_history_path": "history_objective_plot",
    "plot_slice_path": "slice_plot",
    "plot_contour_path": "contour_plot",
    "plot_importance_path": "importance_plot",
}


class UnsafePackageError(ModelPackageError):
    """An entry of the zip would be written outside the extraction folder."""


def unique_name(base: str, taken: Set[str]) -> str:
    """``base`` when free, else ``base (n)`` with the smallest free n >= 2."""
    if base not in taken:
        return base
    number = 2
    while f"{base} ({number})" in taken:
        number += 1
    return f"{base} ({number})"


def safe_extract(archive: zipfile.ZipFile, target: Path) -> None:
    """Extract every entry, refusing the whole zip if one escapes ``target``.

    Raises
    ------
    UnsafePackageError
        If an entry is absolute or resolves outside ``target`` (zip slip).
    """
    root = target.resolve()
    for name in archive.namelist():
        destination = (root / name).resolve()
        if os.path.isabs(name) or not destination.is_relative_to(root):
            raise UnsafePackageError(
                f"The file has an entry outside its folder ({name!r}); "
                "it was not imported."
            )
    archive.extractall(root)


def _date(value: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(value) if value else None


def _copy_model(source: Path, target: Path) -> None:
    """Copy a model file or folder (HuggingFace models save folders)."""
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


def _read_package(path: Union[str, Path], workdir: Path):
    try:
        with zipfile.ZipFile(path) as archive:
            safe_extract(archive, workdir)
        manifest = json.loads((workdir / MANIFEST_ENTRY).read_text(encoding="utf-8"))
    except (
        zipfile.BadZipFile,
        FileNotFoundError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as e:
        raise ModelPackageError(NOT_A_SESSION.format(path=path)) from e
    if not isinstance(manifest, dict):
        raise ModelPackageError(NOT_A_SESSION.format(path=path))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        check_manifest(manifest, KIND_SESSION, SESSION_FORMAT_VERSION)
    notes = [str(warning.message) for warning in caught]
    unknown = [part for part in manifest.get("contents", []) if part not in CONTENTS]
    if unknown:
        notes.append(
            "This file has parts this DashAI does not know and skipped: "
            + ", ".join(unknown)
        )

    try:
        recipe = json.loads((workdir / SESSION_ENTRY).read_text(encoding="utf-8"))
        session = recipe["session"]
        dataset = recipe["dataset"]
        runs = recipe["runs"]
        missing = [field for field in SESSION_FIELDS if field not in session]
        missing += [
            field
            for run in runs
            for field in (*RUN_FIELDS, "status", "model_entry")
            if field not in run
        ]
        if missing or "name" not in dataset:
            raise KeyError(missing)
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError) as e:
        raise ModelPackageError(NOT_A_SESSION.format(path=path)) from e
    if not (workdir / DATASET_ENTRY / "data.arrow").is_file():
        raise ModelPackageError(NOT_A_SESSION.format(path=path))
    return recipe, notes


def _check_components(recipe: Dict[str, Any], component_registry: Any) -> None:
    session = recipe["session"]
    steps = (session["preprocessing"] or {}).get("steps") or []
    needed = [session["task_name"]]
    needed += [run["model_name"] for run in recipe["runs"]]
    needed += [step["converter"] for step in steps]
    for name in needed:
        if name not in component_registry:
            raise MissingPluginError(
                f"This session needs '{name}', which this DashAI does not have. "
                "Install the plugin that provides it and try again."
            )


def import_session_package(
    path: Union[str, Path],
    session_factory: "sessionmaker",
    component_registry: Any,
    config: Dict[str, Any],
    job_queue: Any,
) -> Dict[str, Any]:
    """Create a new session, its dataset and runs from a ``.dashai`` file.

    Returns
    -------
    dict
        ``session_id``, ``dataset_id``, the final ``session_name`` and
        ``dataset_name``, whether each was ``renamed``, version ``warnings``
        and the names of the runs that arrived untrained (``recipe_runs``).

    Raises
    ------
    ModelPackageError
        If the file is not a DashAI session, is unsafe, is newer than this
        DashAI reads, or needs a plugin or component that is missing.
    """
    from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
    from DashAI.back.core.enums.status import RunStatus
    from DashAI.back.dependencies.database.models import (
        Dataset,
        Metric,
        ModelSession,
        Run,
    )
    from DashAI.back.job.preprocessing_job import PreprocessingJob

    workdir = Path(tempfile.mkdtemp(prefix="dashai-import-"))
    # Every path below is new (a fresh uuid), so removing them on failure
    # never touches anything that existed before the import.
    created: List[Path] = []
    try:
        recipe, notes = _read_package(path, workdir)
        _check_components(recipe, component_registry)
        recipe_session = recipe["session"]
        has_steps = bool((recipe_session["preprocessing"] or {}).get("steps"))

        try:
            # Files are copied before the transaction opens: SQLite locks the
            # whole database for writing, and a copy of large models would
            # otherwise make other writers (training jobs) fail.
            dataset_dir = Path(config["DATASETS_PATH"]) / str(uuid.uuid4())
            created.append(dataset_dir)
            shutil.copytree(workdir / DATASET_ENTRY, dataset_dir / DATASET_ENTRY)

            artifacts_dir = None
            if (workdir / PREPROCESSING_ENTRY).is_dir():
                artifacts_dir = Path(config["PREPROCESSING_PATH"]) / str(uuid.uuid4())
                created.append(artifacts_dir)
                shutil.copytree(workdir / PREPROCESSING_ENTRY, artifacts_dir)

            runs_dir = Path(config["RUNS_PATH"])
            runs_dir.mkdir(parents=True, exist_ok=True)
            run_files = []
            for entry in recipe["runs"]:
                if not entry["model_entry"]:
                    run_files.append(None)
                    continue
                key = str(uuid.uuid4())
                run_path = runs_dir / key
                created.append(run_path)
                _copy_model(workdir / entry["model_entry"], run_path)
                plots = {}
                for field in PLOT_FIELDS:
                    source = entry.get("plots", {}).get(field)
                    if source:
                        plot = runs_dir / f"{PLOT_PREFIXES[field]}_{key}.pickle"
                        created.append(plot)
                        shutil.copy2(workdir / source, plot)
                        plots[field] = str(plot)
                run_files.append((run_path, plots))

            with session_factory() as db:
                try:
                    taken_datasets = {name for (name,) in db.query(Dataset.name)}
                    taken_sessions = {name for (name,) in db.query(ModelSession.name)}
                    dataset_name = unique_name(
                        recipe["dataset"]["name"], taken_datasets
                    )
                    session_name = unique_name(recipe_session["name"], taken_sessions)

                    dataset = Dataset(
                        name=dataset_name,
                        file_path=os.path.realpath(dataset_dir),
                        total_rows=recipe["dataset"].get("total_rows"),
                        total_columns=recipe["dataset"].get("total_columns"),
                    )
                    dataset.set_status_as_finished()
                    db.add(dataset)
                    db.flush()

                    session = ModelSession(
                        **{
                            field: recipe_session[field]
                            for field in SESSION_FIELDS
                            if field != "name"
                        },
                        name=session_name,
                        dataset_id=dataset.id,
                        preprocessing_status="pending" if has_steps else "ready",
                    )
                    if artifacts_dir is not None:
                        session.preprocessing_artifacts_path = str(artifacts_dir)
                        session.preprocessing_status = "ready"
                    needs_preprocessing = session.preprocessing_status == "pending"
                    db.add(session)
                    db.flush()

                    recipe_runs = []
                    for entry, files in zip(recipe["runs"], run_files, strict=True):
                        run = Run(
                            model_session_id=session.id,
                            **{field: entry[field] for field in RUN_FIELDS},
                        )
                        if entry.get("created"):
                            run.created = _date(entry["created"])
                        if files is None:
                            recipe_runs.append(entry["name"])
                            db.add(run)
                            continue

                        run_path, plots = files
                        run.run_path = str(run_path)
                        for field, plot in plots.items():
                            setattr(run, field, plot)
                        run.status = RunStatus.FINISHED
                        run.start_time = _date(entry.get("start_time"))
                        run.end_time = _date(entry.get("end_time"))
                        db.add(run)
                        db.flush()
                        db.add_all(
                            Metric(
                                run_id=run.id,
                                split=SplitEnum[metric["split"]],
                                level=LevelEnum[metric["level"]],
                                name=metric["name"],
                                value=metric["value"],
                                std_value=metric.get("std_value"),
                                step=metric["step"],
                                fold_index=metric.get("fold_index"),
                                inner_fold_index=metric.get("inner_fold_index"),
                                **(
                                    {"timestamp": _date(metric["timestamp"])}
                                    if metric.get("timestamp")
                                    else {}
                                ),
                            )
                            for metric in entry.get("metrics", [])
                        )

                    db.commit()
                    session_id, dataset_id = session.id, dataset.id
                except BaseException:
                    db.rollback()
                    raise
        except BaseException:
            for created_path in reversed(created):
                if created_path.is_dir():
                    shutil.rmtree(created_path, ignore_errors=True)
                elif created_path.exists():
                    created_path.unlink()
            raise
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    if needs_preprocessing:
        job_id = job_queue.put(PreprocessingJob(model_session_id=session_id)).id
        with session_factory() as db:
            db.get(ModelSession, session_id).preprocessing_job_id = str(job_id)
            db.commit()

    return {
        "session_id": session_id,
        "dataset_id": dataset_id,
        "session_name": session_name,
        "dataset_name": dataset_name,
        "renamed": {
            "session": session_name != recipe_session["name"],
            "dataset": dataset_name != recipe["dataset"]["name"],
        },
        "warnings": notes,
        "recipe_runs": recipe_runs,
    }
