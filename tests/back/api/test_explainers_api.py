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


@pytest.fixture(scope="module", name="run_id_1")
def fixture_run_id_1(session: sessionmaker, experiment_id: int):
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


@pytest.fixture(scope="module", name="run_id_2")
def fixture_run_id_2(session: sessionmaker, experiment_id: int):
    db = session()
    run = Run(
        experiment_id=experiment_id,
        model_name="SVC",
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


def test_create_explainer(client: TestClient, run_id_1: int, run_id_2):
    print(f"rund_id_1: {run_id_1}, run_id_2: {run_id_2}")
    response = client.post(
        "/api/v1/explainer/",
        json={
            "name": "test_explainer_1",
            "run_id": run_id_1,
            "explainer": "PartialDependence",
            "parameters": {"grid_resolution": 100, "percentiles": [0.1, 0.6]},
        },
    )
    assert response.status_code == 201, response.text

    response = client.post(
        "/api/v1/explainer/",
        json={
            "name": "test_explainer_2",
            "run_id": run_id_1,
            "explainer": "PartialDependence",
            "parameters": {"grid_resolution": 50, "percentiles": [0.1, 0.2]},
        },
    )

    response = client.post(
        "/api/v1/explainer/",
        json={
            "name": "test_explainer_3",
            "run_id": run_id_2,
            "explainer": "PartialDependence",
            "parameters": {"grid_resolution": 50, "percentiles": [0.1, 0.55]},
        },
    )


def test_get_explainer_by_id(
    client: TestClient, run_id_1: int, run_id_2: int, dataset_id: int
):
    response = client.get("/api/v1/explainer/1")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "test_explainer_1"
    assert data["run_id"] == run_id_1
    assert data["dataset_id"] == dataset_id
    assert data["explainer"] == "PartialDependence"
    assert data["explainer_path"] == os.path.join(
        settings.USER_EXPLAINER_PATH, f"{1}.pkl"
    )
    response = client.get("/api/v1/explainer/3")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "test_explainer_3"
    assert data["run_id"] == run_id_2
    assert data["dataset_id"] == dataset_id
    assert data["explainer"] == "PartialDependence"
    assert data["explainer_path"] == os.path.join(
        settings.USER_EXPLAINER_PATH, f"{3}.pkl"
    )


def test_get_explainers(
    client: TestClient, run_id_1: int, run_id_2: int, dataset_id: int
):
    response = client.get("/api/v1/explainer")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["name"] == "test_explainer_1"
    assert data[0]["run_id"] == run_id_1
    assert data[0]["dataset_id"] == dataset_id
    assert data[0]["explainer"] == "PartialDependence"
    assert data[0]["explainer_path"] == os.path.join(
        settings.USER_EXPLAINER_PATH, f"{1}.pkl"
    )
    assert data[1]["name"] == "test_explainer_2"
    assert data[1]["run_id"] == run_id_1
    assert data[1]["dataset_id"] == dataset_id
    assert data[1]["explainer"] == "PartialDependence"
    assert data[1]["explainer_path"] == os.path.join(
        settings.USER_EXPLAINER_PATH, f"{2}.pkl"
    )

    assert data[2]["name"] == "test_explainer_3"
    assert data[2]["run_id"] == run_id_2
    assert data[2]["dataset_id"] == dataset_id
    assert data[2]["explainer"] == "PartialDependence"
    assert data[2]["explainer_path"] == os.path.join(
        settings.USER_EXPLAINER_PATH, f"{3}.pkl"
    )


def test_get_explainer_by_run_id(client: TestClient, run_id_1: int, dataset_id: int):
    response = client.get("/api/v1/explainer/?run_id=1")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["name"] == "test_explainer_1"
    assert data[0]["run_id"] == run_id_1
    assert data[0]["dataset_id"] == dataset_id
    assert data[0]["explainer"] == "PartialDependence"
    assert data[0]["explainer_path"] == os.path.join(
        settings.USER_EXPLAINER_PATH, f"{1}.pkl"
    )
    assert data[1]["name"] == "test_explainer_2"
    assert data[1]["run_id"] == run_id_1
    assert data[1]["dataset_id"] == dataset_id
    assert data[1]["explainer"] == "PartialDependence"
    assert data[1]["explainer_path"] == os.path.join(
        settings.USER_EXPLAINER_PATH, f"{2}.pkl"
    )


def test_get_not_found_explainer(client: TestClient):
    response = client.get("/api/v1/explainer/666")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Explainer not found"}'


def test_delete_explainer(client: TestClient):
    response = client.delete("/api/v1/explainer/1")
    assert response.status_code == 204, response.text


def test_modify_explainer(client: TestClient):
    response = client.patch("/api/v1/explainer/")
    assert response.status_code == 501, response.text
