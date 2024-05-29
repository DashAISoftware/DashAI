import json
import os

import joblib
import pytest
from fastapi.testclient import TestClient

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dependencies.database.models import Experiment, Run
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.job.model_job import ModelJob
from DashAI.back.metrics import BaseMetric
from DashAI.back.models import BaseModel
from DashAI.back.tasks import BaseTask


class DummyTask(BaseTask):
    name: str = "DummyTask"

    def prepare_for_task(self, dataset, output_columns):
        return dataset


class DummyModel(BaseModel):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    def save(self, filename):
        joblib.dump(self, filename)

    def load(self, filename):
        return

    def predict(self, x):
        return {}

    def fit(self, x, y):
        return


class FailDummyModel(BaseModel):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    def save(self, filename):
        return

    def load(self, filename):
        return

    def predict(self, x):
        return {}

    def fit(self, x, y):
        raise Exception("Always fails")


class DummyMetric(BaseMetric):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    @staticmethod
    def score(true_labels: list, probs_pred_labels: list):
        return 1


@pytest.fixture(autouse=True, name="test_registry")
def setup_test_registry(client, monkeypatch: pytest.MonkeyPatch):
    """Setup a test registry with test task, dataloader and model components."""
    container = client.app.container

    test_registry = ComponentRegistry(
        initial_components=[
            DummyTask,
            DummyModel,
            FailDummyModel,
            DummyMetric,
            CSVDataLoader,
            ModelJob,
        ]
    )

    monkeypatch.setitem(
        container._services,
        "component_registry",
        test_registry,
    )
    return test_registry


@pytest.fixture(scope="module", name="dataset_id", autouse=True)
def fixture_dataset_id(client: TestClient):
    script_dir = os.path.dirname(__file__)
    test_dataset = "iris.csv"
    abs_file_path = os.path.join(script_dir, test_dataset)
    with open(abs_file_path, "rb") as csv:
        response = client.post(
            "/api/v1/dataset/",
            data={
                "params": """{  "dataloader": "CSVDataLoader",
                                    "name": "test_csv3",
                                    "splits_in_folders": false,
                                    "splits": {
                                        "train_size": 0.5,
                                        "test_size": 0.2,
                                        "val_size": 0.3
                                    },
                                    "separator": ",",
                                    "more_options": {
                                        "seed": 42,
                                        "shuffle": true,
                                        "stratify": false
                                    }
                                }""",
                "url": "",
            },
            files={"file": ("filename", csv, "text/csv")},
        )
    assert response.status_code == 201, response.text
    dataset = response.json()

    yield dataset["id"]

    response = client.delete(f"/api/v1/dataset/{dataset['id']}")
    assert response.status_code == 204, response.text


@pytest.fixture(scope="module", name="experiment_id", autouse=True)
def create_experiment(client: TestClient, dataset_id: int):
    container = client.app.container
    session = container["session_factory"]

    with session() as db:
        experiment = Experiment(
            dataset_id=dataset_id,
            name="DummyExperiment",
            task_name="DummyTask",
            input_columns=[],
            output_columns=[],
            splits=json.dumps(
                {
                    "train": 0.5,
                    "test": 0.2,
                    "validation": 0.3,
                    "is_random": True,
                    "has_changed": True,
                    "seed": 42,
                    "shuffle": True,
                    "stratify": False,
                }
            ),
        )
        db.add(experiment)
        db.commit()
        db.refresh(experiment)

        yield experiment.id

        db.delete(experiment)
        db.commit()
        db.close()


@pytest.fixture(scope="module", name="run_id", autouse=True)
def create_run(client: TestClient, experiment_id: int):
    response = client.post(
        "/api/v1/run/",
        json={
            "experiment_id": experiment_id,
            "model_name": "DummyModel",
            "name": "DummyRun",
            "parameters": {},
            "description": "This is a test run",
        },
    )
    assert response.status_code == 201, response.text
    run = response.json()

    yield run["id"]

    response = client.delete(f"/api/v1/run/{run['id']}")
    assert response.status_code == 204, response.text


