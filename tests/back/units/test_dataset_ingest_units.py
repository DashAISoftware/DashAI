"""Contract tests for the units DatasetJob is built from.

The context is built by hand rather than through the job, which is what exposes
composability mistakes: a job always wires the context "correctly", so an
end-to-end run cannot tell a real contract from a lucky one.
"""

import pandas as pd
import pytest
from kink import di

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.job.base_job import JobError
from DashAI.back.units.apply_dataset_schema_unit import ApplyDatasetSchemaUnit
from DashAI.back.units.compute_dataset_metadata_unit import (
    EXTENDED_METADATA_KEYS,
    ComputeDatasetMetadataUnit,
)
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.infer_dataset_types_unit import InferDatasetTypesUnit
from DashAI.back.units.load_datafile_dataset_unit import LoadDatafileDatasetUnit
from DashAI.back.units.load_uploaded_dataset_unit import LoadUploadedDatasetUnit
from DashAI.back.units.save_dataset_to_path_unit import SaveDatasetToPathUnit

SCHEMA = {
    "n": {"type": "Float", "dtype": "float64"},
    "label": {"type": "Categorical", "dtype": "string"},
}


@pytest.fixture(name="dataset")
def fixture_dataset():
    frame = pd.DataFrame({"n": [1.0, 2.0, 3.0], "label": ["a", "b", "a"]})
    return to_dashai_dataset(frame)


@pytest.fixture(name="ctx")
def fixture_ctx(dataset):
    ctx = ExecutionContext()
    ctx.put("dataset", dataset)
    return ctx


# --------------------------------------------------------------------------- #
# ComputeDatasetMetadataUnit
# --------------------------------------------------------------------------- #


def test_metadata_unit_computes_the_extended_keys_by_default(ctx):
    ComputeDatasetMetadataUnit(compute_metadata=True)(ctx)

    splits = ctx.require("dataset").splits
    assert splits["total_rows"] == 3
    for key in EXTENDED_METADATA_KEYS:
        assert key in splits


def test_metadata_unit_strips_extended_keys_it_did_not_ask_for(ctx):
    """A dataset can arrive carrying metadata from wherever it was copied from.

    Asking for base only has to mean base only, whatever the file happened to
    bring — otherwise the result depends on the dataset's history.
    """
    dataset = ctx.require("dataset")
    dataset.splits["correlations"] = {"stale": "value"}
    dataset.splits["general_info"] = {"stale": "value"}

    ComputeDatasetMetadataUnit(compute_metadata=False)(ctx)

    splits = ctx.require("dataset").splits
    assert splits["total_rows"] == 3
    for key in EXTENDED_METADATA_KEYS:
        assert key not in splits


def test_metadata_unit_reuses_trusted_extended_metadata(ctx):
    """Trusting what is there is the whole point of the flag: the marker value
    below survives only because nothing was recomputed."""
    dataset = ctx.require("dataset")
    for key in EXTENDED_METADATA_KEYS:
        dataset.splits[key] = {"marker": key}

    ComputeDatasetMetadataUnit(compute_metadata=True, trust_inherited_metadata=True)(
        ctx
    )

    splits = ctx.require("dataset").splits
    assert splits["correlations"] == {"marker": "correlations"}


def test_metadata_unit_computes_when_there_is_nothing_to_trust(ctx):
    """Trusting metadata that is not there would silently store none at all."""
    ComputeDatasetMetadataUnit(compute_metadata=True, trust_inherited_metadata=True)(
        ctx
    )

    splits = ctx.require("dataset").splits
    assert splits["total_rows"] == 3
    for key in EXTENDED_METADATA_KEYS:
        assert key in splits


def test_metadata_unit_keeps_the_same_dataset_object(ctx):
    """It fills the dataset in place, so downstream units that already hold a
    reference see the metadata too. Asserted with ``is``: an equal copy would
    pass ``==`` and still break that."""
    before = ctx.require("dataset")

    ComputeDatasetMetadataUnit(compute_metadata=False)(ctx)

    assert ctx.require("dataset") is before


def test_metadata_unit_refuses_to_run_without_a_dataset():
    with pytest.raises(UnitContractError):
        ComputeDatasetMetadataUnit(compute_metadata=True)(ExecutionContext())


# --------------------------------------------------------------------------- #
# InferDatasetTypesUnit
# --------------------------------------------------------------------------- #


