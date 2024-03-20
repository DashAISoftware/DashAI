import io
import os

import numpy as np
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


@pytest.fixture(scope="module", name="split_dataset")
def tabular_model_fixture():
    test_dataset_path = "tests/back/models/iris.csv"
    dataloader_test = CSVDataLoader()

    with open(test_dataset_path, "r") as file:
        csv_binary = io.BytesIO(bytes(file.read(), encoding="utf8"))
        file = UploadFile(csv_binary)

    datasetdict = dataloader_test.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/models",
        params={"separator": ","},
    )

    datasetdict = to_dashai_dataset(
        datasetdict,
        inputs_columns=[
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
        ],
        outputs_columns=["Species"],
    )

    split_dataset = dataloader_test.split_dataset(
        datasetdict,
        train_size=0.7,
        test_size=0.1,
        val_size=0.2,
        class_column=datasetdict["train"].outputs_columns[0],
    )

    return split_dataset


@pytest.fixture(scope="module", name="model_params")
def fixture_model_params() -> dict:
    return {
        "knn": {
            "n_neighbors": 5,
            "weights": "uniform",
            "algorithm": "auto",
        },
        "rf": {
            "n_estimators": 1,
            "max_depth": None,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
            "max_leaf_nodes": None,
            "random_state": None,
        },
        "svc": {
            "C": 1.0,
            "coef0": 0.0,
            "degree": 3.0,
            "gamma": "scale",
            "kernel": "rbf",
            "max_iter": -1,
            "probability": True,
            "shrinking": True,
            "tol": 0.001,
            "verbose": False,
        },
    }


def test_check_is_fitted(split_dataset: DatasetDict, model_params: dict):
    knn_model = KNeighborsClassifier(**model_params["knn"])
    knn_model.fit(split_dataset["train"])

    rf_model = RandomForestClassifier(**model_params["rf"])
    rf_model.fit(split_dataset["train"])

    svc_model = SVC(**model_params["svc"])
    svc_model.fit(split_dataset["train"])

    try:
        check_is_fitted(knn_model)
        check_is_fitted(rf_model)
        check_is_fitted(svc_model)

    except Exception as e:
        pytest.fail(f"Unexpected error in test_fit_models_tabular: {repr(e)}")


def test_predict_tabular_models(split_dataset: DatasetDict, model_params: dict):
    knn_model = KNeighborsClassifier(**model_params["knn"])
    knn_model.fit(split_dataset["train"])
    y_pred_knn = knn_model.predict(split_dataset["test"])

    rf_model = RandomForestClassifier(**model_params["rf"])
    rf_model.fit(split_dataset["train"])
    y_pred_rf = rf_model.predict(split_dataset["test"])

    svc_model = SVC(**model_params["svc"])
    svc_model.fit(split_dataset["train"])
    y_pred_svm = svc_model.predict(split_dataset["test"])

    assert isinstance(y_pred_knn, np.ndarray)
    assert isinstance(y_pred_rf, np.ndarray)
    assert isinstance(y_pred_svm, np.ndarray)

    assert split_dataset["test"].num_rows == len(y_pred_knn)
    assert split_dataset["test"].num_rows == len(y_pred_rf)
    assert split_dataset["test"].num_rows == len(y_pred_svm)


def test_not_fitted_model(split_dataset: DatasetDict, model_params: dict):
    rf = RandomForestClassifier(**model_params["rf"])

    with pytest.raises(NotFittedError):
        rf.predict(split_dataset["test"])


def test_save_and_load_model(split_dataset: DatasetDict, model_params: dict):
    svc_model = SVC(**model_params["svc"])
    svc_model.fit(split_dataset["train"])

    svc_model.save("tests/back/models/svm_model")
    loaded_model = SklearnLikeModel.load("tests/back/models/svm_model")

    y_pred_svm = loaded_model.predict(split_dataset["test"])

    assert isinstance(y_pred_svm, np.ndarray)
    assert split_dataset["test"].num_rows == len(y_pred_svm)

    os.remove("tests/back/models/svm_model")


def test_get_schema_from_model_class():
    models_schemas = [
        m.get_schema() for m in (KNeighborsClassifier, RandomForestClassifier, SVC)
    ]

    for model_schema in models_schemas:
        assert isinstance(model_schema, dict)
        assert "type" in model_schema
        assert model_schema["type"] == "object"
        assert "properties" in model_schema
        assert isinstance(model_schema["properties"], dict)
