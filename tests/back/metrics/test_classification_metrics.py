import io
import os
from typing import Tuple

import pytest
from datasets import DatasetDict
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.metrics.classification.accuracy import Accuracy
from DashAI.back.metrics.classification.f1 import F1
from DashAI.back.metrics.classification.precision import Precision
from DashAI.back.metrics.classification.recall import Recall
from DashAI.back.models.scikit_learn.random_forest_classifier import (
    RandomForestClassifier,
)
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask


@pytest.fixture(scope="module")
def classification_metrics_fixture():
    test_dataset_path = "tests/back/metrics/iris.csv"

    csv_dataloader = CSVDataLoader()
    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
        csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
        file = UploadFile(csv_binary)

    dataset_dict = csv_dataloader.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/metrics",
        params={"separator": ","},
    )
    dashai_dataset = to_dashai_dataset(
        dataset_dict,
        inputs_columns=[
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
        ],
        outputs_columns=["Species"],
    )

    outputs_columns = dashai_dataset["train"].outputs_columns
    dataset = csv_dataloader.split_dataset(
        dashai_dataset, 0.7, 0.1, 0.2, class_column=outputs_columns[0]
    )

    tabular_task = TabularClassificationTask()

    name_datasetdict = "Iris"
    dataset = tabular_task.prepare_for_task(dataset)
    tabular_task.validate_dataset_for_task(dataset, name_datasetdict)

    model = RandomForestClassifier()
    model.fit(dataset["train"])
    model.save("tests/back/metrics/rf_model")

    yield dataset, model

    os.remove("tests/back/metrics/rf_model")


def test_accuracy(
    classification_metrics_fixture: Tuple[DatasetDict, RandomForestClassifier]
):
    dataset, model = classification_metrics_fixture
    y_pred = model.predict(dataset["test"])
    score = Accuracy.score(dataset["test"], y_pred)

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_precision(
    classification_metrics_fixture: Tuple[DatasetDict, RandomForestClassifier]
):
    dataset, model = classification_metrics_fixture
    y_pred = model.predict(dataset["test"])

    score = Precision.score(dataset["test"], y_pred)

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_recall(
    classification_metrics_fixture: Tuple[DatasetDict, RandomForestClassifier]
):
    dataset, model = classification_metrics_fixture
    y_pred = model.predict(dataset["test"])
    score = Recall.score(dataset["test"], y_pred)

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_f1_score(
    classification_metrics_fixture: Tuple[DatasetDict, RandomForestClassifier]
):
    dataset, model = classification_metrics_fixture
    y_pred = model.predict(dataset["test"])
    score = F1.score(dataset["test"], y_pred)

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_metrics_different_input_sizes(
    classification_metrics_fixture: Tuple[DatasetDict, RandomForestClassifier]
):
    dataset, model = classification_metrics_fixture
    y_pred = model.predict(dataset["validation"])

    with pytest.raises(
        ValueError,
        match=(
            r"The length of the true labels and the predicted labels must be equal, "
            r"given: len\(true_labels\) = 15 and len\(pred_labels\) = 30\."
        ),
    ):
        Accuracy.score(dataset["test"], y_pred)

    with pytest.raises(
        ValueError,
        match=(
            r"The length of the true labels and the predicted labels must be equal, "
            r"given: len\(true_labels\) = 15 and len\(pred_labels\) = 30\."
        ),
    ):
        Precision.score(dataset["test"], y_pred)

    with pytest.raises(
        ValueError,
        match=(
            r"The length of the true labels and the predicted labels must be equal, "
            r"given: len\(true_labels\) = 15 and len\(pred_labels\) = 30\."
        ),
    ):
        Recall.score(dataset["test"], y_pred)

    with pytest.raises(
        ValueError,
        match=(
            r"The length of the true labels and the predicted labels must be equal, "
            r"given: len\(true_labels\) = 15 and len\(pred_labels\) = 30\."
        ),
    ):
        F1.score(dataset["test"], y_pred)
