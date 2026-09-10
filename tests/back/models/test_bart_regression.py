"""Tests for the pymc-bart backed BART regression model."""

import numpy as np
import pyarrow as pa
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.models.pymc.bart_regression import BARTRegression
from DashAI.back.types.value_types import Float


@pytest.fixture(scope="module", name="regression_dataset")
def fixture_regression_dataset():
    """A small synthetic regression dataset with a strong linear signal."""
    import pandas as pd

    rng = np.random.default_rng(0)
    n = 120
    x0 = rng.uniform(-2, 2, n)
    x1 = rng.uniform(-2, 2, n)
    x2 = rng.uniform(-2, 2, n)
    y = 3.0 * x0 - 2.0 * x1 + 0.5 * x2 + rng.normal(0, 0.2, n)

    feature_df = pd.DataFrame({"x0": x0, "x1": x1, "x2": x2}).astype("float64")
    target_df = pd.DataFrame({"target": y}).astype("float64")

    feature_types = {c: Float(arrow_type=pa.float64()) for c in feature_df.columns}
    target_types = {"target": Float(arrow_type=pa.float64())}

    x = to_dashai_dataset(feature_df, types=feature_types)
    y_ds = to_dashai_dataset(target_df, types=target_types)

    split = 90
    x_train = to_dashai_dataset(feature_df.iloc[:split], types=feature_types)
    x_test = to_dashai_dataset(feature_df.iloc[split:], types=feature_types)
    y_train = to_dashai_dataset(target_df.iloc[:split], types=target_types)

    return {
        "x": x,
        "y": y_ds,
        "x_train": x_train,
        "x_test": x_test,
        "y_train": y_train,
        "y_true_test": y[split:],
    }


@pytest.fixture(scope="module", name="bart_params")
def fixture_bart_params() -> dict:
    # Deliberately small so the MCMC test stays fast.
    return {
        "m": 20,
        "alpha": 0.95,
        "beta": 2.0,
        "response": "constant",
        "draws": 100,
        "tune": 50,
        "chains": 1,
        "random_seed": 0,
    }


def test_bart_get_schema():
    schema = BARTRegression.get_schema()
    assert isinstance(schema, dict)
    assert schema["type"] == "object"
    assert isinstance(schema["properties"], dict)
    for key in ("m", "alpha", "beta", "response", "draws", "tune", "chains"):
        assert key in schema["properties"], f"missing schema field {key}"


def test_bart_train_and_predict(regression_dataset, bart_params):
    model = BARTRegression(**bart_params)
    model.train(regression_dataset["x_train"], regression_dataset["y_train"])

    y_pred = model.predict(regression_dataset["x_test"])

    assert isinstance(y_pred, np.ndarray)
    assert y_pred.shape == (regression_dataset["x_test"].num_rows,)
    assert np.all(np.isfinite(y_pred))

    # The signal is strong, so predictions must track the true targets.
    corr = np.corrcoef(y_pred, regression_dataset["y_true_test"])[0, 1]
    assert corr > 0.8, f"BART predictions poorly correlated with target (corr={corr})"


def test_bart_save_and_load(tmp_path, regression_dataset, bart_params):
    model = BARTRegression(**bart_params)
    model.train(regression_dataset["x_train"], regression_dataset["y_train"])
    y_pred = model.predict(regression_dataset["x_test"])

    model_path = str(tmp_path / "bart_model.joblib")
    model.save(model_path)
    loaded = BARTRegression.load(model_path)
    y_pred_loaded = loaded.predict(regression_dataset["x_test"])

    assert isinstance(y_pred_loaded, np.ndarray)
    np.testing.assert_allclose(y_pred_loaded, y_pred)
