"""Tests for the compute_metadata flag in DatasetJob.run()."""

import json
import shutil
from pathlib import Path

from DashAI.back.dependencies.database.models import Dataset
from DashAI.back.job.dataset_job import DatasetJob

IRIS_SCHEMA = {
    "SepalLengthCm": {"type": "Float", "dtype": "float64"},
    "SepalWidthCm": {"type": "Float", "dtype": "float64"},
    "PetalLengthCm": {"type": "Float", "dtype": "float64"},
    "PetalWidthCm": {"type": "Float", "dtype": "float64"},
    "Species": {"type": "Categorical", "dtype": "string"},
}


def _run_dataset_job(client, name: str, compute_metadata: bool) -> Dataset:
    """Run DatasetJob synchronously with the given compute_metadata flag.

    Parameters
    ----------
    client : TestClient
        Module-scoped FastAPI test client (from ``conftest.py``).
    name : str
        Dataset name.
    compute_metadata : bool
        Value to pass through ``params["compute_metadata"]``.

    Returns
    -------
    Dataset
        The persisted ``Dataset`` row after the job has finished.
    """
    abs_file_path = Path(__file__).parent / "iris.csv"
    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        entry = Dataset(name=name, file_path="")
        db.add(entry)
        db.commit()
        db.refresh(entry)

        kwargs = {
            "dataset_id": entry.id,
            "url": "",
            "params": {
                "dataloader": "CSVDataLoader",
                "separator": ",",
                "name": entry.name,
                "schema": IRIS_SCHEMA,
                "compute_metadata": compute_metadata,
            },
            "file_path": abs_file_path,
        }
        job = DatasetJob(job_type="DatasetJob", kwargs=kwargs, db=db)
        job.run()
        db.refresh(entry)
        return entry


def _load_splits(dataset: Dataset) -> dict:
    splits_path = Path(dataset.file_path) / "dataset" / "splits.json"
    with open(splits_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_compute_metadata_true_writes_full_metadata(client):
    entry = _run_dataset_job(client, "iris_full_meta", compute_metadata=True)
    splits = _load_splits(entry)

    assert "column_names" in splits
    assert "total_rows" in splits
    assert splits["total_rows"] == 150
    for key in (
        "general_info",
        "numeric_stats",
        "categorical_stats",
        "text_stats",
        "quality_info",
        "correlations",
    ):
        assert key in splits, f"missing {key} when compute_metadata=True"

    shutil.rmtree(entry.file_path, ignore_errors=True)


def test_compute_metadata_false_writes_base_only(client):
    entry = _run_dataset_job(client, "iris_base_meta", compute_metadata=False)
    splits = _load_splits(entry)

    assert splits["total_rows"] == 150
    assert "column_names" in splits
    assert "nan" in splits
    assert entry.total_rows == 150
    assert entry.total_columns == 5
    for key in (
        "general_info",
        "numeric_stats",
        "categorical_stats",
        "text_stats",
        "quality_info",
        "correlations",
    ):
        assert key not in splits, f"unexpected {key} when compute_metadata=False"

    shutil.rmtree(entry.file_path, ignore_errors=True)


def test_compute_metadata_default_is_true(client):
    """Backward compatibility: omitting the flag preserves current behavior."""
    abs_file_path = Path(__file__).parent / "iris.csv"
    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        entry = Dataset(name="iris_default_meta", file_path="")
        db.add(entry)
        db.commit()
        db.refresh(entry)

        kwargs = {
            "dataset_id": entry.id,
            "url": "",
            "params": {
                "dataloader": "CSVDataLoader",
                "separator": ",",
                "name": entry.name,
                "schema": IRIS_SCHEMA,
            },
            "file_path": abs_file_path,
        }
        DatasetJob(job_type="DatasetJob", kwargs=kwargs, db=db).run()
        db.refresh(entry)

    splits = _load_splits(entry)
    assert "general_info" in splits
    shutil.rmtree(entry.file_path, ignore_errors=True)
