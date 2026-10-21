"""Missing cells in hand-typed or exported-model rows reach the preprocessor.

A session can impute missing values, so rejecting a null while validating the
input would refuse exactly the rows its imputer exists to fix. Rows read from a
CSV with pandas carry NaN for an empty cell, typed rows may carry None.
"""

import math

import pandas as pd
import pyarrow as pa
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import (
    save_dataset,
    to_dashai_dataset,
)
from DashAI.back.tasks.tabular_classification_task import TabularClassificationTask
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Integer


@pytest.fixture(name="schema_path")
def fixture_schema_path(tmp_path):
    frame = pd.DataFrame({"count": [1, 2], "color": ["red", "blue"]})
    types = {
        "count": Integer(arrow_type=pa.int64()),
        "color": Categorical(values=["red", "blue"]),
    }
    path = tmp_path / "dataset"
    save_dataset(to_dashai_dataset(frame, types=types), str(path))
    return str(path)


@pytest.mark.parametrize("missing", [None, math.nan], ids=["none", "nan"])
def test_a_missing_cell_is_kept_as_null_instead_of_rejected(schema_path, missing):
    rows = [{"count": missing, "color": missing}, {"count": 3, "color": "red"}]

    dataset = TabularClassificationTask().process_manual_input(rows, schema_path)

    table = dataset.arrow_table
    assert table.column("count").to_pylist()[0] is None
    assert table.column("color").to_pylist()[0] is None
    assert table.column("count").to_pylist()[1] == 3
