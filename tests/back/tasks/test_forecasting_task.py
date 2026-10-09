import pandas as pd
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.tasks.forecasting_task import ForecastingTask

DATES = ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]


def _dataset(**columns):
    schema = {
        "date": {"type": "Date", "dtype": "%Y-%m-%d"},
        "other_date": {"type": "Date", "dtype": "%Y-%m-%d"},
        "sales": {"type": "Float", "dtype": "float64"},
        "count": {"type": "Integer", "dtype": "int64"},
        "label": {"type": "Text", "dtype": "string"},
    }
    frame = pd.DataFrame(columns)
    return transform_dataset_with_schema(
        to_dashai_dataset(frame), {name: schema[name] for name in frame.columns}
    )


def test_a_date_input_and_a_float_output_are_accepted():
    dataset = _dataset(date=DATES, sales=[1.0, 2.0, 3.0, 4.0])

    prepared = ForecastingTask().prepare_for_task(dataset, ["date"], ["sales"])

    assert len(prepared) == 4


def test_an_integer_output_is_accepted():
    dataset = _dataset(date=DATES, count=[1, 2, 3, 4])

    prepared = ForecastingTask().prepare_for_task(dataset, ["date"], ["count"])

    assert len(prepared) == 4


def test_a_text_input_is_rejected():
    dataset = _dataset(label=["a", "b", "c", "d"], sales=[1.0, 2.0, 3.0, 4.0])

    with pytest.raises(TypeError):
        ForecastingTask().prepare_for_task(dataset, ["label"], ["sales"])


def test_a_text_output_is_rejected():
    dataset = _dataset(date=DATES, label=["a", "b", "c", "d"])

    with pytest.raises(TypeError):
        ForecastingTask().prepare_for_task(dataset, ["date"], ["label"])


def test_a_second_input_column_is_rejected():
    # Exogenous variables are a separate task by design, so a second input is
    # refused here rather than quietly ignored.
    dataset = _dataset(date=DATES, other_date=DATES, sales=[1.0, 2.0, 3.0, 4.0])

    with pytest.raises(ValueError, match="Input cardinality"):
        ForecastingTask().prepare_for_task(dataset, ["date", "other_date"], ["sales"])


def test_two_output_columns_are_rejected():
    dataset = _dataset(date=DATES, sales=[1.0, 2.0, 3.0, 4.0], count=[1, 2, 3, 4])

    with pytest.raises(ValueError, match="Output cardinality"):
        ForecastingTask().prepare_for_task(dataset, ["date"], ["sales", "count"])


def test_it_reports_no_labels():
    dataset = _dataset(date=DATES, sales=[1.0, 2.0, 3.0, 4.0])

    assert ForecastingTask().num_labels(dataset, "sales") is None


def test_predictions_pass_through_unchanged():
    import numpy as np

    dataset = _dataset(date=DATES, sales=[1.0, 2.0, 3.0, 4.0])
    predictions = np.array([1.5, 2.5])

    processed = ForecastingTask().process_predictions(dataset, predictions, "sales")

    assert list(processed) == [1.5, 2.5]


def test_the_metadata_the_frontend_reads():
    metadata = ForecastingTask.get_metadata()

    assert metadata["inputs_types"] == ["Date"]
    assert set(metadata["outputs_types"]) == {"Float", "Integer"}
    assert metadata["inputs_cardinality"] == 1
    assert metadata["outputs_cardinality"] == 1
