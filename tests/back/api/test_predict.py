import json
import os

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Experiment, Run


@pytest.fixture(scope="module", name="dataset_id")
def create_dataset(client: TestClient):
    script_dir = os.path.dirname(__file__)
    test_dataset = "irisDataset.json"
    abs_file_path = os.path.join(script_dir, test_dataset)
    with open(abs_file_path, "rb") as json_file:
        response = client.post(
            "/api/v1/dataset/",
            data={
                "params": """{  "task_name": "TabularClassificationTask",
                                    "dataloader": "JSONDataLoader",
                                    "dataset_name": "test_json",
                                    "splits_in_folders": false,
                                    "splits": {
                                        "train_size": 0.5,
                                        "test_size": 0.2,
                                        "val_size": 0.3,
                                        "seed": 42,
                                        "shuffle": false
                                    },
                                    "dataloader_params": {
                                        "data_key": "data"
                                    }
                                }""",
                "url": "",
            },
            files={"file": ("filename", json_file, "text/json")},
        )
    assert response.status_code == 201, response.text
    dataset = response.json()

    yield dataset["id"]

    response = client.delete(f"/api/v1/dataset/{dataset['id']}")
    assert response.status_code == 204, response.text


@pytest.fixture(scope="module", name="experiment_id")
def create_experiment(client: TestClient, dataset_id: int):
    session = client.app.container.db.provided().session

    with session() as db:
        experiment = Experiment(
            dataset_id=dataset_id,
            name="Experiment",
            task_name="TabularClassificationTask",
            input_columns=["feature_0", "feature_1", "feature_2", "feature_3"],
            output_columns=["class"],
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


@pytest.fixture(scope="module", name="run_id")
def create_run(client: TestClient, experiment_id: int):
    session = client.app.container.db.provided().session

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


@pytest.fixture(scope="module", name="trained_run_id")
def create_trained_run(client: TestClient, run_id: int):
    response = client.post(
        "/api/v1/job/",
        json={"job_type": "ModelJob", "kwargs": {"run_id": run_id}},
    )
    assert response.status_code == 201, response.text

    response = client.post("/api/v1/job/start/?stop_when_queue_empties=True")
    assert response.status_code == 202, response.text

    return run_id


def test_get_prediction(client: TestClient):
    response = client.get("/api/v1/predict/")
    assert response.status_code == 501, response.text


def test_make_prediction(client: TestClient, trained_run_id: int):
    script_dir = os.path.dirname(__file__)
    test_dataset = "input_iris.json"
    abs_file_path = os.path.join(script_dir, test_dataset)
    with open(abs_file_path, "rb") as json_file:
        response = client.post(
            "/api/v1/predict/",
            params={
                "run_id": trained_run_id,
            },
            files={"input_file": ("filename", json_file, "text/json")},
        )
        data = response.json()
        assert len(data) == 3


def test_delete_prediction(client: TestClient):
    response = client.delete("/api/v1/predict/")
    assert response.status_code == 501, response.text


def test_patch_prediction(client: TestClient):
    response = client.patch("/api/v1/predict/")
    assert response.status_code == 501, response.text
