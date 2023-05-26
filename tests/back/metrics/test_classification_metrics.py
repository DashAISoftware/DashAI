import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
from DashAI.back.metrics.Classification.accuracy import Accuracy
from DashAI.back.metrics.Classification.f1score import F1Score
from DashAI.back.metrics.Classification.precision import Precision
from DashAI.back.metrics.Classification.recall import Recall
from DashAI.back.models.scikit_learn.random_forest_classifier import (
    RandomForestClassifier,
)
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask


@pytest.fixture(scope="module", name="datasetdashai_tabular_classification")
def fixture_datasetdashai_tab_class_and_fit_model():
    tabular_task = TabularClassificationTask.create()
    dashai_datasetdict = load_dataset("tests/back/metrics/dashaidataset")
    name_datasetdict = "Iris"
    dashai_datasetdict = tabular_task.prepare_for_task(dashai_datasetdict)
    tabular_task.validate_dataset_for_task(dashai_datasetdict, name_datasetdict)
    rf = RandomForestClassifier()
    dataset_prepared = rf.format_data(dashai_datasetdict)
    rf.fit(dataset_prepared["train"]["input"], dataset_prepared["train"]["output"])
    rf.save("tests/back/metrics/rf_model")
    yield dataset_prepared


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
        isinstance(F1Score.score(dataset_prepared["test"]["output"], pred_ref), float)
    except Exception as e:
        pytest.fail(f"Unexpected error in test_f1score: {repr(e)}")


def test_wrong_size_metric(datasetdashai_tabular_classification: dict):
    dataset_prepared = datasetdashai_tabular_classification
    model_rf = SklearnLikeModel.load("tests/back/metrics/rf_model")
    pred_ref = model_rf.predict(dataset_prepared["validation"]["input"])
    with pytest.raises(ValueError):
        Accuracy.score(dataset_prepared["test"]["output"], pred_ref)
