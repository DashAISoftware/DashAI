import io
import os

import pytest
from datasets import DatasetDict
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.models.scikit_learn.k_neighbors_classifier import KNeighborsClassifier
from DashAI.back.models.scikit_learn.random_forest_classifier import (
    RandomForestClassifier,
)
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.scikit_learn.svc import SVC


@pytest.fixture(scope="module", name="load_dashaidataset")
def fixture_load_dashaidataset():
    test_dataset_path = "tests/back/models/iris.csv"
    dataloader_test = CSVDataLoader()
    params = {"separator": ","}
    with open(test_dataset_path, "r") as file:
        csv_data = file.read()
    csv_binary = io.BytesIO(bytes(csv_data, encoding="utf8"))
    file = UploadFile(csv_binary)
    datasetdict = dataloader_test.load_data("tests/back/models", params, file=file)
    inputs_columns = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    outputs_columns = ["Species"]
    datasetdict = to_dashai_dataset(datasetdict, inputs_columns, outputs_columns)
    outputs_columns = datasetdict["train"].outputs_columns
    separate_datasetdict = dataloader_test.split_dataset(
        datasetdict, 0.7, 0.1, 0.2, class_column=outputs_columns[0]
    )

    yield separate_datasetdict


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
    os.remove("tests/back/models/svm_model")
