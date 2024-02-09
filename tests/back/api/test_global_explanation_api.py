import json

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset, Experiment, Run


@pytest.fixture(scope="module", name="dataset_id")
def create_dummy_dataset(client: TestClient):
    """Create a dummy dataset for the experiments."""
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        dummy_dataset = Dataset(
            name="DummyDataset",
            task_name="TabularClassificationTask",
            file_path="dummy.csv",
            feature_names=json.dumps([]),
        )
        db.add(dummy_dataset)
        db.commit()
        db.refresh(dummy_dataset)

        yield dummy_dataset.id

        db.delete(dummy_dataset)
        db.commit()


@pytest.fixture(scope="module", name="experiment_id", autouse=True)
def create_experiment(client: TestClient, dataset_id: int):
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        experiment = Experiment(
            dataset_id=dataset_id,
            name="DummyExperiment",
            task_name="DummyTask",
        )
        db.add(experiment)
        db.commit()
        db.refresh(experiment)

        yield experiment.id

        db.delete(experiment)
        db.commit()
        db.close()


@pytest.fixture(scope="module", name="run_id_1")
def fixture_run_id_1(client: TestClient, experiment_id: int):
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
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
def fixture_run_id_2(client: TestClient, experiment_id: int):
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
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


def test_create_global_explanation(client: TestClient, run_id_1: int, run_id_2: int):
    response = client.post(
        "/api/v1/global-explanation/",
        json={
            "name": "test_1",
            "run_id": run_id_1,
            "explainer_name": "PartialDependence",
            "parameters": {"grid_resolution": 100, "percentiles": [0.1, 0.6]},
        },
    )
    assert response.status_code == 201, response.text

    response = client.post(
        "/api/v1/global-explanation/",
        json={
            "name": "test_2",
            "run_id": run_id_1,
            "explainer_name": "PartialDependence",
            "parameters": {"grid_resolution": 50, "percentiles": [0.1, 0.2]},
        },
    )
    assert response.status_code == 201, response.text

    response = client.post(
        "/api/v1/global-explanation/",
        json={
            "name": "test_3",
            "run_id": run_id_2,
            "explainer_name": "PartialDependence",
            "parameters": {"grid_resolution": 50, "percentiles": [0.1, 0.55]},
        },
    )
    assert response.status_code == 201, response.text


def test_get_global_explanation_by_id(
    client: TestClient, run_id_1: int, run_id_2: int, dataset_id: int
):
    response = client.post(
        "/api/v1/global-explanation/",
        json={
            "name": "test_1",
            "run_id": run_id_1,
            "explainer_name": "PartialDependence",
            "parameters": {"grid_resolution": 100, "percentiles": [0.1, 0.6]},
        },
    )
    assert response.status_code == 201, response.text

    response = client.get("/api/v1/global-explanation/1")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "test_1"
    assert data["run_id"] == run_id_1
    assert data["explainer_name"] == "PartialDependence"
    assert data["parameters"] == {"grid_resolution": 100, "percentiles": [0.1, 0.6]}


def test_get_explainer_by_run_id(client: TestClient, run_id_1: int):
    response = client.post(
        "/api/v1/global-explanation/",
        json={
            "name": "test_1",
            "run_id": run_id_1,
            "explainer_name": "PartialDependence",
            "parameters": {"grid_resolution": 50, "percentiles": [0.1, 0.2]},
        },
    )
    assert response.status_code == 201, response.text

    response = client.post(
        "/api/v1/global-explanation/",
        json={
            "name": "test_2",
            "run_id": run_id_1,
            "explainer_name": "PartialDependence",
            "parameters": {"grid_resolution": 100, "percentiles": [0.1, 0.2]},
        },
    )
    assert response.status_code == 201, response.text

    response = client.get("/api/v1/global-explanation/?run_id=1")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["name"] == "test_1"
    assert data[0]["run_id"] == run_id_1
    assert data[0]["explainer_name"] == "PartialDependence"
    assert data[0]["parameters"] == {"grid_resolution": 50, "percentiles": [0.1, 0.2]}

    assert data[1]["name"] == "test_2"
    assert data[1]["run_id"] == run_id_1
    assert data[1]["explainer_name"] == "PartialDependence"
    assert data[1]["parameters"] == {"grid_resolution": 100, "percentiles": [0.1, 0.2]}


def test_get_not_found_explainer(client: TestClient):
    response = client.get("/api/v1/global-explanation/666")
    assert response.status_code == 404, response.text


def test_delete_explainer(client: TestClient, run_id_1: int):
    response = client.post(
        "/api/v1/global-explanation/",
        json={
            "name": "test_2",
            "run_id": run_id_1,
            "explainer_name": "PartialDependence",
            "parameters": {"grid_resolution": 100, "percentiles": [0.1, 0.2]},
        },
    )
    assert response.status_code == 201, response.text

    response = client.delete("/api/v1/global-explanation/1")
    assert response.status_code == 200, response.text


def test_modify_explainer(client: TestClient):
    response = client.patch("/api/v1/global-explanation")
    assert response.status_code == 501, response.text
