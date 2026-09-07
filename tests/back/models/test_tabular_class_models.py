# flake8: noqa: ERA001
from typing import Tuple

import numpy as np
import pyarrow as pa
import pytest
from datasets import DatasetDict
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    select_columns,
    split_dataset,
    split_indexes,
    to_dashai_dataset,
)
from DashAI.back.models.scikit_learn.adaboost_classifier import AdaBoostClassifier
from DashAI.back.models.scikit_learn.bagging_classifier import BaggingClassifier
from DashAI.back.models.scikit_learn.extra_trees_classifier import ExtraTreesClassifier
from DashAI.back.models.scikit_learn.gaussian_nb import GaussianNB
from DashAI.back.models.scikit_learn.gradient_boosting_classifier import (
    GradientBoostingClassifier,
)
from DashAI.back.models.scikit_learn.k_neighbors_classifier import KNeighborsClassifier
from DashAI.back.models.scikit_learn.linear_svc_classifier import LinearSVCClassifier
from DashAI.back.models.scikit_learn.mlp_classifier import MLPClassifier
from DashAI.back.models.scikit_learn.random_forest_classifier import (
    RandomForestClassifier,
)
from DashAI.back.models.scikit_learn.sgd_classifier import SGDClassifier
from DashAI.back.models.scikit_learn.svc import SVC
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.utils import save_types_in_arrow_metadata
from DashAI.back.types.value_types import Float


@pytest.fixture(scope="module", name="divided_dataset")
def tabular_model_fixture():
    test_dataset_path = "tests/back/models/iris.csv"
    dataloader_test = CSVDataLoader()

    datasetdict = dataloader_test.load_data(
        filepath_or_buffer=test_dataset_path,
        temp_path="tests/back/models",
        params={
            "separator": ",",
            "schema": {
                "SepalLengthCm": {"type": "Float", "dtype": "float64"},
                "SepalWidthCm": {"type": "Float", "dtype": "float64"},
                "PetalLengthCm": {"type": "Float", "dtype": "float64"},
                "PetalWidthCm": {"type": "Float", "dtype": "float64"},
                "Species": {"type": "Categorical", "dtype": "string"},
            },
        },
    )

    datasetdict = to_dashai_dataset(datasetdict)

    datasetdict.types = datasetdict.types = {
        "SepalLengthCm": Float(arrow_type=pa.float64()),
        "SepalWidthCm": Float(arrow_type=pa.float64()),
        "PetalLengthCm": Float(arrow_type=pa.float64()),
        "PetalWidthCm": Float(arrow_type=pa.float64()),
        "Species": Categorical(
            values=["Iris-setosa", "Iris-versicolor", "Iris-virginica"]
        ),
    }

    new_table = save_types_in_arrow_metadata(
        datasetdict.arrow_table,
        {col: dtype.to_string() for col, dtype in datasetdict.types.items()},
    )

    datasetdict = DashAIDataset(
        new_table, splits=datasetdict.splits, types=datasetdict.types
    )

    total_rows = datasetdict.num_rows
    train_indexes, test_indexes, val_indexes = split_indexes(
        total_rows=total_rows, train_size=0.7, test_size=0.1, val_size=0.2
    )
    split_dataset_dict = split_dataset(
        datasetdict,
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )

    inputs_columns = [
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
    ]
    outputs_columns = ["Species"]
    x, y = select_columns(split_dataset_dict, inputs_columns, outputs_columns)
    x = split_dataset(x)
    y = split_dataset(y)
    return (x, y)


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
        "gradient_boosting": {
            "loss": "log_loss",
            "learning_rate": 0.1,
            "n_estimators": 5,
            "max_depth": 2,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
            "subsample": 1.0,
            "random_state": 42,
        },
        "extra_trees": {
            "n_estimators": 5,
            "max_depth": None,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
            "bootstrap": False,
            "random_state": 42,
        },
        "adaboost": {
            "n_estimators": 5,
            "learning_rate": 1.0,
            "random_state": 42,
        },
        "bagging": {
            "n_estimators": 5,
            "max_samples": 1.0,
            "max_features": 1.0,
            "bootstrap": True,
            "bootstrap_features": False,
            "random_state": 42,
        },
        "gaussian_nb": {
            "var_smoothing": 1e-9,
        },
        "mlp": {
            "hidden_layer_size": 10,
            "activation": "relu",
            "solver": "adam",
            "alpha": 0.0001,
            "learning_rate_init": 0.001,
            "max_iter": 50,
            "random_state": 42,
        },
        "linear_svc": {
            "C": 1.0,
            "loss": "squared_hinge",
            "max_iter": 100,
            "tol": 1e-4,
            "fit_intercept": True,
            "random_state": 42,
        },
        "sgd": {
            "loss": "hinge",
            "alpha": 0.0001,
            "max_iter": 100,
            "tol": 1e-3,
            "learning_rate": "optimal",
            "random_state": 42,
        },
    }


