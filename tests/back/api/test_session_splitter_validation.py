"""A session's splitter is one its task offers, of the shape its strategy takes.

ModelJob picks the unit that prepares a run from the splitter's
``PARTITIONING`` and the unit that fits it from the strategy's ``KIND``, and
reads neither against the other nor against the task. So the session API is
what keeps the three consistent, on creation and on a change of task: a
holdout strategy with a fold splitter would fail every run with a missing
context key, and a splitter the task does not offer would run without a word,
like a temporal holdout on a regression or a shuffling holdout on a series.

A payload that names no splitter falls back to ``HoldoutSplitter``, which is
what sessions stored before splitters had names mean. The fallback is checked
like any splitter, so it can no longer shuffle a task that does not offer it.
"""

import json

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset
from tests.back.api.row_order_tasks import SeriesOnlyTask

IRIS_FEATURES = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
HOLDOUT = {
    "splitter_name": "HoldoutSplitter",
    "train": 0.6,
    "validation": 0.2,
    "test": 0.2,
}
KFOLD = {"splitter_name": "KFoldSplitter", "n_splits": 3, "test_size": 0.2}
STRATIFIED_KFOLD = {"splitter_name": "StratifiedKFoldSplitter", "n_splits": 3}
TEMPORAL = {
    "splitter_name": "TemporalHoldoutSplitter",
    "train": 0.6,
    "validation": 0.2,
    "test": 0.2,
}


def _payload(dataset_id, name, splits, task="TabularClassificationTask", **overrides):
    payload = {
        "dataset_id": dataset_id,
        "task_name": task,
        "name": name,
        "input_columns": IRIS_FEATURES,
        "output_columns": ["Species"],
        "train_metrics": [],
        "validation_metrics": [],
        "test_metrics": [],
        "evaluation_strategy": "HoldoutEvaluationStrategy",
        "splits": json.dumps(splits),
        "preprocessing": [],
    }
    payload.update(overrides)
    return payload


@pytest.fixture(name="series_only_task", scope="module")
def register_series_only_task(client: TestClient):
    registry = client.app.container["component_registry"]
    registry.register_component(SeriesOnlyTask)
    yield SeriesOnlyTask
    registry.unregister_component(SeriesOnlyTask)


@pytest.mark.parametrize(
    ("strategy", "splits", "detail"),
    [
        (
            "HoldoutEvaluationStrategy",
            KFOLD,
            "Evaluation strategy HoldoutEvaluationStrategy takes a 'holdout' "
            "splitter, but KFoldSplitter is a 'folds' splitter.",
        ),
        (
            "CrossValidationEvaluationStrategy",
            HOLDOUT,
            "Evaluation strategy CrossValidationEvaluationStrategy takes a 'folds' "
            "splitter, but HoldoutSplitter is a 'holdout' splitter.",
        ),
    ],
    ids=["holdout-with-folds", "cv-with-holdout"],
)
def test_a_splitter_of_the_wrong_shape_for_the_strategy_is_refused(
    client: TestClient, dataset_1: Dataset, strategy, splits, detail
):
    response = client.post(
        "/api/v1/model-session/",
        json=_payload(
            dataset_1.id,
            f"shape {strategy} {splits['splitter_name']}",
            splits,
            evaluation_strategy=strategy,
        ),
    )

    assert response.status_code == 422, response.text
    assert response.json()["detail"] == detail


def test_a_splitter_the_task_does_not_offer_is_refused(
    client: TestClient, dataset_1: Dataset
):
    response = client.post(
        "/api/v1/model-session/",
        json=_payload(dataset_1.id, "temporal on tabular", TEMPORAL),
    )

    assert response.status_code == 422, response.text
    assert response.json()["detail"].startswith(
        "Splitter 'TemporalHoldoutSplitter' is not available for task "
        "TabularClassificationTask. Available splitters: ["
    )
    assert "'HoldoutSplitter'" in response.json()["detail"]


def test_a_component_that_is_not_a_splitter_is_refused(
    client: TestClient, dataset_1: Dataset
):
    """A registered name of another type used to reach the splitter schema."""
    response = client.post(
        "/api/v1/model-session/",
        json=_payload(
            dataset_1.id, "metric as splitter", {"splitter_name": "Accuracy"}
        ),
    )

    assert response.status_code == 422, response.text
    assert response.json()["detail"].startswith(
        "Splitter 'Accuracy' is not available for task TabularClassificationTask."
    )


def test_the_default_splitter_is_refused_where_the_task_does_not_offer_it(
    client: TestClient, dataset_1: Dataset, series_only_task
):
    """No splitter named, and the default would shuffle a series."""
    response = client.post(
        "/api/v1/model-session/",
        json=_payload(
            dataset_1.id,
            "series without a splitter",
            {"train": 0.6, "validation": 0.2, "test": 0.2},
            task=series_only_task.__name__,
            input_columns=["SepalWidthCm"],
            output_columns=["SepalLengthCm"],
        ),
    )

    assert response.status_code == 422, response.text
    assert response.json()["detail"] == (
        "splits names no splitter, and the default, HoldoutSplitter, is not "
        "available for task SeriesOnlyTask. Available splitters: "
        "['TemporalHoldoutSplitter']."
    )


def test_the_splitter_the_task_offers_is_accepted(
    client: TestClient, dataset_1: Dataset, series_only_task
):
    response = client.post(
        "/api/v1/model-session/",
        json=_payload(
            dataset_1.id,
            "series with its splitter",
            TEMPORAL,
            task=series_only_task.__name__,
            input_columns=["SepalWidthCm"],
            output_columns=["SepalLengthCm"],
        ),
    )

    assert response.status_code == 201, response.text


def test_a_change_of_task_must_keep_the_splitter_available(
    client: TestClient, dataset_1: Dataset
):
    created = client.post(
        "/api/v1/model-session/",
        json=_payload(
            dataset_1.id,
            "stratified folds then regression",
            STRATIFIED_KFOLD,
            evaluation_strategy="CrossValidationEvaluationStrategy",
        ),
    )
    assert created.status_code == 201, created.text
    session_id = created.json()["id"]

    # Regression offers the strategy but not a splitter that stratifies on
    # its target.
    refused = client.patch(
        f"/api/v1/model-session/{session_id}?task_name=RegressionTask"
    )

    assert refused.status_code == 422, refused.text
    assert refused.json()["detail"].startswith(
        "Splitter 'StratifiedKFoldSplitter' is not available for task RegressionTask."
    )
    stored = client.get(f"/api/v1/model-session/{session_id}").json()
    assert stored["task_name"] == "TabularClassificationTask"
