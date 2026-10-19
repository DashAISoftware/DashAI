"""The explanation job hands its units the session's persisted preprocessor.

``test_explainer_preprocessing.py`` checks that the jobs finish. This one
checks what the units were given, through the only place it is observable
from outside: the rows a local explanation stores as its input. An instance
typed in by hand carries the raw feature, so the stored value being the
scaled one proves the job passed the artifacts path on and the unit applied
``final.pkl`` before selecting the session's input columns.

A scaler rather than the Binarizer the other file uses, on purpose: it keeps
the column name, so the session's resolved input column exists in the raw
rows too and training does not depend on its own preprocessing support.
"""

import json
import os
import pickle

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
from DashAI.back.dependencies.database.models import (
    Dataset,
    LocalExplainer,
    ModelSession,
)


def _train_session_with_scaler(client: TestClient, dataset_id: int):
    session_response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_id,
            "task_name": "TabularClassificationTask",
            "name": "explainer-job-preprocessing-session",
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
                    "converter": "StandardScaler",
                    "params": {"with_mean": True, "with_std": True},
                    "scope": [{"kind": "raw", "name": "SepalLengthCm"}],
                },
            ],
            "input_column_refs": [{"kind": "raw", "name": "SepalLengthCm"}],
        },
    )
    assert session_response.status_code == 201, session_response.text
    session_body = session_response.json()
    assert session_body["preprocessing_status"] == "ready", session_body
    model_session_id = session_body["id"]

    run_response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "KNeighborsClassifier",
            "name": "ExplainerJobPreprocessingRun",
            "parameters": {"n_neighbors": 3, "weights": "uniform", "algorithm": "auto"},
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 10,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "Training for the explainer job preprocessing test",
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
    job_status = client.get(f"/api/v1/job/status/{job_response.json()['id']}").json()
    assert job_status["status"] == "finished", job_status

    return model_session_id, run_id


def test_a_manual_local_explanation_stores_the_transformed_instance(
    client: TestClient, dataset_1: Dataset
):
    model_session_id, run_id = _train_session_with_scaler(client, dataset_1.id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        local_explainer = LocalExplainer(
            name="job_preprocessing_local_explainer",
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

    raw_value = 3.0
    job_response = client.post(
        "/api/v1/job/",
        data={
            "job_type": "ExplainerJob",
            "kwargs": json.dumps(
                {
                    "explainer_id": explainer_id,
                    "explainer_scope": "local",
                    "manual_input_data": [{"SepalLengthCm": raw_value}],
                }
            ),
        },
    )
    assert job_response.status_code == 201, job_response.text
    job_status = client.get(f"/api/v1/job/status/{job_response.json()['id']}").json()
    assert job_status["status"] == "finished", job_status

    with session_factory() as db:
        input_dataset_path = db.get(LocalExplainer, explainer_id).input_dataset_path
        artifacts_path = db.get(
            ModelSession, model_session_id
        ).preprocessing_artifacts_path

    with open(os.path.join(artifacts_path, "final.pkl"), "rb") as handle:
        scaler = pickle.load(handle).fitted_converters[0]
    expected = (raw_value - scaler.mean_[0]) / scaler.scale_[0]

    saved = load_dataset(os.path.join(input_dataset_path, "dataset"))
    assert saved.column_names == ["SepalLengthCm"]
    assert len(saved) == 1
    assert saved["SepalLengthCm"][0] == pytest.approx(expected)
    assert saved["SepalLengthCm"][0] != pytest.approx(raw_value)

    client.delete(f"/api/v1/model-session/{model_session_id}")


def test_a_session_with_steps_but_no_artifacts_refuses_to_explain(
    client: TestClient, dataset_1: Dataset
):
    """Steps declared and nothing fitted: explaining raw rows with a model that
    was fitted on transformed ones would be silently wrong, so the job ends in
    error with its own message instead."""
    model_session_id, run_id = _train_session_with_scaler(client, dataset_1.id)

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(ModelSession, model_session_id).preprocessing_artifacts_path = None
        local_explainer = LocalExplainer(
            name="job_preprocessing_local_explainer_no_artifacts",
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
    job_status = client.get(f"/api/v1/job/status/{job_response.json()['id']}").json()
    assert job_status["status"] == "error", job_status
    assert "no fitted preprocessor" in json.dumps(job_status), job_status

    client.delete(f"/api/v1/model-session/{model_session_id}")
