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
from DashAI.back.explainability.explainers.regression_kernel_shap import (
    RegressionKernelShap,
)
from DashAI.back.explainability.explainers.regression_partial_dependence import (
    RegressionPartialDependence,
)
from DashAI.back.explainability.explainers.regression_permutation_feature_importance import (  # noqa: E501
    RegressionPermutationFeatureImportance,
)
from DashAI.back.explainability.explainers.token_ablation import TokenAblation
from DashAI.back.models.scikit_learn.linear_regression import LinearRegression
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.utils import save_types_in_arrow_metadata
from DashAI.back.types.value_types import Float

REGRESSION_INPUT_COLUMNS = [
    "SepalLengthCm",
    "SepalWidthCm",
    "PetalLengthCm",
]
REGRESSION_OUTPUT_COLUMNS = ["PetalWidthCm"]


@pytest.fixture(scope="module", name="regression_dataset")
def regression_dataset_fixture():
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

    x, y = select_columns(
        split_dataset_dict, REGRESSION_INPUT_COLUMNS, REGRESSION_OUTPUT_COLUMNS
    )

    y = split_dataset(y)
    x = split_dataset(x)

    return x, y


@pytest.fixture(scope="module", name="trained_regressor")
def trained_regressor(regression_dataset):
    x, y = regression_dataset
    model = LinearRegression(fit_intercept=True)
    model.train(x["train"], y["train"])

    return model


def test_regression_permutation_feature_importance(
    trained_regressor, regression_dataset
):
    explainer = RegressionPermutationFeatureImportance(
        trained_regressor,
        scoring="r2",
        n_repeats=5,
        random_state=0,
        max_samples_fraction=1.0,
    )
    explanation = explainer.explain(copy.deepcopy(regression_dataset))

    assert explanation["features"] == REGRESSION_INPUT_COLUMNS
    assert len(explanation["importances_mean"]) == len(REGRESSION_INPUT_COLUMNS)
    assert len(explanation["importances_std"]) == len(REGRESSION_INPUT_COLUMNS)
    # PetalLengthCm is highly correlated with PetalWidthCm: its importance
    # must be positive.
    petal_length = explanation["features"].index("PetalLengthCm")
    assert explanation["importances_mean"][petal_length] > 0

    artifacts = explainer.plot(explanation)
    assert len(artifacts) == 1
    assert artifacts[0].type == "plotly"
    assert artifacts[0].title == "Permutation Feature Importance"


@pytest.mark.parametrize(
    "scoring", ["neg_mean_squared_error", "neg_mean_absolute_error"]
)
def test_regression_pfi_other_scorings(trained_regressor, regression_dataset, scoring):
    explainer = RegressionPermutationFeatureImportance(
        trained_regressor, scoring=scoring, n_repeats=3, random_state=0
    )
    explanation = explainer.explain(copy.deepcopy(regression_dataset))
    assert len(explanation["importances_mean"]) == len(REGRESSION_INPUT_COLUMNS)


def test_regression_kernel_shap(trained_regressor, regression_dataset):
    x, _ = regression_dataset

    explainer = RegressionKernelShap(trained_regressor)
    explainer.fit(
        copy.deepcopy(regression_dataset),
        sample_background_data=True,
        background_fraction=0.3,
    )

    instances = x["test"].select(range(3))
    explanation = explainer.explain_instance(instances)

    assert explanation["metadata"]["feature_names"] == REGRESSION_INPUT_COLUMNS
    assert explanation["metadata"]["output_column"] == "PetalWidthCm"

    base_value = explanation["base_value"]
    instance_keys = [
        key for key in explanation if key not in ("metadata", "base_value")
    ]
    assert len(instance_keys) == 3

    for key in instance_keys:
        instance = explanation[key]
        assert len(instance["shap_values"]) == len(REGRESSION_INPUT_COLUMNS)
        # SHAP values are additive: base + contributions ~= prediction.
        reconstructed = base_value + sum(instance["shap_values"])
        assert reconstructed == pytest.approx(instance["model_prediction"], abs=0.05)

    plot = explainer.plot(explanation)
    assert len(plot) == 1
    groups = plot[0].groups
    assert len(groups) == len(instance_keys)
    assert [a.type for a in groups[0].artifacts] == ["plotly"]
    assert "baseline" in explainer.story(explanation, groups[0]).en


