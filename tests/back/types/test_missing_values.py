import pandas as pd

from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.types.missing_values import (
    missing_columns_by_row,
    missing_values_message,
)

SCHEMA = {
    "age": {"type": "Integer", "dtype": "int64"},
    "city": {"type": "Categorical", "dtype": "string"},
    "note": {"type": "Text", "dtype": "string"},
}


def _dataset():
    frame = pd.DataFrame(
        {
            "age": pd.array([30, None, 41, 25], dtype="Int64"),
            "city": ["a", "b", "N/A", "c"],
            "note": ["ok", "fine", "x", "."],
        }
    )
    return transform_dataset_with_schema(to_dashai_dataset(frame), SCHEMA)


def test_missing_values_include_nulls_and_null_like_strings():
    missing = missing_columns_by_row(_dataset(), ["age", "city", "note"])

    assert missing == {1: ["age"], 2: ["city"], 3: ["note"]}


def test_message_names_rows_one_based_and_columns():
    message = missing_values_message(_dataset(), ["age", "city"])

    assert message == (
        "The model cannot predict rows with missing values. Row 2: age. Row 3: city."
    )


def test_no_message_without_missing_values():
    complete = _dataset().select([0])
    assert missing_values_message(complete, ["age", "city", "note"]) is None
