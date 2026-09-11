"""Contract tests for SaveDatasetUnit."""

import pandas as pd
import pyarrow as pa
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import (
    load_dataset,
    to_dashai_dataset,
)
from DashAI.back.job.base_job import JobError
from DashAI.back.types.value_types import Integer
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.save_dataset_unit import SaveDatasetUnit


def _dataset(**columns):
    frame = pd.DataFrame(columns)
    types = {name: Integer(arrow_type=pa.int64()) for name in frame.columns}
    return to_dashai_dataset(frame, types=types)


def test_the_dataset_is_written_where_the_path_says(tmp_path):
    destination = str(tmp_path / "notebook" / "dataset")
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[1, 2], b=[3, 4]))
    ctx.put_ref("dataset_path", destination)

    SaveDatasetUnit()(ctx)

    assert load_dataset(destination).column_names == ["a", "b"]


def test_saving_without_a_dataset_is_a_contract_error(tmp_path):
    ctx = ExecutionContext()
    ctx.put_ref("dataset_path", str(tmp_path / "dataset"))

    with pytest.raises(UnitContractError, match="'dataset' is not available"):
        SaveDatasetUnit()(ctx)


def test_saving_without_a_path_is_a_contract_error():
    """A missing path is a wiring mistake, not a "nowhere to save" decision.

    The unit has no fallback destination on purpose: silently picking one would
    write the dataset somewhere nobody asked for.
    """
    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[1]))

    with pytest.raises(UnitContractError, match="'dataset_path' is not available"):
        SaveDatasetUnit()(ctx)


def test_an_unwritable_destination_becomes_a_job_error(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")

    ctx = ExecutionContext()
    ctx.put("dataset", _dataset(a=[1]))
    ctx.put_ref("dataset_path", str(blocker / "dataset"))

    with pytest.raises(JobError, match="Can not save dataset to path"):
        SaveDatasetUnit()(ctx)
