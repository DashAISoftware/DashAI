import pytest
from datasets import DatasetDict
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted

from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
from DashAI.back.models.scikit_learn.k_neighbors_classifier import KNeighborsClassifier
from DashAI.back.models.scikit_learn.random_forest_classifier import (
    RandomForestClassifier,
)
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.scikit_learn.svc import SVC


@pytest.fixture(scope="module", name="load_dashaidataset")
def fixture_load_dashaidataset():
    dashai_datasetdict = load_dataset("tests/back/dataloaders/dashaidataset")
    return dashai_datasetdict


def test_fit_models_tabular(load_dashaidataset: DatasetDict):
    knn = KNeighborsClassifier()
    dataset_prepared = knn.format_data(load_dashaidataset)
    knn.fit(dataset_prepared["train"]["input"], dataset_prepared["train"]["output"])
    rf = RandomForestClassifier()
    dataset_prepared = rf.format_data(load_dashaidataset)
    rf.fit(dataset_prepared["train"]["input"], dataset_prepared["train"]["output"])
    svm = SVC()
    dataset_prepared = svm.format_data(load_dashaidataset)
    svm.fit(dataset_prepared["train"]["input"], dataset_prepared["train"]["output"])
    try:
        check_is_fitted(knn)
        check_is_fitted(rf)
        check_is_fitted(svm)
    except Exception as e:
        pytest.fail(f"Unexpected error in test_fit_models_tabular: {repr(e)}")


def test_predict_models_tabular(load_dashaidataset: DatasetDict):
    knn = KNeighborsClassifier()
    dataset_prepared = knn.format_data(load_dashaidataset)
    knn.fit(dataset_prepared["train"]["input"], dataset_prepared["train"]["output"])
    pred_knn = knn.predict(dataset_prepared["test"]["input"])

    rf = RandomForestClassifier()
    dataset_prepared = rf.format_data(load_dashaidataset)
    rf.fit(dataset_prepared["train"]["input"], dataset_prepared["train"]["output"])
    pred_ref = rf.predict(dataset_prepared["test"]["input"])

    svm = SVC()
    dataset_prepared = svm.format_data(load_dashaidataset)
    svm.fit(dataset_prepared["train"]["input"], dataset_prepared["train"]["output"])
    pred_svm = svm.predict(dataset_prepared["test"]["input"])

    assert len(dataset_prepared["test"]["input"]) == len(pred_knn)
    assert len(dataset_prepared["test"]["input"]) == len(pred_ref)
    assert len(dataset_prepared["test"]["input"]) == len(pred_svm)


def test_not_fitted_models_tabular(load_dashaidataset: DatasetDict):
    rf = RandomForestClassifier()
    dataset_prepared = rf.format_data(load_dashaidataset)

    with pytest.raises(NotFittedError):
        rf.predict(dataset_prepared["test"]["input"])


def test_save_and_load_model(load_dashaidataset: DatasetDict):
    svm = SVC()
    dataset_prepared = svm.format_data(load_dashaidataset)
    svm.fit(dataset_prepared["train"]["input"], dataset_prepared["train"]["output"])
    svm.save("tests/back/models/svm_model")
    model_svm = SklearnLikeModel.load("tests/back/models/svm_model")
    pred_svm = model_svm.predict(dataset_prepared["test"]["input"])
    assert len(dataset_prepared["test"]["input"]) == len(pred_svm)


def test_get_schema_from_model():
    models_schemas = map(
        lambda m: m.get_schema(), [KNeighborsClassifier, RandomForestClassifier, SVC]
    )

    for model_schema in models_schemas:
        assert type(model_schema) is dict
        assert "type" in model_schema.keys()
        assert model_schema["type"] == "object"
        assert "properties" in model_schema.keys()
        assert type(model_schema["properties"]) is dict
