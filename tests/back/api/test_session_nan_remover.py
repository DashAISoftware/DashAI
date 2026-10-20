"""A session with NanRemover trains and explains end to end."""

import json

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset, GlobalExplainer
from DashAI.back.job.dataset_job import DatasetJob

RUN_PARAMS = {
    "model_name": "KNeighborsClassifier",
    "name": "nan-remover-run",
    "parameters": {"n_neighbors": 3, "weights": "uniform", "algorithm": "auto"},
    "optimizer_name": "",
    "optimizer_parameters": {"n_trials": 10, "sampler": "TPESampler", "pruner": "None"},
    "goal_metric": "",
    "description": "",
    "plot_history_path": "",
    "plot_slice_path": "",
    "plot_contour_path": "",
    "plot_importance_path": "",
}


@pytest.fixture(name="incomplete_dataset", scope="module")
def create_incomplete_dataset(client: TestClient, tmp_path_factory) -> Dataset:
    """60 rows; every sixth has no age."""
    rows = ["age,height,label"]
    for i in range(60):
        age = "" if i % 6 == 0 else str(20 + (i * 7) % 40)
        rows.append(f"{age},{1.5 + (i % 9) / 20:.2f},{'yes' if i % 3 else 'no'}")
    csv = tmp_path_factory.mktemp("nan_remover") / "incomplete.csv"
    csv.write_text("\n".join(rows))

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        dataset = Dataset(name="incomplete", file_path="")
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        DatasetJob(
            job_type="DatasetJob",
            db=db,
            kwargs={
                "dataset_id": dataset.id,
                "url": "",
                "file_path": csv,
                "params": {
                    "dataloader": "CSVDataLoader",
                    "separator": ",",
                    "name": "incomplete",
                    "schema": {
                        "age": {"type": "Integer", "dtype": "int64"},
                        "height": {"type": "Float", "dtype": "float64"},
                        "label": {"type": "Categorical", "dtype": "string"},
                    },
                },
            },
        ).run()
        db.refresh(dataset)
    return dataset


def _run_job(client: TestClient, job_type: str, kwargs: dict) -> dict:
    job = client.post(
        "/api/v1/job/", data={"job_type": job_type, "kwargs": json.dumps(kwargs)}
    ).json()
    return client.get(f"/api/v1/job/status/{job['id']}").json()


def test_a_session_with_nan_remover_trains_and_explains(
    client: TestClient, incomplete_dataset: Dataset
) -> None:
    # KNN cannot handle missing values, so training, scoring and the
    # explainer only succeed if NanRemover cleaned every split they use.
    raw = [{"kind": "raw", "name": "age"}, {"kind": "raw", "name": "height"}]
    session = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": incomplete_dataset.id,
            "task_name": "TabularClassificationTask",
            "name": "nan-remover-session",
            "input_columns": ["age", "height"],
            "output_columns": ["label"],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(
                {
                    "train": 0.6,
                    "test": 0.2,
                    "validation": 0.2,
                    "is_random": True,
                    "has_changed": True,
                    "seed": 42,
                    "shuffle": True,
                    "stratify": False,
                }
            ),
            "preprocessing": [{"converter": "NanRemover", "params": {}, "scope": raw}],
            "input_column_refs": raw,
        },
    )
    assert session.status_code == 201, session.text
    body = session.json()
    assert body["preprocessing_status"] == "ready", body["preprocessing_error"]

    run = client.post(
        "/api/v1/run/", json={**RUN_PARAMS, "model_session_id": body["id"]}
    )
    assert run.status_code == 201, run.text
    run_id = run.json()["id"]
    status = _run_job(client, "ModelJob", {"run_id": run_id})
    assert status["status"] == "finished", status

    with client.app.container["session_factory"]() as db:
        explainer = GlobalExplainer(
            name="nan-remover-explainer",
            run_id=run_id,
            explainer_name="PermutationFeatureImportance",
            parameters={"scoring": "accuracy", "n_repeats": 5},
        )
        db.add(explainer)
        db.commit()
        db.refresh(explainer)
        explainer_id = explainer.id
    status = _run_job(
        client,
        "ExplainerJob",
        {"explainer_id": explainer_id, "explainer_scope": "global"},
    )
    assert status["status"] == "finished", status

    client.delete(f"/api/v1/run/{run_id}")
    client.delete(f"/api/v1/model-session/{body['id']}")
