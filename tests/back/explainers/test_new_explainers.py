import copy

import numpy as np
import pyarrow as pa
import pytest

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    select_columns,
    split_dataset,
    split_indexes,
)
from DashAI.back.explainability.explainers.contrastive_shap import ContrastiveShap
from DashAI.back.explainability.explainers.nearest_counterfactual import (
    NearestCounterfactual,
)
from DashAI.back.models.scikit_learn.decision_tree_classifier import (
    DecisionTreeClassifier,
)
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.utils import save_types_in_arrow_metadata
from DashAI.back.types.value_types import Float

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

    datasetdict = dataloader.load_data(
        filepath_or_buffer=dataset_path,
        temp_path="tests/back/explainers",
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
    datasetdict.types = {
        "SepalLengthCm": Float(arrow_type=pa.float64()),
        "SepalWidthCm": Float(arrow_type=pa.float64()),
        "PetalLengthCm": Float(arrow_type=pa.float64()),
        "PetalWidthCm": Float(arrow_type=pa.float64()),
        "Species": Categorical(values=TARGETS),
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

    x, y = select_columns(split_dataset_dict, INPUT_COLUMNS, OUTPUT_COLUMNS)

    y = split_dataset(y)
    x = split_dataset(x)

    return x, y


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
    model.train(x["train"], y["train"])

    return model


def test_nearest_counterfactual(trained_model, dataset):
    x, _ = dataset
    n_counterfactuals = 2

    explainer = NearestCounterfactual(
        trained_model, n_counterfactuals=n_counterfactuals, distance="l1"
    )
    explainer.fit(copy.deepcopy(dataset))

    instances = x["test"]
    explanation = explainer.explain_instance(instances)

    metadata = explanation["metadata"]
    assert set(metadata["target_names"]) == set(TARGETS)
    assert metadata["feature_names"] == INPUT_COLUMNS

    instance_keys = [key for key in explanation if key != "metadata"]
    assert len(instance_keys) == instances.num_rows

    for key in instance_keys:
        instance = explanation[key]
        assert len(instance["instance_values"]) == len(INPUT_COLUMNS)
        assert len(instance["model_prediction"]) == len(TARGETS)
        assert len(instance["counterfactuals"]) <= n_counterfactuals

        for counterfactual in instance["counterfactuals"]:
            # A counterfactual must be classified differently.
            assert counterfactual["predicted_class"] != instance["predicted_class"]
            assert counterfactual["distance"] >= 0
            assert len(counterfactual["values"]) == len(INPUT_COLUMNS)

    plot = explainer.plot(explanation)
    # A single grouped artifact with one group per instance, each holding a
    # comparison table.
    assert len(plot) == 1
    groups = plot[0].groups
    assert len(groups) == len(instance_keys)
    for group in groups:
        assert [a.type for a in group.artifacts] == ["table"]

    first_table = groups[0].artifacts[0].payload
    # Feature rows plus the predicted class row.
    assert len(first_table.rows) == len(INPUT_COLUMNS) + 1
    for cell in first_table.highlight:
        assert 0 <= cell.row < len(first_table.rows)
        assert 0 <= cell.column < len(first_table.columns)


def test_nearest_counterfactual_distance_l2(trained_model, dataset):
    x, _ = dataset

    explainer = NearestCounterfactual(trained_model, n_counterfactuals=1, distance="l2")
    explainer.fit(copy.deepcopy(dataset))

    instances = x["test"].select(range(2))
    explanation = explainer.explain_instance(instances)

    instance_keys = [key for key in explanation if key != "metadata"]
    assert len(instance_keys) == 2
    for key in instance_keys:
        assert len(explanation[key]["counterfactuals"]) == 1


def test_contrastive_shap(trained_model, dataset):
    x, _ = dataset

    explainer = ContrastiveShap(trained_model)
    explainer.fit(
        copy.deepcopy(dataset),
        sample_background_data=True,
        background_fraction=0.3,
    )

    instances = x["test"].select(range(3))
    explanation = explainer.explain_instance(instances)

    metadata = explanation["metadata"]
    assert set(metadata["target_names"]) == set(TARGETS)

    instance_keys = [key for key in explanation if key != "metadata"]
    assert len(instance_keys) == 3

    for key in instance_keys:
        instance = explanation[key]
        assert instance["fact_class"] != instance["foil_class"]
        assert len(instance["delta_values"]) == len(INPUT_COLUMNS)

        delta = np.asarray(instance["delta_values"])
        fact = np.asarray(instance["fact_shap_values"])
        foil = np.asarray(instance["foil_shap_values"])
        assert np.allclose(delta, fact - foil, atol=1e-2)

    plot = explainer.plot(explanation)
    assert len(plot) == 1
    groups = plot[0].groups
    assert len(groups) == len(instance_keys)
    assert [a.type for a in groups[0].artifacts] == ["plotly"]
    assert "rather than" in explainer.story(explanation, groups[0]).en


def test_contrastive_shap_fixed_foil(trained_model, dataset):
    x, _ = dataset

    explainer = ContrastiveShap(trained_model, foil_class="Iris-virginica")
    explainer.fit(copy.deepcopy(dataset))

    instances = x["test"].select(range(2))
    explanation = explainer.explain_instance(instances)

    target_names = explanation["metadata"]["target_names"]
    virginica = target_names.index("Iris-virginica")

    instance_keys = [key for key in explanation if key != "metadata"]
    for key in instance_keys:
        instance = explanation[key]
        if instance["fact_class"] != virginica:
            assert instance["foil_class"] == virginica
        else:
            # Fixed foil equals the fact: falls back to the runner-up class.
            assert instance["foil_class"] != virginica
