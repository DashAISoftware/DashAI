import pandas as pd

from DashAI.back.converters.dataset_columns import (
    rebuild_dataset_with_transformed_columns,
)
from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)


def _dataset(columns, schema):
    return transform_dataset_with_schema(
        to_dashai_dataset(pd.DataFrame(columns)), schema
    )


def test_replaces_scoped_column_in_place_and_keeps_others():
    base = _dataset(
        {"a": [1, 2, 3], "b": [10, 20, 30]},
        {
            "a": {"type": "Integer", "dtype": "int64"},
            "b": {"type": "Integer", "dtype": "int64"},
        },
    )
    transformed = _dataset(
        {"a": [0, 1, 0]},
        {"a": {"type": "Integer", "dtype": "int64"}},
    )

    result = rebuild_dataset_with_transformed_columns(base, transformed, ["a"], [0])

    assert result.column_names == ["a", "b"]
    assert result.to_pandas()["a"].tolist() == [0, 1, 0]
    assert result.to_pandas()["b"].tolist() == [10, 20, 30]


def test_appends_new_columns_not_in_the_scope():
    base = _dataset(
        {"a": [1, 2, 3]},
        {"a": {"type": "Integer", "dtype": "int64"}},
    )
    transformed = _dataset(
        {"a_bin_0": [1, 0, 1], "a_bin_1": [0, 1, 0]},
        {
            "a_bin_0": {"type": "Integer", "dtype": "int64"},
            "a_bin_1": {"type": "Integer", "dtype": "int64"},
        },
    )

    result = rebuild_dataset_with_transformed_columns(base, transformed, ["a"], [0])

    assert result.column_names == ["a_bin_0", "a_bin_1"]
