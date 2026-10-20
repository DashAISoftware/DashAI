"""A session pairs its task with a strategy that task offers, and nothing else.

ModelJob chooses which units to chain from the session's evaluation strategy
alone. That holds only while the strategy that carves nothing reaches tasks
without a target, and the strategies that partition reach tasks with one, so
the session API refuses any other pairing, on creation and on a change of task.
"""

import json

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset

IRIS_FEATURES = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
HOLDOUT_SPLITS = {
    "splitter_name": "HoldoutSplitter",
    "train": 0.6,
    "validation": 0.2,
    "test": 0.2,
}


def _payload(dataset_id: int, task: str, strategy: str, name: str, **overrides):
    without_target = strategy == "FullDatasetEvaluationStrategy"
    payload = {
        "dataset_id": dataset_id,
        "task_name": task,
        "name": name,
        "input_columns": IRIS_FEATURES,
        "output_columns": [] if without_target else ["Species"],
        "train_metrics": [],
        "validation_metrics": [],
        "test_metrics": [],
        "evaluation_strategy": strategy,
        "splits": json.dumps({} if without_target else HOLDOUT_SPLITS),
        "preprocessing": [],
    }
    payload.update(overrides)
    return payload


def _offered(client: TestClient, task: str) -> set:
    response = client.get(
        "/api/v1/component/",
        params={"select_types": ["EvaluationStrategy"], "related_component": task},
    )
    assert response.status_code == 200, response.text
    return {component["name"] for component in response.json()}


def test_each_task_is_offered_only_its_own_strategies(client: TestClient):
    assert _offered(client, "ClusteringTask") == {"FullDatasetEvaluationStrategy"}
    assert _offered(client, "TabularClassificationTask") == {
        "HoldoutEvaluationStrategy",
        "CrossValidationEvaluationStrategy",
    }


@pytest.mark.parametrize(
    ("task", "strategy"),
    [
        ("ClusteringTask", "HoldoutEvaluationStrategy"),
        ("ClusteringTask", "CrossValidationEvaluationStrategy"),
        ("TabularClassificationTask", "FullDatasetEvaluationStrategy"),
        ("TabularClassificationTask", "NoSuchStrategy"),
    ],
)
def test_a_strategy_the_task_does_not_offer_is_refused(
    client: TestClient, dataset_1: Dataset, task: str, strategy: str
):
    response = client.post(
        "/api/v1/model-session/",
        json=_payload(dataset_1.id, task, strategy, f"refused {task} {strategy}"),
    )

    assert response.status_code == 422, response.text
    assert response.json()["detail"].startswith(
        f"Evaluation strategy {strategy!r} is not available for task {task}."
    )


def test_an_unknown_task_is_refused(client: TestClient, dataset_1: Dataset):
    response = client.post(
        "/api/v1/model-session/",
        json=_payload(
            dataset_1.id, "NoSuchTask", "HoldoutEvaluationStrategy", "unknown task"
        ),
    )

    assert response.status_code == 422, response.text
    assert response.json()["detail"] == (
        "Task NoSuchTask does not exist in the registry."
    )


def test_a_clustering_session_takes_no_splitter(client: TestClient, dataset_1: Dataset):
    response = client.post(
        "/api/v1/model-session/",
        json=_payload(
            dataset_1.id,
            "ClusteringTask",
            "FullDatasetEvaluationStrategy",
            "clustering without splitter",
        ),
    )

    assert response.status_code == 201, response.text
    assert response.json()["evaluation_strategy"] == "FullDatasetEvaluationStrategy"
    assert json.loads(response.json()["splits"]) == {}


@pytest.mark.parametrize(
    ("splits", "detail"),
    [
        # What the front sent before the strategy existed.
        (json.dumps({"splitType": "none"}), "splits must be an empty object"),
        (json.dumps(HOLDOUT_SPLITS), "splits must be an empty object"),
        (json.dumps([]), "splits must be an empty object"),
        ("not json", "splits is not a valid JSON object"),
    ],
)
def test_a_strategy_that_carves_nothing_refuses_a_splits_payload(
    client: TestClient, dataset_1: Dataset, splits: str, detail: str
):
    """Nothing reads the payload of such a session, so none is stored."""
    response = client.post(
        "/api/v1/model-session/",
        json=_payload(
            dataset_1.id,
            "ClusteringTask",
            "FullDatasetEvaluationStrategy",
            f"clustering with splits {splits}",
            splits=splits,
        ),
    )

    assert response.status_code == 422, response.text
    assert detail in response.json()["detail"]


def test_a_strategy_that_carves_nothing_refuses_session_preprocessing(
    client: TestClient, dataset_1: Dataset
):
    """Session preprocessing is fitted once per partition, and there are none."""
    response = client.post(
        "/api/v1/model-session/",
        json=_payload(
            dataset_1.id,
            "ClusteringTask",
            "FullDatasetEvaluationStrategy",
            "clustering with preprocessing",
            preprocessing=[
                {
                    "converter": "Binarizer",
                    "params": {"threshold": 3.0},
                    "scope": [{"kind": "raw", "name": "SepalLengthCm"}],
                }
            ],
            input_column_refs=[{"kind": "group", "step": 0}],
        ),
    )

    assert response.status_code == 422, response.text
    assert "does not take session preprocessing" in response.json()["detail"]


def test_a_change_of_task_must_keep_the_strategy_available(
    client: TestClient, dataset_1: Dataset
):
    created = client.post(
        "/api/v1/model-session/",
        json=_payload(
            dataset_1.id,
            "TabularClassificationTask",
            "HoldoutEvaluationStrategy",
            "change of task",
        ),
    )
    assert created.status_code == 201, created.text
    session_id = created.json()["id"]

    refused = client.patch(
        f"/api/v1/model-session/{session_id}?task_name=ClusteringTask"
    )
    assert refused.status_code == 422, refused.text
    stored = client.get(f"/api/v1/model-session/{session_id}").json()
    assert stored["task_name"] == "TabularClassificationTask"

    accepted = client.patch(
        f"/api/v1/model-session/{session_id}?task_name=RegressionTask"
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["task_name"] == "RegressionTask"