def test_infer_types_unit_publishes_a_type_per_column(ctx):
    InferDatasetTypesUnit(method="DashAIPtype")(ctx)

    inferred = ctx.require("inferred_types")
    assert set(inferred) == {"n", "label"}


def test_infer_types_unit_prefers_the_types_the_dataset_already_carries(ctx):
    """A reader that got types from the source knows better than inference over
    the values, so those have to win."""
    typed = ApplyDatasetSchemaUnit(column_renames=None)
    ctx.put_ref("inferred_types", SCHEMA)
    typed(ctx)

    InferDatasetTypesUnit(method="DashAIPtype")(ctx)

    inferred = ctx.require("inferred_types")
    assert inferred["label"]["type"] == "Categorical"


def test_infer_types_unit_publishes_something_json_serializable(ctx):
    """It is a ref, not a live object: it has to survive ``put_ref``'s check."""
    InferDatasetTypesUnit(method="DashAIPtype")(ctx)

    # Round-trips through the serializable half without raising.
    assert "inferred_types" in ctx.to_dict()


# --------------------------------------------------------------------------- #
# ApplyDatasetSchemaUnit
# --------------------------------------------------------------------------- #


def test_apply_schema_unit_casts_the_declared_types(ctx):
    ctx.put_ref("inferred_types", SCHEMA)

    ApplyDatasetSchemaUnit(column_renames=None)(ctx)

    types = ctx.require("dataset").types
    assert type(types["label"]).__name__ == "Categorical"


def test_apply_schema_unit_carries_the_types_through_a_rename(ctx):
    """The declared type has to follow the column, not the old name."""
    ctx.put_ref("inferred_types", SCHEMA)

    ApplyDatasetSchemaUnit(column_renames={"label": "variety"})(ctx)

    dataset = ctx.require("dataset")
    assert dataset.column_names == ["n", "variety"]
    assert type(dataset.types["variety"]).__name__ == "Categorical"


def test_apply_schema_unit_rejects_renames_that_collide(ctx):
    ctx.put_ref("inferred_types", SCHEMA)

    with pytest.raises(JobError) as excinfo:
        ApplyDatasetSchemaUnit(column_renames={"label": "n"})(ctx)

    assert "contain duplicates: ['n']" in str(excinfo.value)


def test_apply_schema_unit_rejects_a_declaration_for_columns_that_are_gone(ctx):
    """The underlying transform passes unknown columns through untouched, so a
    stale declaration would silently leave columns with the wrong types. This is
    the check that turns that into an error.
    """
    ctx.put_ref("inferred_types", dict(SCHEMA, removed_column={"type": "Float"}))

    with pytest.raises(JobError) as excinfo:
        ApplyDatasetSchemaUnit(column_renames=None)(ctx)

    assert "removed_column" in str(excinfo.value)


def test_apply_schema_unit_validate_runs_before_any_work(ctx):
    """``validate`` is a precondition check, so it must not need the transform to
    have run — and ``__call__`` runs it on its own."""
    ctx.put_ref("inferred_types", {"not_a_column": {"type": "Float"}})

    with pytest.raises(JobError):
        ApplyDatasetSchemaUnit(column_renames=None).validate(ctx)


def test_apply_schema_unit_refuses_to_run_without_a_declaration(ctx):
    """Declared in REQUIRES, so a missing value is a wiring mistake and has to
    read as one instead of as "no types to apply"."""
    with pytest.raises(UnitContractError):
        ApplyDatasetSchemaUnit(column_renames=None)(ctx)


def test_infer_then_apply_compose_over_the_same_key(ctx):
    """The pair is meant to chain: one publishes what the other consumes."""
    InferDatasetTypesUnit(method="DashAIPtype")(ctx)
    ApplyDatasetSchemaUnit(column_renames={"n": "number"})(ctx)

    assert ctx.require("dataset").column_names == ["number", "label"]


# --------------------------------------------------------------------------- #
# SaveDatasetToPathUnit
# --------------------------------------------------------------------------- #


def test_save_to_path_unit_writes_where_it_is_told(ctx, tmp_path):
    from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

    destination = tmp_path / "somewhere" / "dataset"
    ComputeDatasetMetadataUnit(compute_metadata=False)(ctx)

    SaveDatasetToPathUnit(path=str(destination))(ctx)

    assert load_dataset(str(destination)).column_names == ["n", "label"]


