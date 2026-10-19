"""``PreprocessingJob`` partitions the rows the task prepared, as training does.

``ModelJob`` validates the dataset against the task and partitions what the
task hands back (``SplitterScopeMixin._prepare``), and a task may reorder the
rows: forecasting sorts them by date. ``PreprocessingJob`` fits one
preprocessor per entry the splitter produces, and ``ModelJob`` applies
``fold_{i}.pkl`` and ``final.pkl`` to its own entries by position. So both
have to carve the same rows, and nothing downstream would notice if they did
not: the entries still come in the same number, and ``zip(strict=True)`` in
the prepare units only checks that. A fold fitted on the wrong rows is also a
leak, since those rows may be the ones that fold is scored on.

The task here reverses the rows, which is the smallest reordering that tells
the two datasets apart. What each preprocessor must have been fitted on is
asked of the splitter itself, over the prepared dataset, which is what the
prepare units hand it.

Lives under ``tests/back/api`` to reuse the ``client`` and ``dataset_1``
fixtures from this package's ``conftest.py``.
"""

import json

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
from DashAI.back.dependencies.database.models import Dataset
from DashAI.back.preprocessing.session_preprocessor import SessionPreprocessor
from DashAI.back.splitters.splits_payload import normalize_splits_payload
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask

OUTPUT_COLUMNS = ["Species"]

HOLDOUT = {
    "evaluation_strategy": "HoldoutEvaluationStrategy",
    "splits": {
        "train": 0.5,
        "test": 0.2,
        "validation": 0.3,
        "shuffle": False,
        "stratify": False,
        "seed": 42,
    },
}
KFOLD = {
    "evaluation_strategy": "CrossValidationEvaluationStrategy",
    "splits": {
        "splitter_name": "KFoldSplitter",
        "n_splits": 3,
        "test_size": 0.2,
        "shuffle": False,
        "seed": 42,
    },
}


class ReversingTask(TabularClassificationTask):
    """A task whose preparation hands the rows back in reverse order.

    Like any task added from outside, it names the strategies it offers: the
    strategies list only the built-in tasks, and the session API refuses a
    strategy its task does not offer.
    """

    COMPATIBLE_COMPONENTS = [
        "HoldoutEvaluationStrategy",
        "CrossValidationEvaluationStrategy",
    ]

    def prepare_for_task(self, dataset, input_columns, output_columns):
        prepared = super().prepare_for_task(dataset, input_columns, output_columns)
        return prepared.select(range(len(prepared) - 1, -1, -1))


@pytest.fixture(name="reversing_task", scope="module")
def register_reversing_task(client: TestClient):
    registry = client.app.container["component_registry"]
    registry.register_component(ReversingTask)
    yield ReversingTask
    registry.unregister_component(ReversingTask)


def _train_rows(entry):
    return entry["train"].to_pandas()["SepalLengthCm"].tolist()


def _train_rows_per_entry(client, dataset, splits):
    """The training rows of every entry the splitter carves out of ``dataset``."""
    payload = normalize_splits_payload(dict(splits))
    registry = client.app.container["component_registry"]
    splitter = registry[payload.get("splitter_name")]["class"](splits_data=payload)
    x, _, _ = splitter.split(dataset, dataset.select_columns(OUTPUT_COLUMNS))
    return [_train_rows(entry) for entry in (x if isinstance(x, list) else [x])]


@pytest.mark.parametrize("strategy", [HOLDOUT, KFOLD], ids=["holdout", "kfold"])
def test_each_preprocessor_is_fitted_on_the_rows_its_entry_trains_on(
    client: TestClient, dataset_1: Dataset, reversing_task, monkeypatch, strategy
):
    fitted_on = []
    original_fit_transform = SessionPreprocessor.fit_transform

    def recording_fit_transform(self, split):
        fitted_on.append(_train_rows(split))
        return original_fit_transform(self, split)

    monkeypatch.setattr(SessionPreprocessor, "fit_transform", recording_fit_transform)

    response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset_1.id,
            "task_name": reversing_task.__name__,
            "name": f"preprocessing-row-order-{strategy['evaluation_strategy']}",
            "input_columns": [],
            "output_columns": OUTPUT_COLUMNS,
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": strategy["evaluation_strategy"],
            "splits": json.dumps(strategy["splits"]),
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
    assert body["preprocessing_status"] == "ready", body

    loaded = load_dataset(f"{dataset_1.file_path}/dataset")
    prepared = reversing_task().prepare_for_task(loaded, [], OUTPUT_COLUMNS)
    expected = _train_rows_per_entry(client, prepared, strategy["splits"])
    from_the_loaded_order = _train_rows_per_entry(client, loaded, strategy["splits"])
    # The file is sorted by species, so the two orders carve different rows;
    # without that the assertion below could not tell them apart.
    assert expected != from_the_loaded_order

    # One fit per fold, in fold order, then final.pkl on the trailing entry;
    # a holdout split is that trailing entry alone. Each one on the training
    # rows of the entry training applies it to, and on nothing else.
    assert fitted_on == expected

    client.delete(f"/api/v1/model-session/{body['id']}")
