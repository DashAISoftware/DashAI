import json

from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset

SESSION_PARAMS = {
    "task_name": "TabularClassificationTask",
    "input_columns": [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
    ],
    "output_columns": ["Species"],
    "train_metrics": [],
    "validation_metrics": [],
    "test_metrics": [],
    "evaluation_strategy": "HoldoutEvaluationStrategy",
    "splits": json.dumps(
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
}


def test_delete_model_session(client: TestClient, dataset_1: Dataset) -> None:
    response = client.post(
        "/api/v1/model-session/",
        json={**SESSION_PARAMS, "dataset_id": dataset_1.id, "name": "delete_me"},
    )
    assert response.status_code == 201, response.text
    session_id = response.json()["id"]

    response = client.delete(f"/api/v1/model-session/{session_id}")
    assert response.status_code == 204, response.text

    response = client.get(f"/api/v1/model-session/{session_id}")
    assert response.status_code == 404, response.text

    response = client.delete("/api/v1/model-session/10000")
    assert response.status_code == 404, response.text


def test_create_model_session_without_preprocessing_is_ready_immediately(
    client: TestClient, dataset_1: Dataset
) -> None:
    response = client.post(
        "/api/v1/model-session/",
        json={
            **SESSION_PARAMS,
            "dataset_id": dataset_1.id,
            "name": "no-preprocessing-session",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["preprocessing_status"] == "ready"

    session_id = response.json()["id"]
    client.delete(f"/api/v1/model-session/{session_id}")


def test_create_model_session_with_preprocessing_fits_and_resolves_columns(
    client: TestClient, dataset_1: Dataset
) -> None:
    response = client.post(
        "/api/v1/model-session/",
        json={
            **SESSION_PARAMS,
            "dataset_id": dataset_1.id,
            "name": "with-preprocessing-session",
            "input_columns": [],
            "preprocessing": [
                {
                    "converter": "Binarizer",
                    "params": {"threshold": 3.0},
                    "scope": [{"kind": "raw", "name": "SepalLengthCm"}],
                },
            ],
            "input_column_refs": [{"kind": "group", "step": 0}],
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    # The test client runs the job queue in immediate mode, so by the time
    # the request returns, PreprocessingJob already fit and resolved this.
    # Binarizer is an EncodingConverter: it appends "bin_<col>" and keeps the
    # original column unchanged (a passthrough, like BagOfWords keeping its
    # source text column) — the group is only the genuinely new column it
    # produced, not the untouched original alongside it.
    assert body["preprocessing_status"] == "ready"
    assert body["input_columns"] == ["bin_SepalLengthCm"]
    # The frontend tracks this exact job via the shared job-polling
    # mechanism (useJobTracker), so it must be a real, non-empty id.
    assert body["preprocessing_job_id"]

    session_id = body["id"]
    client.delete(f"/api/v1/model-session/{session_id}")


def test_create_model_session_with_preprocessing_requires_input_column_refs(
    client: TestClient, dataset_1: Dataset
) -> None:
    response = client.post(
        "/api/v1/model-session/",
        json={
            **SESSION_PARAMS,
            "dataset_id": dataset_1.id,
            "name": "missing-refs-session",
            "preprocessing": [
                {
                    "converter": "Binarizer",
                    "params": {"threshold": 3.0},
                    "scope": [{"kind": "raw", "name": "SepalLengthCm"}],
                },
            ],
        },
    )
    assert response.status_code == 422, response.text


def test_validate_columns_accepts_a_group_ref_matching_the_task_type(
    client: TestClient, dataset_1: Dataset
) -> None:
    response = client.post(
        "/api/v1/model-session/validation",
        json={
            "task_name": "TabularClassificationTask",
            "dataset_id": dataset_1.id,
            "inputs_columns": ["SepalWidthCm"],
            "outputs_columns": ["Species"],
            "input_refs": [
                {"kind": "raw", "name": "SepalWidthCm"},
                {"kind": "group", "step": 0},
            ],
            "converter_output_types": {"0": "Integer"},
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["dataset_status"] == "valid"


def test_validate_columns_rejects_a_group_ref_with_an_incompatible_type(
    client: TestClient, dataset_1: Dataset
) -> None:
    response = client.post(
        "/api/v1/model-session/validation",
        json={
            "task_name": "TabularClassificationTask",
            "dataset_id": dataset_1.id,
            "inputs_columns": [],
            "outputs_columns": ["Species"],
            "input_refs": [{"kind": "group", "step": 0}],
            "converter_output_types": {"0": "Text"},
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["dataset_status"] == "invalid"


def test_validate_columns_accepts_a_slotted_group_ref_matching_the_task_type(
    client: TestClient, dataset_1: Dataset
) -> None:
    response = client.post(
        "/api/v1/model-session/validation",
        json={
            "task_name": "TabularClassificationTask",
            "dataset_id": dataset_1.id,
            "inputs_columns": [],
            "outputs_columns": ["Species"],
            "input_refs": [{"kind": "group", "step": 0, "slot": "Integer"}],
            "converter_output_types": {"0:Integer": "Integer", "0:Categorical": "Text"},
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["dataset_status"] == "valid"


def test_validate_columns_rejects_a_slotted_group_ref_with_an_incompatible_type(
    client: TestClient, dataset_1: Dataset
) -> None:
    response = client.post(
        "/api/v1/model-session/validation",
        json={
            "task_name": "TabularClassificationTask",
            "dataset_id": dataset_1.id,
            "inputs_columns": [],
            "outputs_columns": ["Species"],
            "input_refs": [{"kind": "group", "step": 0, "slot": "Categorical"}],
            "converter_output_types": {"0:Integer": "Integer", "0:Categorical": "Text"},
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["dataset_status"] == "invalid"


def test_bulk_delete_model_sessions(client: TestClient, dataset_1: Dataset) -> None:
    created_ids = []
    for name in ["bulk_delete_session_1", "bulk_delete_session_2"]:
        response = client.post(
            "/api/v1/model-session/",
            json={**SESSION_PARAMS, "dataset_id": dataset_1.id, "name": name},
        )
        assert response.status_code == 201, response.text
        created_ids.append(response.json()["id"])

    # A non-existent id mixed in should be skipped rather than failing the batch.
    response = client.request(
        "DELETE",
        "/api/v1/model-session/",
        json={"ids": [*created_ids, 999999]},
    )
    assert response.status_code == 204, response.text

    for session_id in created_ids:
        response = client.get(f"/api/v1/model-session/{session_id}")
        assert response.status_code == 404, response.text
