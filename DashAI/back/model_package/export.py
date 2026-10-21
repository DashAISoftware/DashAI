"""Write a finished run, and what it needs from its session, to a package."""

import json
import pickle
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

from DashAI.back.model_package.manifest import (
    FORMAT_VERSION,
    MANIFEST_ENTRY,
    MODEL_ENTRY,
    PACKAGE_EXTENSION,
    PREPROCESSOR_ENTRY,
    SCHEMA_ENTRY,
    ModelPackageError,
    current_versions,
    plugin_distributions,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker


class RunNotFoundError(ModelPackageError):
    """The run to export does not exist."""


class RunNotExportableError(ModelPackageError):
    """The run exists but has no usable trained model yet."""


def package_filename(run_name: str) -> str:
    """Turn a run name into a safe file name with the package extension."""
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", run_name or "").strip("_") or "model"
    return f"{base}{PACKAGE_EXTENSION}"


def _class_reference(cls: type) -> Dict[str, str]:
    return {"module": cls.__module__, "class": cls.__qualname__}


def _write_empty_schema(source: Path, target: Path) -> None:
    """Copy an Arrow file's schema, DashAI type metadata included, with no rows."""
    import pyarrow as pa

    with pa.OSFile(str(source), "rb") as handle:
        schema = pa.ipc.open_file(handle).schema
    target.parent.mkdir(parents=True, exist_ok=True)
    with (
        pa.OSFile(str(target), "wb") as sink,
        pa.ipc.new_file(sink, schema) as writer,
    ):
        writer.write_table(schema.empty_table())


def _zip_directory(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())


def build_package(
    run_id: int,
    destination: Path,
    session_factory: "sessionmaker",
    component_registry: Any,
) -> Dict[str, Any]:
    """Export a finished run as a model package written to ``destination``.

    Returns
    -------
    dict
        The manifest written into the package.

    Raises
    ------
    RunNotFoundError
        If the run does not exist.
    RunNotExportableError
        If the run is not finished, has no saved model, or its session has
        preprocessing steps without a fitted preprocessor.
    """
    from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
    from DashAI.back.dependencies.database.models import (
        Dataset,
        Metric,
        ModelSession,
        Run,
        RunStatus,
    )
    from DashAI.back.job.base_job import JobError
    from DashAI.back.job.predict_job import _preprocessing_artifacts_path
    from DashAI.back.units.apply_session_preprocessing_unit import (
        FINAL_PREPROCESSOR_FILENAME,
    )

    with session_factory() as db:
        run = db.get(Run, run_id)
        if run is None:
            raise RunNotFoundError(f"Run {run_id} does not exist.")
        if run.status != RunStatus.FINISHED or not run.run_path:
            raise RunNotExportableError(
                "Only a finished run with a saved model can be exported."
            )
        session = db.get(ModelSession, run.model_session_id)
        dataset = db.get(Dataset, session.dataset_id)
        try:
            artifacts_path = _preprocessing_artifacts_path(session)
        except JobError as e:
            raise RunNotExportableError(str(e)) from e
        test_metrics = {
            metric.name: metric.value
            for metric in db.query(Metric).filter(
                Metric.run_id == run_id,
                Metric.level == LevelEnum.LAST,
                Metric.split == SplitEnum.TEST,
            )
        }
        model_name = run.model_name
        run_name = run.name
        run_path = Path(run.run_path)
        parameters = run.parameters
        trained_at = run.end_time.isoformat() if run.end_time else None
        task_name = session.task_name
        session_name = session.name
        input_columns = list(session.input_columns)
        output_columns = list(session.output_columns)
        dataset_arrow = Path(dataset.file_path) / "dataset" / "data.arrow"

    model_class = component_registry[model_name]["class"]
    task_class = component_registry[task_name]["class"]
    provider_classes = [model_class, task_class]
    preprocessor_file = None
    if artifacts_path:
        preprocessor_file = Path(artifacts_path) / FINAL_PREPROCESSOR_FILENAME
        with open(preprocessor_file, "rb") as handle:
            preprocessor = pickle.load(handle)
        provider_classes += [type(c) for c in preprocessor.fitted_converters]

    manifest = {
        "format_version": FORMAT_VERSION,
        "model": {
            "name": model_name,
            **_class_reference(model_class),
            "parameters": parameters,
        },
        "task": {"name": task_name, **_class_reference(task_class)},
        "input_columns": input_columns,
        "output_columns": output_columns,
        "has_preprocessing": preprocessor_file is not None,
        "versions": current_versions(),
        "plugins": plugin_distributions(provider_classes),
        "info": {
            "run_name": run_name,
            "session_name": session_name,
            "trained_at": trained_at,
            "test_metrics": test_metrics,
        },
    }

    with tempfile.TemporaryDirectory(prefix="dashai-export-") as staging_dir:
        staging = Path(staging_dir)
        # A model saves either one file or a folder (HuggingFace models).
        if run_path.is_dir():
            shutil.copytree(run_path, staging / MODEL_ENTRY)
        else:
            shutil.copy2(run_path, staging / MODEL_ENTRY)
        if preprocessor_file is not None:
            (staging / PREPROCESSOR_ENTRY).parent.mkdir(parents=True)
            shutil.copy2(preprocessor_file, staging / PREPROCESSOR_ENTRY)
        _write_empty_schema(dataset_arrow, staging / SCHEMA_ENTRY / "data.arrow")
        (staging / MANIFEST_ENTRY).write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        _zip_directory(staging, Path(destination))

    return manifest
