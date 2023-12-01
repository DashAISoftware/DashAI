import io
import os
from typing import Tuple

import pytest
from datasets import DatasetDict
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import select_columns
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.metrics.classification.accuracy import Accuracy
from DashAI.back.metrics.classification.f1 import F1
from DashAI.back.metrics.classification.precision import Precision
from DashAI.back.metrics.classification.recall import Recall
from DashAI.back.models.scikit_learn.random_forest_classifier import (
    RandomForestClassifier,
)
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask


@pytest.fixture(scope="module", name="dataset_and_model")
def dataset_and_model_fixture() -> Tuple[DatasetDict, RandomForestClassifier]:
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
    dashai_dataset = to_dashai_dataset(dataset_dict)

    dataset = csv_dataloader.split_dataset(
        dataset=dashai_dataset,
        train_size=0.7,
        test_size=0.1,
        val_size=0.2,
    )

    input_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    output_columns = ["Species"]

    tabular_task = TabularClassificationTask()

    name_datasetdict = "Iris"
    dataset = tabular_task.prepare_for_task(dataset, output_columns)
    tabular_task.validate_dataset_for_task(
        dataset, name_datasetdict, input_columns, output_columns
    )

    divided_dataset = select_columns(
        dataset,
        input_columns,
        output_columns,
    )

    model = RandomForestClassifier()
    model.fit(divided_dataset[0]["train"], divided_dataset[1]["train"])
    model.save("tests/back/metrics/rf_model")

    yield divided_dataset, model

    os.remove("tests/back/metrics/rf_model")


def test_accuracy(
    dataset_and_model: Tuple[Tuple[DatasetDict, DatasetDict], RandomForestClassifier]
):
    dataset, model = dataset_and_model
    y_pred = model.predict(dataset[0]["test"])
    score = Accuracy.score(dataset[1]["test"], y_pred)

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_precision(
    dataset_and_model: Tuple[Tuple[DatasetDict, DatasetDict], RandomForestClassifier]
):
    dataset, model = dataset_and_model
    y_pred = model.predict(dataset[0]["test"])

    score = Precision.score(dataset[1]["test"], y_pred)

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_recall(
    dataset_and_model: Tuple[Tuple[DatasetDict, DatasetDict], RandomForestClassifier]
):
    dataset, model = dataset_and_model
    y_pred = model.predict(dataset[0]["test"])
    score = Recall.score(dataset[1]["test"], y_pred)

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_f1_score(
    dataset_and_model: Tuple[Tuple[DatasetDict, DatasetDict], RandomForestClassifier]
):
    dataset, model = dataset_and_model
    y_pred = model.predict(dataset[0]["test"])
    score = F1.score(dataset[1]["test"], y_pred)

    assert isinstance(score, float)
    assert score >= 0.0
    assert score <= 1.0


def test_metrics_different_input_sizes(
    dataset_and_model: Tuple[Tuple[DatasetDict, DatasetDict], RandomForestClassifier]
):
    dataset, model = dataset_and_model
    y_pred = model.predict(dataset[0]["validation"])

    with pytest.raises(
        ValueError,
        match=(
            r"The length of the true labels and the predicted labels must be equal, "
            r"given: len\(true_labels\) = 15 and len\(pred_labels\) = 30\."
        ),
    ):
        Accuracy.score(dataset[1]["test"], y_pred)

    with pytest.raises(
        ValueError,
        match=(
            r"The length of the true labels and the predicted labels must be equal, "
            r"given: len\(true_labels\) = 15 and len\(pred_labels\) = 30\."
        ),
    ):
        Precision.score(dataset[1]["test"], y_pred)

    with pytest.raises(
        ValueError,
        match=(
            r"The length of the true labels and the predicted labels must be equal, "
            r"given: len\(true_labels\) = 15 and len\(pred_labels\) = 30\."
        ),
    ):
        Recall.score(dataset[1]["test"], y_pred)

    with pytest.raises(
        ValueError,
        match=(
            r"The length of the true labels and the predicted labels must be equal, "
            r"given: len\(true_labels\) = 15 and len\(pred_labels\) = 30\."
        ),
    ):
        F1.score(dataset[1]["test"], y_pred)
