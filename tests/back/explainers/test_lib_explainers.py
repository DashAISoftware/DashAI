import copy

import numpy as np
import pandas as pd
import pyarrow as pa
import pytest

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    select_columns,
    split_dataset,
    split_indexes,
)
from DashAI.back.explainability.explainers.dice_counterfactual import (
    DiceCounterfactual,
)
from DashAI.back.explainability.explainers.lime_text import LimeText
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
def tabular_dataset_fixture():
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


def test_dice_counterfactual(trained_model, dataset):
    x, _ = dataset

    explainer = DiceCounterfactual(trained_model, total_cfs=2, method="random")
    explainer.fit(copy.deepcopy(dataset))

    instances = x["test"].select(range(2))
    explanation = explainer.explain_instance(instances)

    metadata = explanation["metadata"]
    assert metadata["feature_names"] == INPUT_COLUMNS
    assert set(metadata["target_names"]) == set(TARGETS)

    instance_keys = [key for key in explanation if key != "metadata"]
    assert len(instance_keys) == 2

    found_any = False
    for key in instance_keys:
        instance = explanation[key]
        assert len(instance["instance_values"]) == len(INPUT_COLUMNS)
        assert 0 <= instance["predicted_class"] < len(TARGETS)
        for counterfactual in instance["counterfactuals"]:
            found_any = True
            assert len(counterfactual["values"]) == len(INPUT_COLUMNS)
            # A counterfactual must reach a different class.
            assert counterfactual["predicted_class"] != instance["predicted_class"]
    # DiCE's random search on iris should find counterfactuals.
    assert found_any

    plot = explainer.plot(explanation)
    assert len(plot) == 1
    groups = plot[0].groups
    assert len(groups) == len(instance_keys)
    for group in groups:
        assert [a.type for a in group.artifacts] == ["table"]


class DummyTextModel:
    """Predicts positive when the text contains the word 'good'."""

    def predict(self, dataset):
        frame = dataset.to_pandas()
        texts = frame.iloc[:, 0].tolist()
        return np.array(
            [[0.1, 0.9] if "good" in str(t).split() else [0.9, 0.1] for t in texts]
        )


def test_lime_text():
    explainer = LimeText(DummyTextModel(), num_features=5, num_samples=200)
    explainer.metadata = {"target_names": ["negative", "positive"]}

    instances = pd.DataFrame({"text": ["this movie was good indeed"]})
    explanation = explainer.explain_instance(instances)

    instance = explanation[0]
    assert instance["predicted_class"] == 1

    word_weights = dict(instance["word_weights"])
    assert "good" in word_weights
    # 'good' drives the dummy model towards the positive class.
    assert word_weights["good"] > 0
    assert word_weights["good"] == max(word_weights.values())

    plot = explainer.plot(explanation)
    assert len(plot) == 1
    groups = plot[0].groups
    assert len(groups) == 1
    assert [a.type for a in groups[0].artifacts] == ["plotly"]
    assert "good" in explainer.story(explanation, groups[0]).en
