import json
import os

import joblib
import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import (
    Experiment,
    GlobalExplainer,
    LocalExplainer,
    Run,
)
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.explainability.global_explainer import BaseGlobalExplainer
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.job import ExplainerJob
from DashAI.back.models import BaseModel
from DashAI.back.tasks import BaseTask

input_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
output_columns = ["Species"]
splits = json.dumps(
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
)


@pytest.fixture(scope="module", name="dataset_id")
def create_dataset(client):
    """Create testing dataset 1."""
    abs_file_path = os.path.join(os.path.dirname(__file__), "iris.csv")

    with open(abs_file_path, "rb") as csv:
        response = client.post(
            "/api/v1/dataset/",
            data={
                "params": """{  "dataloader": "CSVDataLoader",
                                    "dataset_name": "DummyDataset3",
                                    "splits_in_folders": false,
                                    "splits": {
                                        "train_size": 0.8,
                                        "test_size": 0.1,
                                        "val_size": 0.1,
                                        "seed": 42,
                                        "shuffle": true
                                    },
                                    "dataloader_params": {
                                        "separator": ","
                                    }
                                }""",
                "url": "",
            },
            files={"file": ("filename", csv, "text/csv")},
        )
    return response.json()["id"]


class DummyTask(BaseTask):
    name: str = "DummyTask"

    def prepare_for_task(self, datasetdict, outputs_columns):
        return datasetdict


class DummyModel(BaseModel):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    @classmethod
    def get_schema(cls):
        return {}

    def save(self, filename):
        joblib.dump(self, filename)

    def load(self, filename):
        return

    def predict(self, x):
        return {}

    def fit(self, x, y):
        return


class DummyGlobalExplainer(BaseGlobalExplainer):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    def __init__(self, model: BaseModel) -> None:
        self.model = model
        self.explanation = None

    @classmethod
    def get_schema(cls):
        return {}

    def explain(self, dataset):
        return

    def plot(self, explanation):
        return


class DummyLocalExplainer(BaseLocalExplainer):
    COMPATIBLE_COMPONENTS = ["DummyTask"]

    def __init__(self, model: BaseModel) -> None:
        self.model = model
        self.explanation = None

    @classmethod
    def get_schema(cls):
        return {}

    def fit(self, dataset):
        return

    def explain_instance(self, instances):
        return

    def plot(self, explanation):
        return


@pytest.fixture(scope="module", autouse=True, name="test_registry")
def setup_test_registry(client):
    """Setup a test registry with test task and explainers components."""
    container = client.app.container

    test_registry = ComponentRegistry(
        initial_components=[
            DummyTask,
            DummyModel,
            DummyGlobalExplainer,
            DummyLocalExplainer,
            ExplainerJob,
        ]
    )

    with container.component_registry.override(test_registry):
        yield test_registry


@pytest.fixture(scope="module", name="experiment_id", autouse=True)
def create_experiment(client: TestClient, dataset_id: int):
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        experiment = Experiment(
            dataset_id=dataset_id,
            name="DummyExperiment",
            task_name="DummyTask",
            input_columns=input_columns,
            output_columns=output_columns,
            splits=splits,
        )
        db.add(experiment)
        db.commit()
        db.refresh(experiment)

        yield experiment.id

        db.delete(experiment)
        db.commit()
        db.close()


