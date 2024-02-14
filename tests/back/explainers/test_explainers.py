import io
import os

import pytest
from datasets import DatasetDict
from starlette.datastructures import UploadFile

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dataloader import to_dashai_dataset
from DashAI.back.explainability import (
    KernelShap,
    PartialDependence,
    PermutationFeatureImportance,
)
from DashAI.back.models.base_model import BaseModel
from DashAI.back.models.scikit_learn.decision_tree_classifier import (
    DecisionTreeClassifier,
)
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask


@pytest.fixture(scope="module", name="split_dataset")
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

    split_dataset = dataloader.split_dataset(
        datasetdict,
        train_size=0.4,
        test_size=0.4,
        val_size=0.2,
        class_column=datasetdict["train"].outputs_columns[0],
    )

    return split_dataset


@pytest.fixture(scope="module", name="trained_model")
def created_trained_model(split_dataset):
    model = DecisionTreeClassifier()
    model.fit(split_dataset["train"])

    return model


def test_partial_dependence(trained_model: BaseModel, split_dataset: DatasetDict):
    task = TabularClassificationTask()
    dataset = task.prepare_for_task(split_dataset)
    dashai_dataset = to_dashai_dataset(
        dataset,
        inputs_columns=[
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
        ],
        outputs_columns=["Species"],
    )

    parameters = {
        "categorical_features": None,
        "grid_resolution": 50,
        "lower_percentile": 0.01,
        "upper_percentile": 0.99,
    }
    explainer = PartialDependence(trained_model, **parameters)
    explanation = explainer.explain(dashai_dataset)

    assert len(explanation) == 4

    for feature_key in explanation.values():
        assert "grid_values" in feature_key
        assert "average" in feature_key


def test_wrong_parameters_partial_dependence(trained_model: BaseModel):
    parameters = {
        "categorical_features": None,
        "grid_resolution": 50,
        "lower_percentile": 2,
        "upper_percentile": 1,
    }

    with pytest.raises(
        AssertionError,
    ):
        PartialDependence(trained_model, **parameters)


def test_permutation_feature_importance(
    trained_model: BaseModel, split_dataset: DatasetDict
):
    task = TabularClassificationTask()
    dataset = task.prepare_for_task(split_dataset)
    dashai_dataset = to_dashai_dataset(
        dataset,
        inputs_columns=[
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
        ],
        outputs_columns=["Species"],
    )

    parameters = {
        "scoring": "accuracy",
        "n_repeats": 5,
        "random_state": None,
        "max_samples": 1,
    }
    explainer = PermutationFeatureImportance(trained_model, **parameters)
    explanation = explainer.explain(dashai_dataset)

    assert len(explanation) == 2
    for values in explanation.values():
        assert len(values) == 4


def test_wrong_parameters_permutation_importance(
    trained_model: BaseModel, split_dataset: DatasetDict
):
    parameters = {
        "categorical_features": None,
        "grid_resolution": 50,
        "lower_percentile": 2,
        "upper_percentile": 1,
    }

    with pytest.raises(
        AssertionError,
    ):
        PartialDependence(trained_model, **parameters)


def test_kernel_shap(trained_model: BaseModel, split_dataset: DatasetDict):
    task = TabularClassificationTask()
    dataset = task.prepare_for_task(split_dataset)
    dashai_dataset = to_dashai_dataset(
        dataset,
        inputs_columns=[
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
        ],
        outputs_columns=["Species"],
    )

    parameters = {
        "link": "identity",
    }

    fit_parameters = {
        "sample_background_data": True,
        "n_background_samples": 50,
        "sampling_method": "kmeans",
        "categorical_features": False,
    }

    explainer = KernelShap(trained_model, **parameters)
    explainer.fit(background_data=dashai_dataset, **fit_parameters)
    explanation = explainer.explain_instance(dashai_dataset["test"])

    assert len(explanation) == len(dashai_dataset["test"]) + 1
    assert len(explanation["base_values"]) == 3

    explanation.pop("base_values")

    for instance_key in explanation.values():
        assert "instance_values" in instance_key
        assert "model_prediction" in instance_key
        assert "shap_values" in instance_key


def test_save_and_load_explanation(
    trained_model: BaseModel, split_dataset: DatasetDict
):
    task = TabularClassificationTask()
    dataset = task.prepare_for_task(split_dataset)
    dashai_dataset = to_dashai_dataset(
        dataset,
        inputs_columns=[
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
        ],
        outputs_columns=["Species"],
    )

    parameters = {
        "categorical_features": None,
        "grid_resolution": 50,
        "lower_percentile": 0.01,
        "upper_percentile": 0.99,
    }
    explainer = PartialDependence(trained_model, **parameters)
    explainer.explain(dashai_dataset)

    path = os.getcwd()
    filename = "test_explanation.json"

    # Save
    explainer.save_explanation(os.path.join(path, filename))

    # Load
    explanation = explainer.load_explanation(os.path.join(path, filename))

    # Remove file
    os.remove(os.path.join(path, filename))

    assert len(explanation) == 4

    for feature_key in explanation.values():
        assert "grid_values" in feature_key
        assert "average" in feature_key
