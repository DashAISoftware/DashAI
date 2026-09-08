import json

from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset


def _session_body(splits: dict, dataset: Dataset, name: str) -> dict:
    return {
        "name": name,
        "dataset_id": dataset.id,
        "task_name": "TabularClassificationTask",
        "input_columns": ["SepalLengthCm"],
        "output_columns": ["Species"],
        "train_metrics": [],
        "validation_metrics": [],
        "test_metrics": [],
        "evaluation_strategy": "HoldoutEvaluationStrategy",
        "splits": json.dumps(splits),
    }


def test_rejects_proportions_that_do_not_sum_to_one(
    client: TestClient, dataset_1: Dataset
):
    splits = {
        "splitter_name": "HoldoutSplitter",
        "splitType": "random",
        "train": 0.8,
        "test": 0.2,
        "validation": 0.2,
        "stratify": False,
        "shuffle": True,
        "random_state": 42,
    }
    response = client.post(
        "/api/v1/model-session/",
        json=_session_body(splits, dataset_1, "bad proportions"),
    )
    assert response.status_code == 422, response.text
    assert "sum to 1" in response.text


def test_rejects_a_single_fold(client: TestClient, dataset_1: Dataset):
    splits = {
        "splitter_name": "KFoldSplitter",
        "splitType": "cv",
        "n_splits": 1,
        "shuffle": True,
        "random_state": 42,
    }
    body = _session_body(splits, dataset_1, "single fold")
    body["evaluation_strategy"] = "CrossValidationEvaluationStrategy"

    response = client.post("/api/v1/model-session/", json=body)
    assert response.status_code == 422, response.text


def test_rejects_an_unknown_splitter(client: TestClient, dataset_1: Dataset):
    splits = {"splitter_name": "NotASplitter", "splitType": "random"}
    response = client.post(
        "/api/v1/model-session/",
        json=_session_body(splits, dataset_1, "unknown splitter"),
    )
    assert response.status_code == 422, response.text


def test_accepts_a_manual_split_without_proportions(
    client: TestClient, dataset_1: Dataset
):
    splits = {
        "splitter_name": "HoldoutSplitter",
        "splitType": "manual",
        "splitted_indexes": {
            "train_indexes": [0, 1, 2],
            "test_indexes": [3],
            "val_indexes": [4],
        },
        "stratify": False,
        "shuffle": True,
        "random_state": 42,
    }
    response = client.post(
        "/api/v1/model-session/",
        json=_session_body(splits, dataset_1, "manual split session"),
    )
    assert response.status_code == 201, response.text


def test_accepts_a_cross_validation_payload(client: TestClient, dataset_1: Dataset):
    splits = {
        "splitter_name": "RepeatedKFoldSplitter",
        "splitType": "cv",
        "n_splits": 4,
        "n_repeats": 3,
        "random_state": 7,
    }
    body = _session_body(splits, dataset_1, "repeated cv session")
    body["evaluation_strategy"] = "CrossValidationEvaluationStrategy"

    response = client.post("/api/v1/model-session/", json=body)
    assert response.status_code == 201, response.text


def test_rejects_more_folds_than_the_schema_allows(
    client: TestClient, dataset_1: Dataset
):
    splits = {
        "splitter_name": "KFoldSplitter",
        "splitType": "cv",
        "n_splits": 50,
        "shuffle": True,
        "random_state": 42,
    }
    body = _session_body(splits, dataset_1, "too many folds")
    body["evaluation_strategy"] = "CrossValidationEvaluationStrategy"

    response = client.post("/api/v1/model-session/", json=body)
    assert response.status_code == 422, response.text


def test_accepts_a_legacy_seed_payload(client: TestClient, dataset_1: Dataset):
    splits = {
        "splitter_name": "HoldoutSplitter",
        "splitType": "random",
        "train": 0.6,
        "test": 0.2,
        "validation": 0.2,
        "stratify": False,
        "shuffle": True,
        "seed": 7,
    }
    response = client.post(
        "/api/v1/model-session/",
        json=_session_body(splits, dataset_1, "legacy seed session"),
    )
    assert response.status_code == 201, response.text
