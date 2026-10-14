"""Contract tests for LoadDatasetUnit, isolated from any orchestrating job.

The context is built by hand rather than through a job, which is what exposes
composability mistakes: a job always wires the context "correctly", so an
end-to-end run cannot tell a real contract from a lucky one.
"""

import pytest
from kink import di

from DashAI.back.dataloaders.classes.dashai_dataset import (
    save_dataset,
    to_dashai_dataset,
)
from DashAI.back.job.base_job import JobError
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.load_dataset_unit import LoadDatasetUnit


class _Row:
    """Stand-in for a Dataset or Notebook ORM row."""

    def __init__(self, file_path=None, dataset_id=None):
        self.file_path = file_path
        self.dataset_id = dataset_id


class _FakeSession:
    """Session that answers ``get`` from a table -> {id: row} mapping."""

    def __init__(self, rows):
        self._rows = rows

    def get(self, model, row_id):
        return self._rows.get(model.__name__, {}).get(row_id)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class _FakeSessionFactory:
    """Stand-in for a ``sessionmaker``.

    A class rather than a lambda on purpose: kink invokes any registered lambda
    with the container to resolve it, so a lambda here would be called as a
    service factory instead of being handed to the unit as one.
    """

    def __init__(self, rows):
        self._rows = rows

    def __call__(self):
        return _FakeSession(self._rows)


@pytest.fixture(name="stored_dataset")
def fixture_stored_dataset(tmp_path):
    """A real two-column dataset written to ``<tmp>/store/dataset``."""
    import pandas as pd
    import pyarrow as pa

    from DashAI.back.types.value_types import Integer

    frame = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    types = {
        "a": Integer(arrow_type=pa.int64()),
        "b": Integer(arrow_type=pa.int64()),
    }
    root = tmp_path / "store"
    save_dataset(to_dashai_dataset(frame, types=types), str(root / "dataset"))
    return root


@pytest.fixture(name="fake_db")
def fixture_fake_db(stored_dataset):
    """Point both a Dataset row and a Notebook row at the stored dataset."""
    rows = {
        "Dataset": {7: _Row(file_path=str(stored_dataset))},
        "Notebook": {3: _Row(file_path=str(stored_dataset), dataset_id=7)},
    }
    di["session_factory"] = _FakeSessionFactory(rows)
    yield rows
    del di["session_factory"]


def test_loading_by_dataset_id_publishes_the_whole_contract(fake_db):
    ctx = ExecutionContext()

    LoadDatasetUnit(dataset_id=7)(ctx)

    assert ctx.require("dataset").column_names == ["a", "b"]
    assert ctx.require("dataset_id") == 7
    assert ctx.require("dataset_path").endswith("dataset")


def test_loading_by_notebook_id_resolves_the_source_dataset_id(fake_db):
    """The notebook branch must still publish a dataset id.

    Downstream error messages identify the work by dataset id, so a notebook
    load that left the key unset would report ``None`` instead of the dataset.
    """
    ctx = ExecutionContext()

    LoadDatasetUnit(notebook_id=3)(ctx)

    assert ctx.require("dataset").column_names == ["a", "b"]
    assert ctx.require("dataset_id") == 7


def test_the_two_starting_points_are_mutually_exclusive(fake_db):
    with pytest.raises(JobError, match="exactly one of dataset_id or notebook_id"):
        LoadDatasetUnit(dataset_id=7, notebook_id=3)(ExecutionContext())


def test_no_starting_point_at_all_is_rejected(fake_db):
    with pytest.raises(JobError, match="exactly one of dataset_id or notebook_id"):
        LoadDatasetUnit()(ExecutionContext())


def test_a_missing_dataset_row_is_reported_by_id(fake_db):
    with pytest.raises(JobError, match="Dataset 99 does not exist in DB."):
        LoadDatasetUnit(dataset_id=99)(ExecutionContext())


def test_a_missing_notebook_row_is_reported_by_id(fake_db):
    with pytest.raises(JobError, match="Notebook 99 does not exist in DB."):
        LoadDatasetUnit(notebook_id=99)(ExecutionContext())


def test_an_unreadable_path_becomes_a_job_error(fake_db, tmp_path):
    fake_db["Notebook"][4] = _Row(file_path=str(tmp_path / "nowhere"), dataset_id=7)

    with pytest.raises(JobError, match="Can not load dataset from path"):
        LoadDatasetUnit(notebook_id=4)(ExecutionContext())


def test_the_dataset_is_cached_live_not_copied(fake_db):
    """The dataset must come back as the same object, not a copy.

    ``ctx.get`` deep-copies the refs half and returns the cache half by
    reference; a dataset that came back copied would mean every unit downstream
    transformed a different object than the one that gets saved.
    """
    ctx = ExecutionContext()

    LoadDatasetUnit(dataset_id=7)(ctx)

    assert ctx.require("dataset") is ctx.require("dataset")