@pytest.fixture(scope="module", name="run_id")
def create_run_id(client: TestClient, experiment_id: int):
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        run = Run(
            experiment_id=experiment_id,
            model_name="DummyModel",
            parameters={},
            name="Run",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        yield run.id

        db.delete(run)
        db.commit()
        db.close()


# Create dummys explainers
@pytest.fixture(scope="module", name="global_explainer_id")
def create_global_explainer(client: TestClient, run_id: int):
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        global_explainer = GlobalExplainer(
            name="test_global",
            run_id=run_id,
            explainer_name="DummyGlobalExplainer",
            parameters={},
        )
        db.add(global_explainer)
        db.commit()
        db.refresh(global_explainer)

        yield global_explainer.id

        db.delete(global_explainer)
        db.commit()
        db.close()


@pytest.fixture(scope="module", name="local_explainer_id")
def create_local_explainer(client: TestClient, run_id: int, dataset_id: int):
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        local_explainer = LocalExplainer(
            name="test_local",
            run_id=run_id,
            explainer_name="DummyLocalExplainer",
            dataset_id=dataset_id,
            parameters={},
            fit_parameters={},
        )
        db.add(local_explainer)
        db.commit()
        db.refresh(local_explainer)

        yield local_explainer.id

        db.delete(local_explainer)
        db.commit()
        db.close()


def test_enqueue_explainer_jobs(
    client: TestClient, global_explainer_id: int, local_explainer_id: int
):
    response = client.post(
        "/api/v1/job/",
        json={
            "job_type": "ExplainerJob",
            "kwargs": {
                "explainer_id": global_explainer_id,
                "explainer_scope": "global",
            },
        },
    )
    assert response.status_code == 201, response.text
    created_job = response.json()
    assert created_job["kwargs"]["job_type"] == "ExplainerJob"
    assert created_job["kwargs"]["explainer_id"] == global_explainer_id

    response = client.get(f"/api/v1/job/{created_job['id']}")
    assert response.status_code == 200, response.text
    gotten_job = response.json()
    assert gotten_job["id"] == created_job["id"]
    assert gotten_job["kwargs"] == created_job["kwargs"]
    assert gotten_job["kwargs"]["job_type"] == created_job["kwargs"]["job_type"]

    response = client.post(
        "/api/v1/job/",
        json={
            "job_type": "ExplainerJob",
            "kwargs": {
                "explainer_id": local_explainer_id,
                "explainer_scope": "local",
            },
        },
    )
    assert response.status_code == 201, response.text
    created_job_2 = response.json()
    assert created_job_2["id"] != created_job["id"]

    response = client.get("/api/v1/job")
    assert response.status_code == 200, response.text
    gotten_jobs = response.json()
    assert gotten_jobs[0]["id"] == created_job["id"]
    assert gotten_jobs[1]["id"] == created_job_2["id"]


def test_execute_jobs(
    client: TestClient,
    global_explainer_id: int,
    local_explainer_id: int,
    run_id: int,
    dataset_id: int,
):
    response = client.post(
        "/api/v1/job/",
        json={
            "job_type": "ExplainerJob",
            "kwargs": {
                "explainer_id": global_explainer_id,
                "explainer_scope": "global",
            },
        },
    )
    assert response.status_code == 201, response.text

    response = client.post(
        "/api/v1/job/",
        json={
            "job_type": "ExplainerJob",
            "kwargs": {
                "explainer_id": local_explainer_id,
                "explainer_scope": "local",
            },
        },
    )
    assert response.status_code == 201, response.text

    response = client.get(f"/api/v1/explainer/global/?run_id={run_id}")
    data = response.json()
    for explainer in data:
        assert explainer["status"] == 1

    response = client.get(f"/api/v1/explainer/local/?run_id={run_id}")
    data = response.json()
    for explainer in data:
        assert explainer["status"] == 1

    response = client.post("/api/v1/job/start/?stop_when_queue_empties=True")
    assert response.status_code == 202, response.text

    response = client.get(f"/api/v1/explainer/global/?run_id={run_id}")
    data = response.json()
    for explainer in data:
        assert explainer["status"] == 3

    response = client.get(f"/api/v1/explainer/local/?run_id={run_id}")
    data = response.json()
    for explainer in data:
        assert explainer["status"] == 3


def test_job_with_wrong_explainer(client: TestClient):
    response = client.post(
        "/api/v1/job/",
        json={
            "job_type": "ExplainerJob",
            "kwargs": {"explainer_id": 31415, "explainer_scope": "local"},
        },
    )
    assert response.status_code == 500, response.text
