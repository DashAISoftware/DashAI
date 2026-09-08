"""API tests for the model artifacts read endpoint."""

import json
import pickle

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import RunStatus
from DashAI.back.dependencies.database.models import Dataset, ModelSession, Run

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


@pytest.fixture(scope="module", name="model_session_id")
def create_model_session(client: TestClient, dataset_1: Dataset):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_1.id,
            name="ArtifactsApiSession",
            task_name="TabularClassificationTask",
            evaluation_strategy="HoldoutEvaluationStrategy",
            input_columns=input_columns,
            output_columns=output_columns,
            splits=splits,
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)

        yield model_session.id

        db.delete(model_session)
        db.commit()


@pytest.fixture(name="run_id")
def create_run(client: TestClient, model_session_id: int):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = Run(
            model_session_id=model_session_id,
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={},
            model_name="DecisionTreeClassifier",
            parameters={},
            goal_metric="Accuracy",
            name="Artifacts run",
            status=RunStatus.FINISHED,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

    yield run_id

    with session_factory() as db:
        run = db.get(Run, run_id)
        if run:
            db.delete(run)
            db.commit()


def test_returns_empty_shape_when_never_generated(client: TestClient, run_id: int):
    response = client.get(f"/api/v1/run/{run_id}/model_artifacts")

    assert response.status_code == 200, response.text
    assert response.json() == {"status": None, "artifacts": []}


def test_returns_stored_artifacts(client: TestClient, run_id: int, tmp_path):
    path = tmp_path / "artifacts.pickle"
    with open(path, "wb") as file:
        pickle.dump(
            [{"type": "text", "payload": "hi", "title": None, "index": 0}], file
        )

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = db.get(Run, run_id)
        run.model_artifacts_path = str(path)
        run.model_artifacts_status = RunStatus.FINISHED
        db.commit()

    body = client.get(f"/api/v1/run/{run_id}/model_artifacts").json()

    assert body["status"] == "FINISHED"
    assert body["artifacts"][0]["payload"] == "hi"
    assert body["artifacts"][0]["type"] == "text"


def test_reports_a_failed_generation(client: TestClient, run_id: int):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = db.get(Run, run_id)
        run.model_artifacts_status = RunStatus.ERROR
        db.commit()

    body = client.get(f"/api/v1/run/{run_id}/model_artifacts").json()

    assert body == {"status": "ERROR", "artifacts": []}


def test_404_when_the_stored_file_is_missing(client: TestClient, run_id: int):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        run = db.get(Run, run_id)
        run.model_artifacts_path = "does-not-exist.pickle"
        run.model_artifacts_status = RunStatus.FINISHED
        db.commit()

    assert client.get(f"/api/v1/run/{run_id}/model_artifacts").status_code == 404


def test_404_for_unknown_run(client: TestClient):
    assert client.get("/api/v1/run/99999/model_artifacts").status_code == 404
