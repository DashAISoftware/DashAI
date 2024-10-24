import io

import pytest
from datasets import DatasetDict, concatenate_datasets
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import (
    select_columns,
    split_dataset,
    split_indexes,
)
from DashAI.back.explainability import (
    KernelShap,
    PartialDependence,
    PermutationFeatureImportance,
)
from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.scikit_learn.decision_tree_classifier import (
    DecisionTreeClassifier,
)

INPUT_COLUMNS = [
    "SepalLengthCm",
    "SepalWidthCm",
    "PetalLengthCm",
    "PetalWidthCm",
]
OUTPUT_COLUMNS = ["Species"]
TARGETS = [
    "Iris-setosa",
    "Iris-versicolor",
    "Iris-virginica",
]


@pytest.fixture(scope="module", name="dataset")
def tabular_model_fixture():
    dataset_path = "tests/back/explainers/iris.csv"
    dataloader = CSVDataLoader()

    with open(dataset_path, "r") as file:
        csv_binary = io.BytesIO(bytes(file.read(), encoding="utf8"))
        file = UploadFile(csv_binary)

    datasetdict = dataloader.load_data(
        filepath_or_buffer=file,
        temp_path="tests/back/explainers",
        params={"separator": ","},
    )

    total_rows = len(datasetdict["train"])
    train_indexes, test_indexes, val_indexes = split_indexes(
        total_rows=total_rows, train_size=0.7, test_size=0.1, val_size=0.2
    )
    split_dataset_dict = split_dataset(
        datasetdict["train"],
        train_indexes=train_indexes,
        test_indexes=test_indexes,
        val_indexes=val_indexes,
    )

    dataset = select_columns(split_dataset_dict, INPUT_COLUMNS, OUTPUT_COLUMNS)
    types = {column: "Categorical" for column in OUTPUT_COLUMNS}

    for split in dataset[1]:
        dataset[1][split] = dataset[1][split].change_columns_type(types)

    return dataset


@pytest.fixture(scope="module", name="trained_model")
def trained_model(dataset):
    x, y = dataset
    model = DecisionTreeClassifier(
        criterion="gini",
        max_depth=3,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features=None,
    )
    model.fit(x["train"], y["train"])

    return model


def test_partial_dependence(trained_model: BaseModel, dataset: DatasetDict):
    parameters = {
        "grid_resolution": 50,
        "lower_percentile": 0.01,
        "upper_percentile": 0.99,
    }
    explainer = PartialDependence(trained_model, **parameters)
    explanation = explainer.explain(dataset)
    plot = explainer.plot(explanation)

    metadata = explanation.pop("metadata")
    assert set(metadata["target_names"]) == set(TARGETS)

    assert len(explanation) == len(INPUT_COLUMNS)
    assert len(plot) == 1

    for feature_key in explanation.values():
        assert "grid_values" in feature_key
        assert "average" in feature_key


def test_wrong_parameters_partial_dependence(trained_model: BaseModel):
    parameters = {
        "grid_resolution": 50,
        "lower_percentile": 2,
        "upper_percentile": 1,
    }

    with pytest.raises(
        AssertionError,
    ):
        PartialDependence(trained_model, **parameters)


def test_permutation_feature_importance(trained_model: BaseModel, dataset: DatasetDict):
    parameters = {
        "scoring": "accuracy",
        "n_repeats": 5,
        "random_state": None,
        "max_samples": 1,
    }
    explainer = PermutationFeatureImportance(trained_model, **parameters)
    explanation = explainer.explain(dataset)
    plot = explainer.plot(explanation)

    assert all(
        key in explanation
        for key in ["features", "importances_mean", "importances_std"]
    )
    assert len(plot) == 1

    for values in explanation.values():
        assert len(values) == len(INPUT_COLUMNS)

    parameters = {
        "scoring": "balanced_accuracy",
        "n_repeats": 5,
        "random_state": None,
        "max_samples": 1,
    }
    explainer = PermutationFeatureImportance(trained_model, **parameters)
    explanation = explainer.explain(dataset)
    plot = explainer.plot(explanation)

    assert all(
        key in explanation
        for key in ["features", "importances_mean", "importances_std"]
    )
    assert len(plot) == 1

    for values in explanation.values():
        assert len(values) == len(INPUT_COLUMNS)


def test_kernel_shap(trained_model: BaseModel, dataset: DatasetDict):
    parameters = {
        "link": "identity",
    }
    fit_parameters = {
        "sample_background_data": True,
        "n_background_samples": 50,
        "sampling_method": "kmeans",
    }

    explainer = KernelShap(trained_model, **parameters)
    explainer.fit(background_dataset=dataset, **fit_parameters)
    explanation = explainer.explain_instance(dataset[0])
    plot = explainer.plot(explanation)

    metadata = explanation.pop("metadata")
    base_values = explanation.pop("base_values")

    splits = list(dataset[0].keys())
    X = dataset[0][splits[0]]
    for split in splits[1:]:
        X = concatenate_datasets([X, dataset[0][split]])

    assert len(explanation) == len(X)
    assert len(base_values) == len(TARGETS)
    assert metadata["feature_names"] == INPUT_COLUMNS
    assert set(metadata["target_names"]) == set(TARGETS)
    assert len(plot) == len(X)

    for instance_key in explanation.values():
        assert "instance_values" in instance_key
        assert "model_prediction" in instance_key
        assert "shap_values" in instance_key
