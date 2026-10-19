import numpy as np
import pandas as pd
import pytest
from kink import di

from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.predict_unit import PredictUnit

SCHEMA = {
    "age": {"type": "Integer", "dtype": "int64"},
    "height": {"type": "Float", "dtype": "float64"},
}


def _rows(ages):
    frame = pd.DataFrame(
        {"age": pd.array(ages, dtype="Int64"), "height": [1.7] * len(ages)}
    )
    return transform_dataset_with_schema(to_dashai_dataset(frame), SCHEMA)


class _Model:
    """Stands in for a trained model; raises `error` if one is given."""

    def __init__(self, error=None):
        self.error = error

    def predict(self, x):
        if self.error is not None:
            raise self.error
        return np.zeros((x.num_rows, 2))


class _Task:
    def process_predictions(self, train_dataset, y_pred_proba, output_column):
        return list(y_pred_proba.argmax(axis=1))


@pytest.fixture(name="registry", autouse=True)
def fixture_registry():
    di["component_registry"] = {"_Task": {"class": _Task}}
    yield
    del di["component_registry"]


def _predict(model, rows):
    ctx = ExecutionContext()
    ctx.put("model_input", rows)
    ctx.put("model", model)
    ctx.put("train_dataset", rows)
    PredictUnit(
        task_name="_Task",
        input_columns=["age", "height"],
        output_columns=["label"],
    )(ctx)
    return ctx.require("y_pred")


def test_a_model_failing_on_missing_values_gets_a_clear_message():
    model = _Model(ValueError("Input X contains NaN."))

    with pytest.raises(ValueError, match="Row 2: age"):
        _predict(model, _rows([30, None]))


def test_a_model_that_accepts_missing_values_still_predicts():
    y_pred = _predict(_Model(), _rows([30, None]))

    assert len(y_pred) == 2


def test_an_unrelated_failure_keeps_its_own_error():
    model = _Model(RuntimeError("out of memory"))

    with pytest.raises(RuntimeError, match="out of memory"):
        _predict(model, _rows([30]))
