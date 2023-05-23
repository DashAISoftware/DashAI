import pytest
from typing import List
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from DashAI.back.database.models import Dataset, Experiment, Run


@pytest.fixture(scope="module", name="run_id_list")
def fixture_run_id_list(session: sessionmaker):
    db = session()

    # Create Dummy Dataset
    dummy_dataset = Dataset(
        name="DummyDataset",
        task_name="TabularClassificationTask",
        file_path="dummy.csv",
    )
    db.add(dummy_dataset)
    db.commit()
    db.refresh(dummy_dataset)

    # Create Dummy Experiment
    dummy_experiment = Experiment(
        dataset_id=dummy_dataset.id,
        task_name="TabularClassificationTask",
        name="Test Experiment",
    )
    db.add(dummy_experiment)
    db.commit()
    db.refresh(dummy_experiment)

    # Create Dummy Runs
    dummy_run1 = Run(
        experiment_id=dummy_dataset.id,
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
        experiment_id=dummy_dataset.id,
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
    db.delete(dummy_dataset)
    db.delete(dummy_run1)
    db.delete(dummy_run2)
    db.commit()


def test_exec_runs(client: TestClient, run_id_list: List[int]):
    for run_id in run_id_list:
        response = client.post(f"/api/v1/runner/?run_id={run_id}")
        assert response.status_code == 200, response.text
    for run_id in run_id_list:
        response = client.get(f'/api/api_v1/run/?run_id={run_id}')
        data = response.json()
        assert data["train_metrics"] is not None
        assert data["test_metrics"] is not None
        assert data["validation_metrics"] is not None
        assert data["status"] == 2
        assert data["start_time"] != data["end_time"]


def test_exec_wrong_run(client: TestClient):
    response = client.get("/api/v1/runner/?run_id=31415")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Run not found"}'
