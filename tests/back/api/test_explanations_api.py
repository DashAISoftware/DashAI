import json

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import (
    Dataset,
    Experiment,
    GlobalExplainer,
    LocalExplainer,
    Run,
)

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
def create_dummy_dataset(client: TestClient):
    """Create a dummy dataset for the experiments."""
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        dummy_dataset = Dataset(
            name="DummyDataset2",
            file_path="dummy.csv",
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


@pytest.fixture(scope="module", name="run_id_1")
def create_run_id_1(client: TestClient, experiment_id: int):
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
def create_run_id_2(client: TestClient, experiment_id: int):
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


def test_create_global_explainer(client: TestClient, run_id_1: int, run_id_2: int):
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        response = client.post(
            "/api/v1/explainer/global",
            json={
                "name": "test_1",
                "run_id": run_id_1,
                "explainer_name": "PartialDependence",
                "parameters": {
                    "categorical_features": None,
                    "grid_resolution": 50,
                    "lower_percentile": 2,
                    "upper_percentile": 1,
                },
            },
        )
        assert response.status_code == 201, response.text

        response = client.post(
            "/api/v1/explainer/global",
            json={
                "name": "test_2",
                "run_id": run_id_2,
                "explainer_name": "PermutationFeatureImportance",
                "parameters": {
                    "scoring": "accuracy",
                    "n_repeats": 5,
                    "random_state": None,
                    "max_samples": 1,
                },
            },
        )
        assert response.status_code == 201, response.text

        explainer_1 = db.get(GlobalExplainer, 1)
        explainer_2 = db.get(GlobalExplainer, 2)
        db.delete(explainer_1)
        db.delete(explainer_2)
        db.commit()
        db.close()


def test_create_local_explainer(client: TestClient, dataset_id: int, run_id_1: int):
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        response = client.post(
            "/api/v1/explainer/local",
            json={
                "name": "test_1",
                "run_id": run_id_1,
                "dataset_id": dataset_id,
                "explainer_name": "KernelShap",
                "parameters": {
                    "link": "identity",
                },
                "fit_parameters": {
                    "sample_background_data": True,
                    "n_background_samples": 50,
                    "sampling_method": "kmeans",
                    "categorical_features": False,
                },
            },
        )
        assert response.status_code == 201, response.text

        explainer = db.get(LocalExplainer, 1)
        db.delete(explainer)
        db.commit()
        db.close()


def test_get_global_explainers_by_run_id(client: TestClient, run_id_1: int):
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        response = client.post(
            "/api/v1/explainer/global",
            json={
                "name": "test_1",
                "run_id": run_id_1,
                "explainer_name": "PartialDependence",
                "parameters": {
                    "categorical_features": None,
                    "grid_resolution": 50,
                    "lower_percentile": 2,
                    "upper_percentile": 1,
                },
            },
        )
        assert response.status_code == 201, response.text

        response = client.post(
            "/api/v1/explainer/global",
            json={
                "name": "test_2",
                "run_id": run_id_1,
                "explainer_name": "PermutationFeatureImportance",
                "parameters": {
                    "scoring": "accuracy",
                    "n_repeats": 5,
                    "random_state": None,
                    "max_samples": 1,
                },
            },
        )
        assert response.status_code == 201, response.text

        response = client.get("/api/v1/explainer/global/?run_id=1")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data[0]["name"] == "test_1"
        assert data[0]["run_id"] == run_id_1
        assert data[0]["explainer_name"] == "PartialDependence"
        assert data[0]["parameters"] == {
            "categorical_features": None,
            "grid_resolution": 50,
            "lower_percentile": 2,
            "upper_percentile": 1,
        }

        assert data[1]["name"] == "test_2"
        assert data[1]["run_id"] == run_id_1
        assert data[1]["explainer_name"] == "PermutationFeatureImportance"
        assert data[1]["parameters"] == {
            "scoring": "accuracy",
            "n_repeats": 5,
            "random_state": None,
            "max_samples": 1,
        }

        explainer_1 = db.get(GlobalExplainer, 1)
        explainer_2 = db.get(GlobalExplainer, 2)
        db.delete(explainer_1)
        db.delete(explainer_2)
        db.commit()
        db.close()


def test_get_local_explainers_by_run_id(
    client: TestClient, dataset_id: int, run_id_1: int
):
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        response = client.post(
            "/api/v1/explainer/local",
            json={
                "name": "test_1",
                "run_id": run_id_1,
                "dataset_id": dataset_id,
                "explainer_name": "KernelShap",
                "parameters": {
                    "link": "identity",
                },
                "fit_parameters": {
                    "sample_background_data": True,
                    "n_background_samples": 50,
                    "sampling_method": "kmeans",
                    "categorical_features": False,
                },
            },
        )
        assert response.status_code == 201, response.text

        response = client.get("/api/v1/explainer/local/?run_id=1")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data[0]["name"] == "test_1"
        assert data[0]["run_id"] == run_id_1
        assert data[0]["explainer_name"] == "KernelShap"
        assert data[0]["parameters"] == {
            "link": "identity",
        }
        assert data[0]["fit_parameters"] == {
            "sample_background_data": True,
            "n_background_samples": 50,
            "sampling_method": "kmeans",
            "categorical_features": False,
        }

        explainer = db.get(LocalExplainer, 1)
        db.delete(explainer)
        db.commit()
        db.close()


def test_get_global_explanation(client: TestClient, run_id_1: int):
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        response = client.post(
            "/api/v1/explainer/global",
            json={
                "name": "test_1",
                "run_id": run_id_1,
                "explainer_name": "PartialDependence",
                "parameters": {
                    "categorical_features": None,
                    "grid_resolution": 50,
                    "lower_percentile": 2,
                    "upper_percentile": 1,
                },
            },
        )
        assert response.status_code == 201, response.text

        response = client.get("/api/v1/explainer/global/1")
        assert response.status_code == 404, response.text

        # Get plot
        response = client.get("/api/v1/explainer/global/plot/1")
        assert response.status_code == 404, response.texts

        explainer = db.get(GlobalExplainer, 1)
        db.delete(explainer)
        db.commit()
        db.close()


def test_get_local_explanation(client: TestClient, dataset_id: int, run_id_1: int):
    container = client.app.container
    session = container.db.provided().session

    with session() as db:
        response = client.post(
            "/api/v1/explainer/local",
            json={
                "name": "test_1",
                "run_id": run_id_1,
                "dataset_id": dataset_id,
                "explainer_name": "KernelShap",
                "parameters": {
                    "link": "identity",
                },
                "fit_parameters": {
                    "sample_background_data": True,
                    "n_background_samples": 50,
                    "sampling_method": "kmeans",
                    "categorical_features": False,
                },
            },
        )
        assert response.status_code == 201, response.text

        response = client.get("/api/v1/explainer/local/1")
        assert response.status_code == 404, response.text

        # Get plot
        response = client.get("/api/v1/explainer/local/plot/1")
        assert response.status_code == 404, response.text

        explainer = db.get(LocalExplainer, 1)
        db.delete(explainer)
        db.commit()
        db.close()


def test_delete_global_explainer(client: TestClient, run_id_1: int):
    response = client.post(
        "/api/v1/explainer/global",
        json={
            "name": "test_1",
            "run_id": run_id_1,
            "explainer_name": "PartialDependence",
            "parameters": {
                "categorical_features": None,
                "grid_resolution": 50,
                "lower_percentile": 2,
                "upper_percentile": 1,
            },
        },
    )
    assert response.status_code == 201, response.text

    response = client.delete("/api/v1/explainer/global/1")
    assert response.status_code == 200, response.text


def test_delete_local_explainer(client: TestClient, dataset_id: int, run_id_1: int):
    response = client.post(
        "/api/v1/explainer/local",
        json={
            "name": "test_2",
            "run_id": run_id_1,
            "explainer_name": "KernelShap",
            "dataset_id": dataset_id,
            "parameters": {
                "link": "identity",
            },
            "fit_parameters": {
                "sample_background_data": False,
                "categorical_features": True,
            },
        },
    )
    assert response.status_code == 201, response.text

    response = client.delete("/api/v1/explainer/local/1")
    assert response.status_code == 200, response.text


def test_update_explainer(client: TestClient):
    response = client.patch("/api/v1/explainer/")
    assert response.status_code == 501, response.text
