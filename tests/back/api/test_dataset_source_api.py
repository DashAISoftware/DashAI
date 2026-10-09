"""Tests for the dataset_source API endpoints."""

import os
import shutil
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import DatafileStatus
from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader
from DashAI.back.dataset_sources.base_dataset_source import (
    BaseDatasetSource,
    DatasetEntry,
    SearchPage,
)
from DashAI.back.dependencies.database.models import Datafile, Dataset
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.job.dataset_job import DatasetJob


class MockDataLoader(BaseDataLoader):
    """Minimal DataLoader for testing the hub import path."""

    name = "MockDataLoader"

    @classmethod
    def get_schema(cls):
        return {}

    def load_data(
        self,
        filepath_or_buffer: str,
        temp_path: str,
        params: Dict[str, Any],
        n_sample=None,
    ):
        import pandas as pd

        from DashAI.back.dataloaders.classes.dashai_dataset import (
            to_dashai_dataset,
        )

        dataset_df = pd.read_csv(filepath_or_buffer)
        return to_dashai_dataset(dataset_df)


class CachingDataLoader(MockDataLoader):
    """DataLoader that leaves a cache file in temp_path, like CSVDataLoader."""

    name = "CachingDataLoader"

    def load_data(self, filepath_or_buffer, temp_path, params, n_sample=None):
        with open(os.path.join(temp_path, "loader-cache.arrow"), "w") as f:
            f.write("cache")
        return super().load_data(filepath_or_buffer, temp_path, params, n_sample)


class MockDatasetSource(BaseDatasetSource):
    DISPLAY_NAME = "Mock Source"
    DESCRIPTION = "Mock for testing"

    def search(self, query, limit=20, cursor=None, **filters):
        if query == "error":
            return SearchPage()
        return SearchPage(
            entries=[
                DatasetEntry(
                    id="mock/dataset",
                    name="Mock Dataset",
                    description="A mock dataset",
                    tags=["tabular"],
                    size_bytes=1024,
                    url="https://mock.example.com/mock-dataset",
                    source="MockDatasetSource",
                )
            ]
        )

    def download_dataset(self, dataset_id, temp_path):
        csv_path = os.path.join(temp_path, "mock.csv")
        with open(csv_path, "w") as f:
            f.write("col_a,col_b\n1,x\n2,y\n3,z\n")
        return csv_path

    @classmethod
    def get_schema(cls):
        return {}


@pytest.fixture(autouse=True, name="test_registry_hub")
def setup_test_registry(client, monkeypatch):
    container = client.app.container
    test_registry = ComponentRegistry(
        initial_components=[MockDatasetSource, MockDataLoader, CachingDataLoader]
    )
    monkeypatch.setitem(container._services, "component_registry", test_registry)
    return test_registry


@pytest.fixture
def ready_datafile(client, tmp_path):
    """Create a READY Datafile record with a real CSV on disk."""
    local_dir = tmp_path / "datafile"
    local_dir.mkdir()
    (local_dir / "mock.csv").write_text("col_a,col_b\n1,x\n2,y\n3,z\n")

    resp = client.post(
        "/api/v1/datafile/",
        json={
            "source_name": "MockDatasetSource",
            "dataset_id": "mock/dataset",
            "name": "Mock Dataset",
        },
    )
    assert resp.status_code == 201
    datafile_id = resp.json()["id"]

    session_factory = client.app.container._services["session_factory"]
    with session_factory() as db:
        row = db.get(Datafile, datafile_id)
        row.status = DatafileStatus.READY
        row.local_path = str(local_dir)
        db.commit()

    return datafile_id


def test_list_sources(client: TestClient):
    response = client.get("/api/v1/component/?select_types=DatasetSource")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "MockDatasetSource"
    assert data[0]["type"] == "DatasetSource"
    assert "compatible_components" not in data[0]


def test_search_returns_entries(client: TestClient):
    response = client.get(
        "/api/v1/dataset-source/MockDatasetSource/search?q=test&limit=5"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == "mock/dataset"
    assert data["results"][0]["name"] == "Mock Dataset"


def test_search_empty_result(client: TestClient):
    response = client.get("/api/v1/dataset-source/MockDatasetSource/search?q=error")
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []


def test_search_unknown_source(client: TestClient):
    response = client.get("/api/v1/dataset-source/UnknownSource/search?q=test")
    assert response.status_code == 404


def test_post_preview_with_dataloader(client: TestClient, ready_datafile):
    response = client.post(
        "/api/v1/dataset-source/MockDatasetSource/mock%2Fdataset/preview",
        json={
            "dataloader": "MockDataLoader",
            "params": {},
            "n_rows": 3,
            "datafile_id": ready_datafile,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "sample" in data
    assert "inferred_types" in data
    assert "preview_row_count" in data
    assert len(data["sample"]) == 3


def test_post_preview_missing_datafile_id(client: TestClient):
    response = client.post(
        "/api/v1/dataset-source/MockDatasetSource/mock%2Fdataset/preview",
        json={"dataloader": "MockDataLoader", "params": {}, "n_rows": 3},
    )
    assert response.status_code == 422


def test_import_endpoint_creates_dataset_and_job(client: TestClient):
    """POST import creates a Dataset record and enqueues a DatasetJob."""
    create_resp = client.post("/api/v1/dataset/", json={"name": "hub_import_test"})
    assert create_resp.status_code == 201
    dataset_id = create_resp.json()["id"]

    response = client.post(
        "/api/v1/dataset-source/MockDatasetSource/mock%2Fdataset/import",
        json={
            "dataset_id": dataset_id,
            "params": {},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert data["dataset_id"] == dataset_id


def test_import_endpoint_unknown_source(client: TestClient):
    response = client.post(
        "/api/v1/dataset-source/Unknown/some%2Fdataset/import",
        json={"dataset_id": 999, "params": {}},
    )
    assert response.status_code == 404


def _datafile_contents(client, datafile_id):
    session_factory = client.app.container._services["session_factory"]
    with session_factory() as db:
        local_path = db.get(Datafile, datafile_id).local_path
    return sorted(os.listdir(local_path))


def test_preview_keeps_loader_cache_out_of_datafile(client, ready_datafile):
    response = client.post(
        "/api/v1/dataset-source/MockDatasetSource/mock%2Fdataset/preview",
        json={
            "dataloader": "CachingDataLoader",
            "params": {},
            "n_rows": 3,
            "datafile_id": ready_datafile,
        },
    )
    assert response.status_code == 200
    assert _datafile_contents(client, ready_datafile) == ["mock.csv"]


def test_import_job_keeps_loader_cache_out_of_datafile(client, ready_datafile):
    session_factory = client.app.container._services["session_factory"]
    with session_factory() as db:
        entry = Dataset(name="hub_cache_test", file_path="")
        db.add(entry)
        db.commit()
        db.refresh(entry)
        job = DatasetJob(
            job_type="DatasetJob",
            kwargs={
                "dataset_id": entry.id,
                "source_name": "MockDatasetSource",
                "params": {
                    "datafile_id": ready_datafile,
                    "dataloader": "CachingDataLoader",
                    "dataloader_params": {},
                    "compute_metadata": False,
                },
            },
            db=db,
        )
        job.run()
        db.refresh(entry)
        assert entry.total_rows == 3

    assert _datafile_contents(client, ready_datafile) == ["mock.csv"]
    shutil.rmtree(entry.file_path, ignore_errors=True)
