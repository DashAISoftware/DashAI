"""A session with a training-only resampler (SMOTE) trains end to end."""

import json

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset
from DashAI.back.job.dataset_job import DatasetJob
from DashAI.back.splitters.splits_payload import schema_placeholder_defaults

RUN_PARAMS = {
    "model_name": "KNeighborsClassifier",
    "name": "smote-run",
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


@pytest.fixture(name="imbalanced_dataset", scope="module")
def create_imbalanced_dataset(client: TestClient, tmp_path_factory) -> Dataset:
    """80 rows, 10 of them "fraud": the imbalance SMOTE exists for."""
    rows = ["age,height,city,label"]
    for i in range(80):
        label = "fraud" if i % 8 == 0 else "normal"
        rows.append(
            f"{20 + (i * 7) % 40},{1.5 + (i % 9) / 20:.2f},{'abc'[i % 3]},{label}"
        )
    csv = tmp_path_factory.mktemp("resampling") / "imbalanced.csv"
    csv.write_text("\n".join(rows))

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        dataset = Dataset(name="imbalanced", file_path="")
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
                    "name": "imbalanced",
                    "schema": {
                        "age": {"type": "Integer", "dtype": "int64"},
                        "height": {"type": "Float", "dtype": "float64"},
                        "city": {"type": "Categorical", "dtype": "string"},
                        "label": {"type": "Categorical", "dtype": "string"},
                    },
                },
            },
        ).run()
        db.refresh(dataset)
    return dataset


def _step(client: TestClient, name: str, scope: list, **params) -> dict:
    """A step as the wizard's form submits it: schema placeholders + params."""
    converter_class = client.app.container["component_registry"][name]["class"]
    return {
        "converter": name,
        "params": {**schema_placeholder_defaults(converter_class), **params},
        "scope": scope,
    }


def _raw(name: str) -> dict:
    return {"kind": "raw", "name": name}


def test_a_session_with_onehot_and_smote_trains_and_evaluates(
    client: TestClient, imbalanced_dataset: Dataset
) -> None:
    onehot_output = {"kind": "group", "step": 0}
    steps = [
        _step(client, "OneHotEncoder", [_raw("city")]),
        _step(
            client,
            "SMOTEConverter",
            [_raw("age"), _raw("height"), onehot_output],
            random_state=0,
            k_neighbors=3,
        ),
    ]
    session = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": imbalanced_dataset.id,
            "task_name": "TabularClassificationTask",
            "name": "onehot-smote",
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
            "preprocessing": steps,
            "input_column_refs": [_raw("age"), _raw("height"), onehot_output],
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
    job = client.post(
        "/api/v1/job/",
        data={"job_type": "ModelJob", "kwargs": json.dumps({"run_id": run_id})},
    ).json()
    status = client.get(f"/api/v1/job/status/{job['id']}").json()
    assert status["status"] == "finished", status

    finished = client.get(f"/api/v1/run/{run_id}").json()
    assert finished["status"] == 3  # RunStatus.FINISHED
    # The test split keeps its real rows, 20% of 80, with no synthetic ones.
    assert len(json.loads(finished["split_indexes"])["test_indexes"]) == 16

    client.delete(f"/api/v1/run/{run_id}")
    client.delete(f"/api/v1/model-session/{body['id']}")
