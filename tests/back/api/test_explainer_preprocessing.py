import json

from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import (
    Dataset,
    GlobalExplainer,
    LocalExplainer,
)


def _create_and_train_session_with_binarizer(client: TestClient, dataset_id: int):
    session_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "explainer-preprocessing-session",
            "input_columns": [],
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
    assert session_response.status_code == 201, session_response.text
    model_session_id = session_response.json()["id"]

    run_response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "KNeighborsClassifier",
            "name": "ExplainerPreprocessingRun",
            "parameters": {"n_neighbors": 3, "weights": "uniform", "algorithm": "auto"},
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "Training for explainer preprocessing test",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert run_response.status_code == 201, run_response.text
    run_id = run_response.json()["id"]

    job_response = client.post(
        "/api/v1/job/",
        data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})},
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]
    job_status = client.get(f"/api/v1/job/status/{job_id}").json()
    assert job_status["status"] == "finished", job_status

    return model_session_id, run_id


def test_local_explainer_manual_input_applies_the_persisted_preprocessor(
    client: TestClient, dataset_1: Dataset
):
    """A manual-mode local explanation, like manual prediction, only ever
    carries the raw feature the converter scoped on. The explainer's own
    fit dataset (the model_session's training data) and the explained
    instance must both be transformed by the persisted Binarizer before
    reaching the model's feature space.
    """
    model_session_id, run_id = _create_and_train_session_with_binarizer(
        client, dataset_1.id
    )

    container = client.app.container
    session_factory = container["session_factory"]
    with session_factory() as db:
        local_explainer = LocalExplainer(
            name="preprocessing_local_explainer",
            run_id=run_id,
            explainer_name="KernelShap",
            dataset_id=dataset_1.id,
            scope={"mode": "manual"},
            parameters={},
            fit_parameters={
                "sample_background_data": False,
                "background_fraction": 0.5,
                "sampling_method": "shuffle",
            },
        )
        db.add(local_explainer)
        db.commit()
        db.refresh(local_explainer)
        explainer_id = local_explainer.id

    job_response = client.post(
        "/api/v1/job/",
        data={
            "job_type": "ExplainerJob",
            "kwargs": json.dumps(
                {
                    "explainer_id": explainer_id,
                    "explainer_scope": "local",
                    "manual_input_data": [{"SepalLengthCm": 3.0}],
                }
            ),
        },
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]

    job_status = client.get(f"/api/v1/job/status/{job_id}").json()
    assert job_status["status"] == "finished", job_status

    client.delete(f"/api/v1/model-session/{model_session_id}")


def test_global_explainer_applies_the_persisted_preprocessor(
    client: TestClient, dataset_1: Dataset
):
    """The global explainer reuses the same background-data preparation as
    the local one (data_x/data_y computed once in ExplainerJob.run before
    branching on scope), so it inherits the same preprocessor fix without
    needing its own — this test exists to confirm that, not just assume it.
    """
    model_session_id, run_id = _create_and_train_session_with_binarizer(
        client, dataset_1.id
    )

    container = client.app.container
    session_factory = container["session_factory"]
    with session_factory() as db:
        global_explainer = GlobalExplainer(
            name="preprocessing_global_explainer",
            run_id=run_id,
            explainer_name="PermutationFeatureImportance",
            parameters={"scoring": "accuracy", "n_repeats": 5},
        )
        db.add(global_explainer)
        db.commit()
        db.refresh(global_explainer)
        explainer_id = global_explainer.id

    job_response = client.post(
        "/api/v1/job/",
        data={
            "job_type": "ExplainerJob",
            "kwargs": json.dumps(
                {
                    "explainer_id": explainer_id,
                    "explainer_scope": "global",
                }
            ),
        },
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]

    job_status = client.get(f"/api/v1/job/status/{job_id}").json()
    assert job_status["status"] == "finished", job_status

    client.delete(f"/api/v1/model-session/{model_session_id}")
