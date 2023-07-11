import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from DashAI.back.database.models import Experiment, Run


@pytest.fixture(scope="module", name="dataset_id")
def fixture_dataset_id(client: TestClient):
    script_dir = os.path.dirname(__file__)
    test_dataset = "iris.csv"
    abs_file_path = os.path.join(script_dir, test_dataset)
    with open(abs_file_path, "rb") as csv:
        response = client.post(
            "/api/v1/dataset/",
            data={
                "params": """{  "task_name": "TabularClassificationTask",
                                    "dataloader": "CSVDataLoader",
                                    "dataset_name": "test_csv",
                                    "outputs_columns": ["Species"],
                                    "splits_in_folders": false,
                                    "splits": {
                                        "train_size": 0.5,
                                        "test_size": 0.2,
                                        "val_size": 0.3,
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
    dataset = response.json()

    yield dataset["id"]

    response = client.delete(f"/api/v1/dataset/{dataset['id']}")
    assert response.status_code == 204, response.text


@pytest.fixture(scope="module", name="experiment_id")
def fixture_experiment_id(session: sessionmaker, dataset_id: int):
    db = session()

    experiment = Experiment(
        dataset_id=dataset_id, name="Experiment", task_name="TabularClassificationTask"
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    yield experiment.id

    db.delete(experiment)
    db.commit()
    db.close()


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


def test_exec_runs(client: TestClient, run_id: int):
    response = client.post(f"/api/v1/runner/?run_id={run_id}")
    assert response.status_code == 202, response.text

    response = client.get(f"/api/v1/run/{run_id}")
    data = response.json()
    print(f"data exc_run: {data}")
    assert isinstance(data["train_metrics"], dict)
    assert isinstance(data["validation_metrics"], dict)
    assert isinstance(data["test_metrics"], dict)
    assert data["run_path"] is not None
    assert data["status"] == 3
    assert data["delivery_time"] is not None
    assert data["start_time"] is not None
    assert data["end_time"] is not None


def test_predict(client: TestClient, run_id: int):
    response = client.post(
        f"""/api/v1/predict/?run_id={run_id}&features=SepalLengthCm&features=SepalWidthCm&features=PetalLengthCm&features=PetalWidthCm&values=2&values=1&values=1&values=1&values=0.85&values=90&values=1&values=100"""
    )
    data = response.json()
    for _, value in data.items():
        assert value in ["Iris-setosa", "Iris-versicolor", "Iris-virginica"]