def test_save_to_path_unit_ignores_dataset_path_entirely(ctx, tmp_path):
    """Its whole reason to exist: a context left over from a load must not be
    able to redirect the save back onto the source."""
    from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

    source = tmp_path / "source"
    destination = tmp_path / "destination"
    ctx.put_ref("dataset_path", str(source))
    ComputeDatasetMetadataUnit(compute_metadata=False)(ctx)

    SaveDatasetToPathUnit(path=str(destination))(ctx)

    assert not source.exists()
    assert load_dataset(str(destination)).column_names == ["n", "label"]


def test_save_to_path_unit_keeps_the_underlying_error_text(ctx, tmp_path):
    """A save failure is an infrastructure failure, and only the outermost
    message reaches the user — so the original text has to stay in it."""
    destination = tmp_path / "dataset"

    from DashAI.back.dataloaders.classes import dashai_dataset

    real_save = dashai_dataset.save_dataset

    def fail(dataset, path):
        raise OSError("no space left on device")

    dashai_dataset.save_dataset = fail
    try:
        with pytest.raises(JobError) as excinfo:
            SaveDatasetToPathUnit(path=str(destination))(ctx)
    finally:
        dashai_dataset.save_dataset = real_save

    message = str(excinfo.value)
    assert str(destination) in message
    assert "no space left on device" in message


# --------------------------------------------------------------------------- #
# the loading units
# --------------------------------------------------------------------------- #


