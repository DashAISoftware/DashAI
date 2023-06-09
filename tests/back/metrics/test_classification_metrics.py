import io
import os

import pytest
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
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask


@pytest.fixture(scope="module", name="datasetdashai_tabular_classification")
def fixture_datasetdashai_tab_class_and_fit_model():
    test_dataset_path = "tests/back/metrics/iris.csv"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}
    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
    csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
    file = UploadFile(csv_binary)
    datasetdict = dataloader_test.load_data("tests/back/metrics", params, file=file)
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    datasetdict = to_dashai_dataset(datasetdict, inputs_columns, outputs_columns)
    outputs_columns = datasetdict["train"].outputs_columns
    dashai_datasetdict = dataloader_test.split_dataset(
        datasetdict, 0.7, 0.1, 0.2, class_column=outputs_columns[0]
    )
    tabular_task = TabularClassificationTask.create()
    name_datasetdict = "Iris"
    dashai_datasetdict = tabular_task.prepare_for_task(dashai_datasetdict)
    tabular_task.validate_dataset_for_task(dashai_datasetdict, name_datasetdict)
    rf = RandomForestClassifier()
    dataset_prepared = rf.format_data(dashai_datasetdict)
    rf.fit(dataset_prepared["train"]["input"], dataset_prepared["train"]["output"])
    rf.save("tests/back/metrics/rf_model")
    yield dataset_prepared
    os.remove("tests/back/metrics/rf_model")


def test_accuracy(datasetdashai_tabular_classification: dict):
    dataset_prepared = datasetdashai_tabular_classification
    model_rf = SklearnLikeModel.load("tests/back/metrics/rf_model")
    pred_ref = model_rf.predict(dataset_prepared["test"]["input"])
    try:
        isinstance(Accuracy.score(dataset_prepared["test"]["output"], pred_ref), float)
    except Exception as e:
        pytest.fail(f"Unexpected error in test_accuracy: {repr(e)}")


def test_precision(datasetdashai_tabular_classification: dict):
    dataset_prepared = datasetdashai_tabular_classification
    model_rf = SklearnLikeModel.load("tests/back/metrics/rf_model")
    pred_ref = model_rf.predict(dataset_prepared["test"]["input"])
    try:
        isinstance(Precision.score(dataset_prepared["test"]["output"], pred_ref), float)
    except Exception as e:
        pytest.fail(f"Unexpected error in test_precision: {repr(e)}")


def test_recall(datasetdashai_tabular_classification: dict):
    dataset_prepared = datasetdashai_tabular_classification
    model_rf = SklearnLikeModel.load("tests/back/metrics/rf_model")
    pred_ref = model_rf.predict(dataset_prepared["test"]["input"])
    try:
        isinstance(Recall.score(dataset_prepared["test"]["output"], pred_ref), float)
    except Exception as e:
        pytest.fail(f"Unexpected error in test_recall: {repr(e)}")


def test_f1score(datasetdashai_tabular_classification: dict):
    dataset_prepared = datasetdashai_tabular_classification
    model_rf = SklearnLikeModel.load("tests/back/metrics/rf_model")
    pred_ref = model_rf.predict(dataset_prepared["test"]["input"])
    try:
        isinstance(F1.score(dataset_prepared["test"]["output"], pred_ref), float)
    except Exception as e:
        pytest.fail(f"Unexpected error in test_f1score: {repr(e)}")


def test_wrong_size_metric(datasetdashai_tabular_classification: dict):
    dataset_prepared = datasetdashai_tabular_classification
    model_rf = SklearnLikeModel.load("tests/back/metrics/rf_model")
    pred_ref = model_rf.predict(dataset_prepared["validation"]["input"])
    with pytest.raises(ValueError):
        Accuracy.score(dataset_prepared["test"]["output"], pred_ref)
