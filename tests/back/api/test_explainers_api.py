import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from DashAI.back.core.config import settings
from DashAI.back.database.models import Experiment, Run


@pytest.fixture(scope="module", name="dataset_id")
def fixture_dataset_id(client: TestClient):
    script_dir = os.path.dirname(__file__)
    test_dataset = "iris.csv"
    abs_file_path = os.path.join(script_dir, test_dataset)
    with open(abs_file_path, "rb") as csv_file:
        response = client.post(
            "/api/v1/dataset/",
            data={
                "params": """{  "task_name": "TabularClassificationTask",
                                    "dataloader": "CSVDataLoader",
                                    "dataset_name": "test_iris",
                                    "outputs_columns": ["Species"],
                                    "splits_in_folders": false,
                                    "splits": {
                                        "train_size": 0.5,
                                        "test_size": 0.2,
                                        "val_size": 0.3,
                                        "seed": 42,
                                        "shuffle": false,
                                        "stratify": false
                                    },
                                    "dataloader_params": {
                                        "data_key": "data"
                                    }
                                }""",
                "url": "",
            },
            files={"file": ("filename", csv_file, "text/csv")},
        )
    assert response.status_code == 201, response.text
    dataset = response.json()
    yield dataset["id"]
    response = client.delete(f"/api/v1/dataset/{dataset['id']}")
    assert response.status_code == 204, response.text


@pytest.fixture(scope="module", name="experiment_id")
def fixture_experiment_id(session: sessionmaker, dataset_id: int):
    db = session()
    dummy_experiment = Experiment(
        dataset_id=dataset_id,
        task_name="TabularClassificationTask",
        name="Test Experiment",
    )
    db.add(dummy_experiment)
    db.commit()
    db.refresh(dummy_experiment)
    yield dummy_experiment.id

    db.delete(dummy_experiment)
    db.commit()


@pytest.fixture(scope="module", name="run_id")
def fixture_run_id(session: sessionmaker, experiment_id: int):
    db = session()
    run = Run(
        experiment_id=experiment_id,
        model_name="RandomForestClassifier",
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


def test_create_explainer(client: TestClient, run_id: int):
    response = client.post(
        "/api/v1/explainer/",
        data=f"""{{"run_id": {run_id},
            "explainer_name": "PartialDependence",
            "parameters": {{
                "grid_resolution": 100,
                "percentiles": [0.1, 0.6]
            }}
        }}""",
    )
    assert response.status_code == 201, response.text


def test_get_explainer(client: TestClient, run_id: int, dataset_id: int):
    response = client.get("/api/v1/explainer/1")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["run_id"] == run_id
    assert data["dataset_id"] == dataset_id
    assert data["explainer_name"] == "PartialDependence"
    assert data["explainer_path"] == os.path.join(
        settings.USER_EXPLAINER_PATH, f"{1}.pkl"
    )


def test_get_explainers(client: TestClient, run_id: int, dataset_id: int):
    response = client.get("/api/v1/explainer")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["run_id"] == run_id
    assert data[0]["dataset_id"] == dataset_id
    assert data[0]["explainer_name"] == "PartialDependence"
    assert data[0]["explainer_path"] == os.path.join(
        settings.USER_EXPLAINER_PATH, f"{1}.pkl"
    )
    response = client.get("/api/v1/explainer/?run_id=1")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["run_id"] == run_id
    assert data[0]["dataset_id"] == dataset_id
    assert data[0]["explainer_name"] == "PartialDependence"
    assert data[0]["explainer_path"] == os.path.join(
        settings.USER_EXPLAINER_PATH, f"{1}.pkl"
    )


def test_get_wrong_explainer(client: TestClient):
    response = client.get("/api/v1/explainer/666")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Explainer not found"}'


def test_delete_explainer(client: TestClient):
    response = client.delete("/api/v1/explainer/1")
    assert response.status_code == 204, response.text


def test_modify_explainer(client: TestClient):
    response = client.patch("/api/v1/explainer/")
    assert response.status_code == 501, response.text