@pytest.fixture(scope="module", name="failed_run_id", autouse=True)
def create_failed_run(client: TestClient, experiment_id: int):
    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        run = Run(
            experiment_id=experiment_id,
            model_name="FailDummyModel",
            parameters={},
            name="DummyRun2",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        yield run.id

        db.delete(run)
        db.commit()
        db.close()


def test_enqueue_jobs(client: TestClient, run_id: int):
    response = client.post(
        "/api/v1/job/", json={"job_type": "ModelJob", "kwargs": {"run_id": run_id}}
    )
    assert response.status_code == 201, response.text
    created_job = response.json()
    assert created_job["kwargs"]["job_type"] == "ModelJob"
    assert created_job["kwargs"]["run_id"] == run_id

    response = client.get(f"/api/v1/job/{created_job['id']}")
    assert response.status_code == 200, response.text
    gotten_job = response.json()
    assert gotten_job["id"] == created_job["id"]
    assert gotten_job["kwargs"] == created_job["kwargs"]
    assert gotten_job["kwargs"]["job_type"] == created_job["kwargs"]["job_type"]

    response = client.post(
        "/api/v1/job/", json={"job_type": "ModelJob", "kwargs": {"run_id": run_id}}
    )
    assert response.status_code == 201, response.text
    created_job_2 = response.json()
    assert created_job_2["id"] != created_job["id"]

    response = client.get("/api/v1/job")
    assert response.status_code == 200, response.text
    gotten_jobs = response.json()
    assert gotten_jobs[0]["id"] == created_job["id"]
    assert gotten_jobs[1]["id"] == created_job_2["id"]


def test_get_all_jobs(client: TestClient, run_id: int):
    # Get all the experiments available in the back
    response = client.get("/api/v1/job")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["kwargs"]["run_id"] == run_id
    assert data[1]["kwargs"]["run_id"] == run_id


def test_get_wrong_job(client: TestClient):
    # Try to retrieve a non-existent experiment an get an error
    response = client.get("/api/v1/job/31415")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Job not found"}'


def test_cancel_jobs(client: TestClient):
    response = client.get("/api/v1/job")
    assert response.status_code == 200, response.text
    gotten_jobs = response.json()

    response = client.delete(f"/api/v1/job/?job_id={gotten_jobs[0]['id']}")
    assert response.status_code == 204, response.text

    response = client.get("/api/v1/job")
    assert response.status_code == 200, response.text
    jobs = response.json()
    assert len(jobs) == len(gotten_jobs) - 1
    assert jobs[0]["id"] != gotten_jobs[0]["id"]
    assert jobs[0]["id"] == gotten_jobs[1]["id"]

    response = client.delete(f"/api/v1/job/?job_id={gotten_jobs[1]['id']}")
    assert response.status_code == 204, response.text

    response = client.get("/api/v1/job")
    assert response.status_code == 200, response.text
    jobs = response.json()
    assert jobs == []


def test_execute_jobs(client: TestClient, run_id: int, failed_run_id: int):
    response = client.post(
        "/api/v1/job/", json={"job_type": "ModelJob", "kwargs": {"run_id": run_id}}
    )
    assert response.status_code == 201, response.text

    response = client.post(
        "/api/v1/job/",
        json={"job_type": "ModelJob", "kwargs": {"run_id": failed_run_id}},
    )
    assert response.status_code == 201, response.text

    response = client.get("/api/v1/run")
    data = response.json()
    for run in data:
        assert run["status"] == 1
        assert run["delivery_time"] is not None
        assert run["start_time"] is None
        assert run["end_time"] is None

    response = client.post("/api/v1/job/start/?stop_when_queue_empties=True")
    assert response.status_code == 202, response.text

    response = client.get(f"/api/v1/run/{run_id}")
    data = response.json()
    print(data["status"])
    assert data["status"] == 3
    assert isinstance(data["train_metrics"], dict)
    assert "DummyMetric" in data["train_metrics"]
    assert data["train_metrics"]["DummyMetric"] == 1
    assert data["train_metrics"] == data["validation_metrics"]
    assert data["train_metrics"] == data["test_metrics"]
    assert data["run_path"] is not None
    assert os.path.exists(data["run_path"])
    assert data["status"] == 3
    assert data["delivery_time"] is not None
    assert data["start_time"] is not None
    assert data["end_time"] is not None

    response = client.get(f"/api/v1/run/{failed_run_id}")
    data = response.json()
    assert data["status"] == 4
    assert data["delivery_time"] is not None
    assert data["start_time"] is not None
    assert data["end_time"] is None


def test_job_with_wrong_run(client: TestClient):
    response = client.post(
        "/api/v1/job/", json={"job_type": "ModelJob", "kwargs": {"run_id": 31415}}
    )
    assert response.status_code == 500, response.text
