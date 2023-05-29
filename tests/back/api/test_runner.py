import os
from typing import List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from DashAI.back.database.models import Experiment, Run


@pytest.fixture(scope="module", name="dataset_id")
def fixture_dataset_id(client: TestClient):
    script_dir = os.path.dirname(__file__)
    test_dataset = "iris.csv"
    abs_file_path = os.path.join(script_dir, test_dataset)
    csv = open(abs_file_path, "rb")
    response = client.post(
        "/api/v1/dataset/",
        data={
            "params": """{  "task_name": "TabularClassificationTask",
                                "dataloader": "CSVDataLoader",
                                "dataset_name": "test_csv",
                                "outputs_columns": [],
                                "splits_in_folders": false,
                                "splits": {
                                    "train_size": 0.8,
                                    "test_size": 0.1,
                                    "val_size": 0.1,
                                    "seed": 42,
                                    "shuffle": true,
                                    "stratify": false
                                },
                                "dataloader_params": {
                                    "separator": ","
                                }
                            }""",
            "url": "",
        },
        files={"file": ("filename", csv, "text/csv")},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    yield data["id"]
    response = client.delete(f"/api/v1/dataset/{data['id']}")
    assert response.status_code == 204, response.text


@pytest.fixture(scope="module", name="run_id_list")
def fixture_run_id_list(session: sessionmaker, dataset_id: int):
    db = session()

    # Create Dummy Experiment
    dummy_experiment = Experiment(
        dataset_id=dataset_id,
        task_name="TabularClassificationTask",
        name="Test Experiment",
    )
    db.add(dummy_experiment)
    db.commit()
    db.refresh(dummy_experiment)

    # Create Dummy Runs
    dummy_run1 = Run(
        experiment_id=dummy_experiment.id,
        model_name="KNeighborsClassifier",
        parameters={
            "n_neighbors": 5,
            "weights": "uniform",
            "algorithm": "auto",
        },
        run_name="Test Run 1",
        run_description="",
    )
    db.add(dummy_run1)
    dummy_run2 = Run(
        experiment_id=dummy_experiment.id,
        model_name="KNeighborsClassifier",
        parameters={
            "n_neighbors": 1,
            "weights": "distance",
            "algorithm": "brute",
        },
        run_name="Test Run 2",
        run_description="",
    )
    db.add(dummy_run2)
    db.commit()
    db.refresh(dummy_run1)
    db.refresh(dummy_run2)

    yield [dummy_run1.id, dummy_run2.id]

    # Delete the dataset, experiment and runs
    db.delete(dummy_experiment)
    db.delete(dummy_run1)
    db.delete(dummy_run2)
    db.commit()


def test_exec_runs(client: TestClient, run_id_list: List[int]):
    for run_id in run_id_list:
        response = client.post(f"/api/v1/runner/?run_id={run_id}")
        assert response.status_code == 202, response.text
    for run_id in run_id_list:
        response = client.get(f"/api/v1/run/{run_id}")
        data = response.json()
        assert data["train_metrics"] is not None
        assert data["test_metrics"] is not None
        assert data["validation_metrics"] is not None
        assert data["status"] == 2
        assert data["start_time"] != data["end_time"]


def test_exec_wrong_run(client: TestClient):
    response = client.post("/api/v1/runner/?run_id=31415")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Run not found"}'