def test_regression_partial_dependence(trained_regressor, regression_dataset):
    explainer = RegressionPartialDependence(
        trained_regressor,
        grid_resolution=10,
        lower_percentile=0.05,
        upper_percentile=0.95,
    )
    explanation = explainer.explain(copy.deepcopy(regression_dataset))

    assert explanation["metadata"]["output_column"] == "PetalWidthCm"
    for feature in REGRESSION_INPUT_COLUMNS:
        assert len(explanation[feature]["grid_values"]) == 10
        assert len(explanation[feature]["average"]) == 10
        grid = explanation[feature]["grid_values"]
        assert grid == sorted(grid)

    # PetalLengthCm drives PetalWidthCm: its PDP curve must not be flat.
    petal_curve = explanation["PetalLengthCm"]["average"]
    assert max(petal_curve) - min(petal_curve) > 0.1

    plot = explainer.plot(explanation)
    assert len(plot) == 1
    groups = plot[0].groups
    assert len(groups) == len(REGRESSION_INPUT_COLUMNS)
    assert all(g.artifacts[0].type == "plotly" for g in groups)
    assert groups[0].title in REGRESSION_INPUT_COLUMNS


def test_regression_pdp_invalid_percentiles(trained_regressor):
    with pytest.raises(AssertionError):
        RegressionPartialDependence(
            trained_regressor, lower_percentile=0.9, upper_percentile=0.1
        )


class DummyTextModel:
    """Predicts positive when the text contains the word 'good'.

    Mimics the transformer models' strictness: predict raises if the dataset
    has more than one text column (see ``tokenize_data`` in
    ``base_text_classification_transformer``).
    """

    def predict(self, dataset):
        frame = dataset.to_pandas()
        text_columns = [col for col in frame.columns if col != "label"]
        if len(text_columns) != 1:
            raise ValueError(f"Expected exactly one text column, found: {text_columns}")
        texts = frame[text_columns[0]].tolist()
        return np.array(
            [[0.1, 0.9] if "good" in str(t).split() else [0.9, 0.1] for t in texts]
        )


class _FakeTargetSplit:
    """Minimal stand-in for a DashAIDataset target split."""

    column_names = ["label"]
    types = {"label": Categorical(values=["negative", "positive"])}


def test_token_ablation_fit_reads_target_names():
    explainer = TokenAblation(DummyTextModel())
    explainer.fit((None, {"train": _FakeTargetSplit()}))
    assert explainer.metadata["target_names"] == ["negative", "positive"]


def test_token_ablation_explains_influential_tokens():
    explainer = TokenAblation(DummyTextModel(), max_tokens=20, replacement="remove")
    explainer.metadata = {"target_names": ["negative", "positive"]}

    instances = pd.DataFrame(
        {"text": ["this movie was good indeed", "terrible boring plot"]}
    )
    explanation = explainer.explain_instance(instances)

    first = explanation[0]
    assert first["predicted_class"] == 1
    tokens = first["tokens"]
    importances = first["token_importances"]
    assert len(tokens) == len(importances)

    # Removing 'good' flips the dummy model: it must be the top token.
    good_importance = importances[tokens.index("good")]
    assert good_importance == pytest.approx(0.8, abs=1e-6)
    assert all(importance <= good_importance for importance in importances)

    second = explanation[1]
    assert second["predicted_class"] == 0
    # No single token changes the dummy model's negative prediction.
    assert all(
        importance == pytest.approx(0.0, abs=1e-6)
        for importance in second["token_importances"]
    )

    plot = explainer.plot(explanation)
    assert len(plot) == 1
    groups = plot[0].groups
    assert len(groups) == 2
    assert [a.type for a in groups[0].artifacts] == ["plotly"]
    assert "good" in explainer.story(explanation, groups[0]).en


def test_token_ablation_ignores_tokenizer_columns():
    # The explainer job hands over datasets already prepared by the model;
    # transformer models add input_ids/attention_mask columns. The explainer
    # must rebuild a clean single text-column dataset before predicting.
    explainer = TokenAblation(DummyTextModel(), max_tokens=10)
    explainer.metadata = {"target_names": ["negative", "positive"]}

    instances = pd.DataFrame(
        {
            "text": ["good stuff", "bad stuff"],
            "input_ids": [[101, 102], [101, 103]],
            "attention_mask": [[1, 1], [1, 1]],
        }
    )
    explanation = explainer.explain_instance(instances)

    assert explanation["metadata"]["text_column"] == "text"
    assert explanation[0]["predicted_class"] == 1
    assert explanation[1]["predicted_class"] == 0


def test_token_ablation_unk_replacement():
    explainer = TokenAblation(DummyTextModel(), max_tokens=10, replacement="unk")
    explainer.metadata = {"target_names": ["negative", "positive"]}

    instances = pd.DataFrame({"text": ["good"]})
    explanation = explainer.explain_instance(instances)

    # Single token replaced by [UNK]: prediction flips, importance 0.8.
    assert explanation[0]["token_importances"] == [pytest.approx(0.8, abs=1e-6)]