@pytest.fixture(name="csv_file")
def fixture_csv_file(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("n,label\n1.0,a\n2.0,b\n", encoding="utf-8")
    return path


@pytest.fixture(name="registry")
def fixture_registry():
    """A registry holding only the CSV reader, injected without an app."""
    from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
    from DashAI.back.dependencies.registry import ComponentRegistry

    registry = ComponentRegistry(initial_components=[CSVDataLoader])
    di["component_registry"] = registry
    yield registry
    del di["component_registry"]


def test_uploaded_unit_reads_the_file_and_publishes_the_dataset(
    registry, csv_file, tmp_path
):
    ctx = ExecutionContext()

    LoadUploadedDatasetUnit(
        dataloader={"component": "CSVDataLoader", "params": {"separator": ","}},
        source=str(csv_file),
        temp_path=str(tmp_path),
        n_sample=None,
    )(ctx)

    assert ctx.require("dataset").column_names == ["n", "label"]


def test_uploaded_unit_publishes_no_path_and_no_id(registry, csv_file, tmp_path):
    """An uploaded file is not a stored dataset yet: there is no id to correlate
    against and nowhere it belongs on disk. Publishing either would hand a later
    unit a value that describes something else."""
    ctx = ExecutionContext()

    LoadUploadedDatasetUnit(
        dataloader={"component": "CSVDataLoader", "params": {"separator": ","}},
        source=str(csv_file),
        temp_path=str(tmp_path),
        n_sample=None,
    )(ctx)

    assert not ctx.has("dataset_path")
    assert not ctx.has("dataset_id")


def test_uploaded_unit_reports_an_unknown_reader_with_the_registry_wording(
    registry, csv_file, tmp_path
):
    ctx = ExecutionContext()

    with pytest.raises(KeyError) as excinfo:
        LoadUploadedDatasetUnit(
            dataloader={"component": "NoSuchLoader", "params": {}},
            source=str(csv_file),
            temp_path=str(tmp_path),
            n_sample=None,
        )(ctx)

    assert "does not exists in the registry" in str(excinfo.value)


class _DatafileRow:
    def __init__(self, local_path, status):
        self.local_path = local_path
        self.status = status


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows

    def get(self, model, row_id):
        return self._rows.get(row_id)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class _FakeSessionFactory:
    """A class, not a lambda: kink calls any registered lambda with the container
    to resolve it, so a lambda would be invoked as a service factory instead of
    handed to the unit as one."""

    def __init__(self, rows):
        self._rows = rows

    def __call__(self):
        return _FakeSession(self._rows)


@pytest.fixture(name="datafile_rows")
def fixture_datafile_rows():
    rows = {}
    di["session_factory"] = _FakeSessionFactory(rows)
    yield rows
    del di["session_factory"]


def test_datafile_unit_reads_the_selected_file(
    registry, datafile_rows, csv_file, tmp_path
):
    from DashAI.back.core.enums.status import DatafileStatus

    datafile_rows[7] = _DatafileRow(str(tmp_path), DatafileStatus.READY)
    ctx = ExecutionContext()

    LoadDatafileDatasetUnit(
        dataloader={"component": "CSVDataLoader", "params": {"separator": ","}},
        datafile_id=7,
        selected_file="data.csv",
    )(ctx)

    assert ctx.require("dataset").column_names == ["n", "label"]


def test_datafile_unit_skips_dotted_paths_when_choosing(
    registry, datafile_rows, csv_file, tmp_path
):
    """Download tools leave metadata directories behind that sort before the real
    data, so without the filter the wrong file would win."""
    from DashAI.back.core.enums.status import DatafileStatus

    hidden = tmp_path / ".cache"
    hidden.mkdir()
    (hidden / "aaa.csv").write_text("junk\n", encoding="utf-8")
    datafile_rows[7] = _DatafileRow(str(tmp_path), DatafileStatus.READY)
    ctx = ExecutionContext()

    LoadDatafileDatasetUnit(
        dataloader={"component": "CSVDataLoader", "params": {"separator": ","}},
        datafile_id=7,
        selected_file=None,
    )(ctx)

    assert ctx.require("dataset").column_names == ["n", "label"]


def test_datafile_unit_rejects_a_download_that_is_not_finished(
    registry, datafile_rows, tmp_path
):
    from DashAI.back.core.enums.status import DatafileStatus

    datafile_rows[7] = _DatafileRow(str(tmp_path), DatafileStatus.DOWNLOADING)

    with pytest.raises(JobError) as excinfo:
        LoadDatafileDatasetUnit(
            dataloader={"component": "CSVDataLoader", "params": {}},
            datafile_id=7,
            selected_file=None,
        )(ExecutionContext())

    assert str(excinfo.value) == "Datafile 7 is not ready."


def test_datafile_unit_treats_a_missing_row_the_same_way(registry, datafile_rows):
    with pytest.raises(JobError) as excinfo:
        LoadDatafileDatasetUnit(
            dataloader={"component": "CSVDataLoader", "params": {}},
            datafile_id=99,
            selected_file=None,
        )(ExecutionContext())

    assert str(excinfo.value) == "Datafile 99 is not ready."


def test_datafile_unit_reports_an_empty_download(registry, datafile_rows, tmp_path):
    from DashAI.back.core.enums.status import DatafileStatus

    empty = tmp_path / "empty"
    empty.mkdir()
    datafile_rows[7] = _DatafileRow(str(empty), DatafileStatus.READY)

    with pytest.raises(JobError) as excinfo:
        LoadDatafileDatasetUnit(
            dataloader={"component": "CSVDataLoader", "params": {}},
            datafile_id=7,
            selected_file=None,
        )(ExecutionContext())

    assert str(excinfo.value) == "Hub download directory is empty."


def test_datafile_unit_has_its_own_wording_for_an_unknown_reader(
    registry, datafile_rows, csv_file, tmp_path
):
    """Deliberately different from the uploaded unit's, which surfaces the
    registry's own ``KeyError``. Both texts reach users today."""
    from DashAI.back.core.enums.status import DatafileStatus

    datafile_rows[7] = _DatafileRow(str(tmp_path), DatafileStatus.READY)

    with pytest.raises(JobError) as excinfo:
        LoadDatafileDatasetUnit(
            dataloader={"component": "NoSuchLoader", "params": {}},
            datafile_id=7,
            selected_file="data.csv",
        )(ExecutionContext())

    assert str(excinfo.value) == "DataLoader 'NoSuchLoader' not found in registry."


def test_datafile_unit_rejects_a_component_that_is_not_a_reader(
    datafile_rows, csv_file, tmp_path
):
    """A registered component of some other kind is still not a reader.

    The registry's ``registry[name]`` indexer searches every type at once, so
    looking the name up that way would find, say, a metric and call it as if it
    could parse a file. The lookup is deliberately scoped to the readers.
    """
    from DashAI.back.core.enums.status import DatafileStatus
    from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
    from DashAI.back.dependencies.registry import ComponentRegistry
    from DashAI.back.metrics.classification.accuracy import Accuracy

    di["component_registry"] = ComponentRegistry(
        initial_components=[CSVDataLoader, Accuracy]
    )
    datafile_rows[7] = _DatafileRow(str(tmp_path), DatafileStatus.READY)
    try:
        with pytest.raises(JobError) as excinfo:
            LoadDatafileDatasetUnit(
                dataloader={"component": "Accuracy", "params": {}},
                datafile_id=7,
                selected_file="data.csv",
            )(ExecutionContext())
    finally:
        del di["component_registry"]

    assert str(excinfo.value) == "DataLoader 'Accuracy' not found in registry."