def test_check_is_fitted(
    divided_dataset: Tuple[DatasetDict, DatasetDict], model_params: dict
):
    knn_model = KNeighborsClassifier(**model_params["knn"])

    knn_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])

    rf_model = RandomForestClassifier(**model_params["rf"])
    rf_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])

    svc_model = SVC(**model_params["svc"])
    svc_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])

    try:
        check_is_fitted(knn_model)
        check_is_fitted(rf_model)
        check_is_fitted(svc_model)

    except Exception as e:
        pytest.fail(f"Unexpected error in test_fit_models_tabular: {repr(e)}")


def test_predict_tabular_models(
    divided_dataset: Tuple[DatasetDict, DatasetDict], model_params: dict
):
    knn_model = KNeighborsClassifier(**model_params["knn"])
    knn_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])
    y_pred_knn = knn_model.predict(divided_dataset[0]["test"])

    rf_model = RandomForestClassifier(**model_params["rf"])
    rf_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])
    y_pred_rf = rf_model.predict(divided_dataset[0]["test"])

    svc_model = SVC(**model_params["svc"])
    svc_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])
    y_pred_svm = svc_model.predict(divided_dataset[0]["test"])

    assert isinstance(y_pred_knn, np.ndarray)
    assert isinstance(y_pred_rf, np.ndarray)
    assert isinstance(y_pred_svm, np.ndarray)

    assert divided_dataset[0]["test"].num_rows == len(y_pred_knn)
    assert divided_dataset[0]["test"].num_rows == len(y_pred_rf)
    assert divided_dataset[0]["test"].num_rows == len(y_pred_svm)


def test_not_fitted_model(
    divided_dataset: Tuple[DatasetDict, DatasetDict], model_params: dict
):
    rf = RandomForestClassifier(**model_params["rf"])

    with pytest.raises(NotFittedError):
        rf.predict(divided_dataset[0]["test"])


# def test_save_and_load_model(
#     divided_dataset: Tuple[DatasetDict, DatasetDict], model_params: dict
# ):
#     svc_model = SVC(**model_params["svc"])
#     svc_model.fit(divided_dataset[0]["train"], divided_dataset[1]["train"])

#     svc_model.save("tests/back/models/svm_model")
#     loaded_model = SklearnLikeModel.load("tests/back/models/svm_model")

#     y_pred_svm = loaded_model.predict(divided_dataset[0]["test"])

#     assert isinstance(y_pred_svm, np.ndarray)
#     assert divided_dataset[0]["test"].num_rows == len(y_pred_svm)

#     os.remove("tests/back/models/svm_model")


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


