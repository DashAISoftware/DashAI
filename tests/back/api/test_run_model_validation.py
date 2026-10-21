"""A run's model is one its session's task offers.

The wizard lists only the models the registry relates to the session's task,
and nothing else checked it: ``POST /run/`` stored any registered name,
whatever its type, and the run then failed or misbehaved inside the fit. The
run API now asks the registry the same question the wizard does. A change of
task by PATCH asks it for every run the session already has, and refuses the
change, naming the runs, rather than leaving them with a model their task does
not offer.
"""

import json

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset

IRIS_FEATURES = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]


def _create_session(client, dataset, name):
    response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset.id,
            "task_name": "TabularClassificationTask",
            "name": name,
            "input_columns": IRIS_FEATURES,
            "output_columns": ["Species"],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(
                {
                    "splitter_name": "HoldoutSplitter",
                    "train": 0.6,
                    "validation": 0.2,
                    "test": 0.2,
                }
            ),
            "preprocessing": [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_run(client, session_id, model_name, name):
    return client.post(
        "/api/v1/run/",
        json={
            "model_session_id": session_id,
            "model_name": model_name,
            "name": name,
            "parameters": {},
            "optimizer_name": "OptunaOptimizer",
            "optimizer_parameters": {
                "n_trials": 1,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "Accuracy",
            "plot_history_path": "",
            "plot_slice_path": "",
            "plot_contour_path": "",
            "plot_importance_path": "",
        },
    )


@pytest.fixture(name="session_id")
def classification_session(client: TestClient, dataset_1: Dataset, request):
    return _create_session(client, dataset_1, f"run model {request.node.name}")


@pytest.mark.parametrize(
    "model_name",
    [
        # A regressor in a classification session.
        "RandomForestRegression",
        # A registered component that is not a model at all.
        "Accuracy",
    ],
)
def test_a_model_the_task_does_not_offer_is_refused(client, session_id, model_name):
    response = _create_run(client, session_id, model_name, f"refused {model_name}")

    assert response.status_code == 422, response.text
    assert response.json()["detail"] == (
        f"Model {model_name!r} is not available for task TabularClassificationTask."
    )


def test_a_model_the_task_offers_is_accepted(client, session_id):
    response = _create_run(client, session_id, "KNeighborsClassifier", "accepted")

    assert response.status_code == 201, response.text


def test_a_change_of_task_is_refused_while_a_run_has_a_model_it_does_not_offer(
    client, session_id
):
    created = _create_run(client, session_id, "KNeighborsClassifier", "a classifier")
    assert created.status_code == 201, created.text
    run_id = created.json()["id"]

    refused = client.patch(
        f"/api/v1/model-session/{session_id}?task_name=RegressionTask"
    )

    assert refused.status_code == 422, refused.text
    assert refused.json()["detail"] == (
        "Task RegressionTask does not offer the model of these runs of the "
        f"session: 'a classifier' (id {run_id}, KNeighborsClassifier). Delete "
        "them or keep the current task."
    )
    stored = client.get(f"/api/v1/model-session/{session_id}").json()
    assert stored["task_name"] == "TabularClassificationTask"