def test_check_is_fitted_new_classifiers(
    divided_dataset: Tuple[DatasetDict, DatasetDict], model_params: dict
):
    gb_model = GradientBoostingClassifier(**model_params["gradient_boosting"])
    gb_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])

    et_model = ExtraTreesClassifier(**model_params["extra_trees"])
    et_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])

    ab_model = AdaBoostClassifier(**model_params["adaboost"])
    ab_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])

    bag_model = BaggingClassifier(**model_params["bagging"])
    bag_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])

    gnb_model = GaussianNB(**model_params["gaussian_nb"])
    gnb_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])

    mlp_model = MLPClassifier(**model_params["mlp"])
    mlp_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])

    lsvc_model = LinearSVCClassifier(**model_params["linear_svc"])
    lsvc_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])

    sgd_model = SGDClassifier(**model_params["sgd"])
    sgd_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])

    try:
        check_is_fitted(gb_model)
        check_is_fitted(et_model)
        check_is_fitted(ab_model)
        check_is_fitted(bag_model)
        check_is_fitted(gnb_model)
        check_is_fitted(mlp_model)
        check_is_fitted(lsvc_model)
        check_is_fitted(sgd_model)
    except Exception as e:
        pytest.fail(
            f"Unexpected error in test_check_is_fitted_new_classifiers: {repr(e)}"
        )


def test_predict_new_classifiers(
    divided_dataset: Tuple[DatasetDict, DatasetDict], model_params: dict
):
    gb_model = GradientBoostingClassifier(**model_params["gradient_boosting"])
    gb_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])
    y_pred_gb = gb_model.predict(divided_dataset[0]["test"])

    et_model = ExtraTreesClassifier(**model_params["extra_trees"])
    et_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])
    y_pred_et = et_model.predict(divided_dataset[0]["test"])

    ab_model = AdaBoostClassifier(**model_params["adaboost"])
    ab_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])
    y_pred_ab = ab_model.predict(divided_dataset[0]["test"])

    bag_model = BaggingClassifier(**model_params["bagging"])
    bag_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])
    y_pred_bag = bag_model.predict(divided_dataset[0]["test"])

    gnb_model = GaussianNB(**model_params["gaussian_nb"])
    gnb_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])
    y_pred_gnb = gnb_model.predict(divided_dataset[0]["test"])

    mlp_model = MLPClassifier(**model_params["mlp"])
    mlp_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])
    y_pred_mlp = mlp_model.predict(divided_dataset[0]["test"])

    lsvc_model = LinearSVCClassifier(**model_params["linear_svc"])
    lsvc_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])
    y_pred_lsvc = lsvc_model.predict(divided_dataset[0]["test"])

    sgd_model = SGDClassifier(**model_params["sgd"])
    sgd_model.train(divided_dataset[0]["train"], divided_dataset[1]["train"])
    y_pred_sgd = sgd_model.predict(divided_dataset[0]["test"])

    n_test = divided_dataset[0]["test"].num_rows
    for y_pred in (
        y_pred_gb,
        y_pred_et,
        y_pred_ab,
        y_pred_bag,
        y_pred_gnb,
        y_pred_mlp,
        y_pred_lsvc,
        y_pred_sgd,
    ):
        assert isinstance(y_pred, np.ndarray)
        assert len(y_pred) == n_test


def test_not_fitted_new_classifiers(
    divided_dataset: Tuple[DatasetDict, DatasetDict], model_params: dict
):
    with pytest.raises(NotFittedError):
        GradientBoostingClassifier(**model_params["gradient_boosting"]).predict(
            divided_dataset[0]["test"]
        )

    with pytest.raises(NotFittedError):
        LinearSVCClassifier(**model_params["linear_svc"]).predict(
            divided_dataset[0]["test"]
        )

    with pytest.raises(NotFittedError):
        SGDClassifier(**model_params["sgd"]).predict(divided_dataset[0]["test"])


def test_get_schema_from_new_classifier_classes():
    new_models = (
        GradientBoostingClassifier,
        ExtraTreesClassifier,
        AdaBoostClassifier,
        BaggingClassifier,
        GaussianNB,
        MLPClassifier,
        LinearSVCClassifier,
        SGDClassifier,
    )
    for model_cls in new_models:
        schema = model_cls.get_schema()
        assert isinstance(schema, dict), f"{model_cls.__name__} schema is not a dict"
        assert schema.get("type") == "object", (
            f"{model_cls.__name__} schema type != object"
        )
        assert isinstance(schema.get("properties"), dict), (
            f"{model_cls.__name__} schema has no properties dict"
        )
