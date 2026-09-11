"""End-to-end regression net for ``DatasetJob``.

Written before the job is decomposed into atomic units, and asserted against the
monolithic implementation, so the refactor has something to be measured against.
The assertions are deliberately explicit — exact status values, exact row/column
counts, exact keys in ``splits.json``, exact error message text — instead of the
looser ``status in ["finished", "error"]`` style used elsewhere in this suite,
which cannot tell a unit that silently stopped doing part of its work from one
that did it.

``DatasetJob`` has the widest blast radius of any job in the repo: it is the
bootstrap fixture of half the suite (``tests/back/api/conftest.py``,
``tests/back/models/conftest.py``, ``tests/back/api/test_predict_api.py``,
``tests/back/types/load_preview_test.py``). Everything here has to keep passing
through every slice of the refactor.

Lives under ``tests/back/api`` to reuse the ``client`` and ``dataset_1``
fixtures from this package's ``conftest.py``.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Optional

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import DatafileStatus, DatasetStatus
from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
from DashAI.back.dependencies.database.models import Datafile, Dataset
from DashAI.back.job.base_job import JobError
from DashAI.back.job.dataset_job import DatasetJob

IRIS_COLUMNS = [
    "SepalLengthCm",
    "SepalWidthCm",
    "PetalLengthCm",
    "PetalWidthCm",
    "Species",
]
IRIS_ROWS = 150

IRIS_SCHEMA = {
    "SepalLengthCm": {"type": "Float", "dtype": "float64"},
    "SepalWidthCm": {"type": "Float", "dtype": "float64"},
    "PetalLengthCm": {"type": "Float", "dtype": "float64"},
    "PetalWidthCm": {"type": "Float", "dtype": "float64"},
    "Species": {"type": "Categorical", "dtype": "string"},
}

#: The extended EDA keys ``compute_metadata=False`` has to leave out.
EXTENDED_KEYS = (
    "general_info",
    "numeric_stats",
    "categorical_stats",
    "text_stats",
    "quality_info",
    "correlations",
)

IRIS_CSV = Path(__file__).parent / "iris.csv"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _session_factory(client):
    return client.app.container["session_factory"]


def _new_dataset_row(client, name: str) -> int:
    """Create a ``Dataset`` row in DELIVERED, the state the job expects."""
    with _session_factory(client)() as db:
        entry = Dataset(name=name, file_path="")
        entry.set_status_as_delivered()
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry.id


def _stored(client, dataset_id: int) -> Optional[dict]:
    """Read the ``Dataset`` row straight from the database.

    No ``start_time`` / ``end_time``: unlike ``Run`` or ``Explorer``, this table
    declares no such columns. The status setters used to assign them anyway,
    which only set attributes that were dropped at commit.
    """
    with _session_factory(client)() as db:
        row = db.get(Dataset, dataset_id)
        if row is None:
            return None
        return {
            "status": row.status,
            "file_path": row.file_path,
            "total_rows": row.total_rows,
            "total_columns": row.total_columns,
            "last_modified": row.last_modified,
        }


def _run_job(client, dataset_id: int, params: dict, **extra) -> None:
    """Run ``DatasetJob`` synchronously, the way every fixture in the suite does."""
    kwargs = {
        "dataset_id": dataset_id,
        "url": "",
        "params": params,
        "file_path": IRIS_CSV,
        **extra,
    }
    DatasetJob(job_type="DatasetJob", kwargs=kwargs).run()


def _csv_params(name: str, **overrides) -> dict:
    params = {
        "dataloader": "CSVDataLoader",
        "separator": ",",
        "name": name,
        "schema": IRIS_SCHEMA,
    }
    params.update(overrides)
    return params


def _splits(file_path: str) -> dict:
    with open(Path(file_path) / "dataset" / "splits.json", encoding="utf-8") as f:
        return json.load(f)


def _cleanup(client, dataset_id: int) -> None:
    row = _stored(client, dataset_id)
    if row and row["file_path"]:
        shutil.rmtree(row["file_path"], ignore_errors=True)


# --------------------------------------------------------------------------- #
# status bookkeeping
# --------------------------------------------------------------------------- #


class TestTheRowIsNeverLeftStuckInStarted:
    """Whatever goes wrong, the row must not stay in STARTED.

    Nothing else moves it: Huey's ``SIGNAL_ERROR`` writes to its own
    ``task_copy`` table and never to the ``Dataset`` row
    (``huey_job_queue.py:201-211``), so an exception the job's own handler does
    not see leaves the dataset advertised as in-progress forever and the UI
    spinning on work that already died.

    Both cases below used to escape — the handler only caught ``JobError``, and
    the final database block only caught ``SQLAlchemyError``. They are the
    reason the handler now catches ``Exception``.
    """

    def test_a_mkdir_failure_that_is_not_file_exists_still_marks_the_row(
        self, client, monkeypatch
    ):
        """Creating the destination folder can fail with more than
        ``FileExistsError``: no permission, no space, a path the filesystem
        rejects. The status was already committed as STARTED by then."""
        dataset_id = _new_dataset_row(client, "stuck_on_mkdir")

        def deny(self, *args, **kwargs):
            raise PermissionError("cannot create the dataset folder")

        monkeypatch.setattr(Path, "mkdir", deny)

        with pytest.raises(PermissionError):
            _run_job(client, dataset_id, _csv_params("stuck_on_mkdir"))

        assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR

    def test_a_row_deleted_mid_run_is_reported_instead_of_crashing(self, client):
        """The row is deletable through the API while the job runs, so the final
        block can find it gone. It used to assign to ``None`` and raise
        ``AttributeError`` from inside a block that only caught database errors.
        """
        dataset_id = _new_dataset_row(client, "stuck_on_deleted_row")
        datasets_dir = _datasets_dir(client)
        before = _folders_in(datasets_dir)

        from DashAI.back.dataloaders.classes import dashai_dataset

        real_save = dashai_dataset.save_dataset

        def save_then_delete(dataset, path):
            real_save(dataset, path)
            with _session_factory(client)() as db:
                db.delete(db.get(Dataset, dataset_id))
                db.commit()

        dashai_dataset.save_dataset = save_then_delete
        try:
            with pytest.raises(JobError) as excinfo:
                _run_job(client, dataset_id, _csv_params("stuck_on_deleted_row"))
        finally:
            dashai_dataset.save_dataset = real_save

        assert str(excinfo.value) == (f"Dataset with ID {dataset_id} no longer exists.")
        # The row is gone, so there is no status to write — but the data written
        # to disk has to go with it instead of being orphaned.
        assert _stored(client, dataset_id) is None
        assert _folders_in(datasets_dir) == before

    def test_a_non_database_failure_in_the_final_block_still_marks_the_row(
        self, client
    ):
        """The mirror of the case above for a row that does still exist: the
        block catches ``SQLAlchemyError`` by name, so anything else has to be
        handled further out rather than escaping."""
        dataset_id = _new_dataset_row(client, "stuck_on_final_block")
        datasets_dir = _datasets_dir(client)
        before = _folders_in(datasets_dir)

        real_set_finished = Dataset.set_status_as_finished

        def boom(self):
            raise RuntimeError("not a database error")

        Dataset.set_status_as_finished = boom
        try:
            with pytest.raises(RuntimeError):
                _run_job(client, dataset_id, _csv_params("stuck_on_final_block"))
        finally:
            Dataset.set_status_as_finished = real_set_finished

        assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR
        assert _folders_in(datasets_dir) == before


# --------------------------------------------------------------------------- #
# file / URL branch — the happy path
# --------------------------------------------------------------------------- #


def test_the_file_branch_finishes_and_writes_every_column_of_the_row(client):
    """Status transitions, the row's columns, and the dataset on disk."""
    dataset_id = _new_dataset_row(client, "net_file_happy")
    before = _stored(client, dataset_id)
    assert before["status"] == DatasetStatus.DELIVERED

    _run_job(client, dataset_id, _csv_params("net_file_happy"))

    row = _stored(client, dataset_id)
    assert row["status"] == DatasetStatus.FINISHED
    assert row["total_rows"] == IRIS_ROWS
    assert row["total_columns"] == len(IRIS_COLUMNS)
    assert row["last_modified"] > before["last_modified"]

    # The path is a realpath under DATASETS_PATH, and the dataset is really there.
    datasets_path = client.app.container["config"]["DATASETS_PATH"]
    assert Path(row["file_path"]).parent == Path(os.path.realpath(datasets_path))

    dataset = load_dataset(f"{row['file_path']}/dataset")
    assert dataset.column_names == IRIS_COLUMNS
    assert len(dataset) == IRIS_ROWS

    _cleanup(client, dataset_id)


def test_the_declared_schema_lands_on_the_stored_types(client):
    """``transform_dataset_with_schema`` is what makes Species categorical."""
    dataset_id = _new_dataset_row(client, "net_file_types")

    _run_job(client, dataset_id, _csv_params("net_file_types"))

    row = _stored(client, dataset_id)
    dataset = load_dataset(f"{row['file_path']}/dataset")
    types = dataset.types

    assert type(types["Species"]).__name__ == "Categorical"
    for column in IRIS_COLUMNS[:4]:
        assert type(types[column]).__name__ == "Float"

    _cleanup(client, dataset_id)


def test_inferred_types_in_the_params_win_over_inference(client):
    """``params["inferred_types"]`` is the first branch of the schema cascade."""
    dataset_id = _new_dataset_row(client, "net_file_inferred")
    # Species declared as plain text instead of categorical: only an honoured
    # override can produce this.
    override = dict(IRIS_SCHEMA, Species={"type": "Text", "dtype": "string"})

    _run_job(
        client,
        dataset_id,
        _csv_params("net_file_inferred", inferred_types=override),
    )

    row = _stored(client, dataset_id)
    types = load_dataset(f"{row['file_path']}/dataset").types
    assert type(types["Species"]).__name__ != "Categorical"

    _cleanup(client, dataset_id)


def test_the_schema_is_inferred_when_the_params_declare_nothing(client):
    """Third branch of the cascade: ``infer_types(..., "DashAIPtype")``."""
    dataset_id = _new_dataset_row(client, "net_file_no_schema")

    _run_job(
        client,
        dataset_id,
        {"dataloader": "CSVDataLoader", "separator": ",", "name": "net_file_no_schema"},
    )

    row = _stored(client, dataset_id)
    assert row["status"] == DatasetStatus.FINISHED
    dataset = load_dataset(f"{row['file_path']}/dataset")
    assert dataset.column_names == IRIS_COLUMNS
    # Inference ran and produced a type for every column.
    assert set(dataset.types) == set(IRIS_COLUMNS)

    _cleanup(client, dataset_id)


def test_column_renames_rewrite_the_columns_and_remap_the_schema(client):
    """The rename remaps ``schema`` too (lines 291-297), so the renamed column
    keeps the type its old name declared."""
    dataset_id = _new_dataset_row(client, "net_file_renames")

    _run_job(
        client,
        dataset_id,
        _csv_params(
            "net_file_renames",
            inferred_types=IRIS_SCHEMA,
            column_renames={"Species": "Variety", "SepalLengthCm": "SepalLength"},
        ),
    )

    row = _stored(client, dataset_id)
    dataset = load_dataset(f"{row['file_path']}/dataset")

    assert dataset.column_names == [
        "SepalLength",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
        "Variety",
    ]
    # The type followed the rename rather than being re-inferred.
    assert type(dataset.types["Variety"]).__name__ == "Categorical"
    assert row["total_columns"] == len(IRIS_COLUMNS)

    _cleanup(client, dataset_id)


# --------------------------------------------------------------------------- #
# metadata policy
# --------------------------------------------------------------------------- #


def test_compute_metadata_true_writes_base_and_extended_metadata(client):
    dataset_id = _new_dataset_row(client, "net_meta_full")

    _run_job(client, dataset_id, _csv_params("net_meta_full", compute_metadata=True))

    splits = _splits(_stored(client, dataset_id)["file_path"])
    assert splits["total_rows"] == IRIS_ROWS
    assert splits["column_names"] == IRIS_COLUMNS
    assert "nan" in splits
    for key in EXTENDED_KEYS:
        assert key in splits, f"missing {key} when compute_metadata=True"

    _cleanup(client, dataset_id)


def test_compute_metadata_false_writes_base_metadata_only(client):
    dataset_id = _new_dataset_row(client, "net_meta_base")

    _run_job(client, dataset_id, _csv_params("net_meta_base", compute_metadata=False))

    row = _stored(client, dataset_id)
    splits = _splits(row["file_path"])
    assert splits["total_rows"] == IRIS_ROWS
    assert splits["column_names"] == IRIS_COLUMNS
    assert "nan" in splits
    for key in EXTENDED_KEYS:
        assert key not in splits, f"unexpected {key} when compute_metadata=False"

    # The row's columns come from splits, so they must survive the base-only path.
    assert row["total_rows"] == IRIS_ROWS
    assert row["total_columns"] == len(IRIS_COLUMNS)

    _cleanup(client, dataset_id)


def test_omitting_the_flag_defaults_to_full_metadata(client):
    """Backward compatibility: the 4 bootstrap fixtures never pass the flag."""
    dataset_id = _new_dataset_row(client, "net_meta_default")

    _run_job(client, dataset_id, _csv_params("net_meta_default"))

    splits = _splits(_stored(client, dataset_id)["file_path"])
    for key in EXTENDED_KEYS:
        assert key in splits

    _cleanup(client, dataset_id)


# --------------------------------------------------------------------------- #
# notebook branch
# --------------------------------------------------------------------------- #


@pytest.fixture(name="notebook")
def create_notebook(client: TestClient, dataset_1):
    """A notebook holding its own copy of the iris dataset.

    ``POST /notebook/`` copies the dataset folder, so the notebook branch of the
    job reads a private working copy and never the source dataset.
    """
    response = client.post(
        "/api/v1/notebook/",
        json={"dataset_id": dataset_1.id, "name": "dataset job net"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _add_converter(client, notebook_id: int) -> int:
    """Register a converter against the notebook.

    The job only asks *whether any Converter row exists* for the notebook
    (lines 174-180); it never runs it. So a row is enough to flip
    ``from_notebook_no_converters`` to False.
    """
    response = client.post(
        "/api/v1/converter/",
        json={
            "notebook_id": notebook_id,
            "converter": "StandardScaler",
            "parameters": {
                "order": 0,
                "params": {},
                "scope": {"columns": [], "rows": []},
                "target": None,
            },
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_the_notebook_branch_copies_the_working_copy_into_a_new_dataset(
    client, notebook
):
    dataset_id = _new_dataset_row(client, "net_notebook_happy")

    _run_job(
        client,
        dataset_id,
        {"name": "net_notebook_happy"},
        notebook_id=notebook["id"],
        file_path=None,
    )

    row = _stored(client, dataset_id)
    assert row["status"] == DatasetStatus.FINISHED
    assert row["total_rows"] == IRIS_ROWS
    assert row["total_columns"] == len(IRIS_COLUMNS)

    # A new folder, not the notebook's own copy.
    assert Path(row["file_path"]) != Path(notebook["file_path"])
    dataset = load_dataset(f"{row['file_path']}/dataset")
    assert dataset.column_names == IRIS_COLUMNS
    assert len(dataset) == IRIS_ROWS

    # And the notebook is untouched.
    assert load_dataset(f"{notebook['file_path']}/dataset").column_names == IRIS_COLUMNS

    _cleanup(client, dataset_id)


def test_a_notebook_without_converters_reuses_the_source_metadata(client, notebook):
    """No converters means the bytes match the source, so ``splits.json`` is
    inherited rather than recomputed (lines 313-328)."""
    dataset_id = _new_dataset_row(client, "net_notebook_inherit")

    _run_job(
        client,
        dataset_id,
        {"name": "net_notebook_inherit", "compute_metadata": True},
        notebook_id=notebook["id"],
        file_path=None,
    )

    splits = _splits(_stored(client, dataset_id)["file_path"])
    # dataset_1 was built with the default (full metadata), so the inherited
    # splits already carry the extended keys.
    for key in EXTENDED_KEYS:
        assert key in splits
    assert splits["total_rows"] == IRIS_ROWS

    _cleanup(client, dataset_id)


def test_a_notebook_without_converters_still_drops_extended_when_asked(
    client, notebook
):
    """``compute_metadata=False`` purges the extended keys the source carried."""
    dataset_id = _new_dataset_row(client, "net_notebook_purge")

    _run_job(
        client,
        dataset_id,
        {"name": "net_notebook_purge", "compute_metadata": False},
        notebook_id=notebook["id"],
        file_path=None,
    )

    splits = _splits(_stored(client, dataset_id)["file_path"])
    assert splits["total_rows"] == IRIS_ROWS
    for key in EXTENDED_KEYS:
        assert key not in splits, f"inherited {key} was not purged"

    _cleanup(client, dataset_id)


def test_a_notebook_with_converters_recomputes_the_metadata(client, notebook):
    """One Converter row is enough to stop trusting the source's splits."""
    _add_converter(client, notebook["id"])
    dataset_id = _new_dataset_row(client, "net_notebook_recompute")

    _run_job(
        client,
        dataset_id,
        {"name": "net_notebook_recompute", "compute_metadata": True},
        notebook_id=notebook["id"],
        file_path=None,
    )

    splits = _splits(_stored(client, dataset_id)["file_path"])
    for key in EXTENDED_KEYS:
        assert key in splits
    assert splits["total_rows"] == IRIS_ROWS

    _cleanup(client, dataset_id)


def test_the_notebook_branch_never_applies_a_schema_or_renames(client, notebook):
    """Lines 260-299 sit in the ``else`` of the notebook check, so neither
    ``inferred_types`` nor ``column_renames`` has any effect here."""
    dataset_id = _new_dataset_row(client, "net_notebook_no_schema")

    _run_job(
        client,
        dataset_id,
        {
            "name": "net_notebook_no_schema",
            "column_renames": {"Species": "ShouldBeIgnored"},
        },
        notebook_id=notebook["id"],
        file_path=None,
    )

    row = _stored(client, dataset_id)
    dataset = load_dataset(f"{row['file_path']}/dataset")
    assert dataset.column_names == IRIS_COLUMNS

    _cleanup(client, dataset_id)


# --------------------------------------------------------------------------- #
# hub branch
# --------------------------------------------------------------------------- #


@pytest.fixture(name="datafile")
def create_datafile(client, tmp_path_factory, request):
    """A READY ``Datafile`` row pointing at a directory holding iris.csv.

    Built by hand: the hub branch only reads the row and the files on disk, so
    no network is involved. ``dataset_id`` carries the test name because the
    table has a ``UNIQUE(source_name, dataset_id)`` constraint and each test
    gets its own row.
    """
    work_dir = tmp_path_factory.mktemp("hub_download")
    shutil.copy(IRIS_CSV, work_dir / "iris.csv")

    with _session_factory(client)() as db:
        row = Datafile(
            source_name="HuggingFaceDatasetSource",
            dataset_id=f"net/iris/{request.node.name}",
            name="net iris",
            local_path=str(work_dir),
            status=DatafileStatus.READY,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {"id": row.id, "local_path": str(work_dir)}


def _hub_params(name: str, datafile_id: int, **overrides) -> dict:
    params = {
        "name": name,
        "dataloader": "CSVDataLoader",
        "dataloader_params": {"separator": ","},
        "datafile_id": datafile_id,
    }
    params.update(overrides)
    return params


def _run_hub_job(client, dataset_id: int, params: dict) -> None:
    DatasetJob(
        job_type="DatasetJob",
        kwargs={
            "dataset_id": dataset_id,
            "source_name": "HuggingFaceDatasetSource",
            "dataset_source_id": "net/iris",
            "params": params,
        },
    ).run()


def test_the_hub_branch_finishes_from_an_explicit_selected_file(client, datafile):
    dataset_id = _new_dataset_row(client, "net_hub_selected")

    _run_hub_job(
        client,
        dataset_id,
        _hub_params("net_hub_selected", datafile["id"], selected_file="iris.csv"),
    )

    row = _stored(client, dataset_id)
    assert row["status"] == DatasetStatus.FINISHED
    assert row["total_rows"] == IRIS_ROWS
    assert row["total_columns"] == len(IRIS_COLUMNS)
    assert load_dataset(f"{row['file_path']}/dataset").column_names == IRIS_COLUMNS

    _cleanup(client, dataset_id)


def test_the_hub_branch_picks_the_first_file_when_none_is_selected(client, datafile):
    """No ``selected_file``: the first entry of a sorted ``rglob`` wins."""
    dataset_id = _new_dataset_row(client, "net_hub_first")

    _run_hub_job(client, dataset_id, _hub_params("net_hub_first", datafile["id"]))

    row = _stored(client, dataset_id)
    assert row["status"] == DatasetStatus.FINISHED
    assert row["total_rows"] == IRIS_ROWS

    _cleanup(client, dataset_id)


def test_the_hub_branch_ignores_dotted_files_when_picking(client, datafile):
    """Any path component starting with a dot is skipped (lines 213-217).

    ``.hidden`` sorts before ``iris.csv``, so without the filter it would win
    and the job would fail on an unreadable file.
    """
    hidden = Path(datafile["local_path"]) / ".hidden"
    hidden.mkdir()
    (hidden / "junk.csv").write_text("not,a,dataset\n", encoding="utf-8")

    dataset_id = _new_dataset_row(client, "net_hub_hidden")

    _run_hub_job(client, dataset_id, _hub_params("net_hub_hidden", datafile["id"]))

    row = _stored(client, dataset_id)
    assert row["status"] == DatasetStatus.FINISHED
    assert row["total_rows"] == IRIS_ROWS

    _cleanup(client, dataset_id)


def test_the_hub_branch_applies_the_schema_and_the_renames(client, datafile):
    """Unlike the notebook branch, hub imports do go through lines 260-299."""
    dataset_id = _new_dataset_row(client, "net_hub_renames")

    _run_hub_job(
        client,
        dataset_id,
        _hub_params(
            "net_hub_renames",
            datafile["id"],
            selected_file="iris.csv",
            inferred_types=IRIS_SCHEMA,
            column_renames={"Species": "Variety"},
        ),
    )

    row = _stored(client, dataset_id)
    dataset = load_dataset(f"{row['file_path']}/dataset")
    assert dataset.column_names[-1] == "Variety"
    assert type(dataset.types["Variety"]).__name__ == "Categorical"

    _cleanup(client, dataset_id)


# --------------------------------------------------------------------------- #
# error messages, by exact text
# --------------------------------------------------------------------------- #
#
# These travel verbatim to ``task_copy.error_msg`` (``huey_job_queue.py:210``
# stores ``str(exc)``) and from there to ``GET /job/status/{id}`` and the UI, so
# the text *is* the contract. Everything raised inside the try at line 153 comes
# back wrapped as ``Error loading dataset: <message>``.


def _datasets_dir(client) -> Path:
    return Path(client.app.container["config"]["DATASETS_PATH"])


def _folders_in(path: Path) -> set:
    return {p.name for p in path.iterdir() if p.is_dir()}


def test_a_missing_dataset_row_is_reported_by_id(client):
    """Raised before the status is touched, so nothing is left behind."""
    with pytest.raises(JobError) as excinfo:
        _run_job(client, 987654, _csv_params("net_missing_row"))

    assert str(excinfo.value) == "Dataset with ID 987654 not found."


def test_a_file_exists_collision_names_the_generated_folder(client, monkeypatch):
    dataset_id = _new_dataset_row(client, "net_collision")

    def collide(self, *args, **kwargs):
        raise FileExistsError(self)

    monkeypatch.setattr(Path, "mkdir", collide)

    with pytest.raises(JobError) as excinfo:
        _run_job(client, dataset_id, _csv_params("net_collision"))

    message = str(excinfo.value)
    assert message.startswith("A dataset with the name ")
    assert message.endswith(" already exists.")
    assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR


def test_a_missing_notebook_is_reported_with_the_original_wording(client):
    """The wording says "has no associated dataset" even though what is missing
    is the Notebook row itself. Preserved verbatim: it reaches the UI."""
    dataset_id = _new_dataset_row(client, "net_missing_notebook")

    with pytest.raises(JobError) as excinfo:
        _run_job(
            client,
            dataset_id,
            {"name": "net_missing_notebook"},
            notebook_id=987654,
            file_path=None,
        )

    assert str(excinfo.value) == (
        "Error loading dataset: Notebook with ID 987654 has no associated dataset."
    )
    assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR


def test_an_unreadable_notebook_copy_names_the_path_it_could_not_read(client, notebook):
    """The notebook branch reads a stored dataset off disk. When that read fails
    the message names the path instead of quoting the reader's exception.

    This is the one intentional wording change of the refactor: the branch now
    goes through the same loading step as every other flow that materialises a
    stored dataset, and that step reports failures by path. The path is the
    actionable part — the reader's own text ("the arrow file is truncated") says
    nothing about *which* file.
    """
    dataset_id = _new_dataset_row(client, "net_unreadable_notebook")

    from DashAI.back.dataloaders.classes import dashai_dataset

    real_load = dashai_dataset.load_dataset

    def fail_to_load(path):
        raise OSError("the arrow file is truncated")

    dashai_dataset.load_dataset = fail_to_load
    try:
        with pytest.raises(JobError) as excinfo:
            _run_job(
                client,
                dataset_id,
                {"name": "net_unreadable_notebook"},
                notebook_id=notebook["id"],
                file_path=None,
            )
    finally:
        dashai_dataset.load_dataset = real_load

    assert str(excinfo.value) == (
        f"Error loading dataset: Can not load dataset from path {notebook['file_path']}"
    )
    assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR


def test_an_unknown_dataloader_in_the_file_branch_reports_the_registry_key_error(
    client,
):
    """The file branch uses ``component_registry[name]``, whose ``KeyError``
    stringifies *with* the quotes."""
    dataset_id = _new_dataset_row(client, "net_bad_loader_file")

    with pytest.raises(JobError) as excinfo:
        _run_job(
            client,
            dataset_id,
            _csv_params("net_bad_loader_file", dataloader="NoSuchDataLoader"),
        )

    assert str(excinfo.value) == (
        "Error loading dataset: \"Component 'NoSuchDataLoader' does not exists "
        'in the registry."'
    )
    assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR


def test_an_unknown_dataloader_in_the_hub_branch_has_its_own_wording(client, datafile):
    """The hub branch looks the loader up itself, with a different message than
    the file branch. Both have to survive the refactor."""
    dataset_id = _new_dataset_row(client, "net_bad_loader_hub")

    with pytest.raises(JobError) as excinfo:
        _run_hub_job(
            client,
            dataset_id,
            _hub_params(
                "net_bad_loader_hub", datafile["id"], dataloader="NoSuchDataLoader"
            ),
        )

    assert str(excinfo.value) == (
        "Error loading dataset: DataLoader 'NoSuchDataLoader' not found in registry."
    )
    assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR


def test_a_hub_import_without_a_datafile_id_says_so(client):
    dataset_id = _new_dataset_row(client, "net_hub_no_id")

    with pytest.raises(JobError) as excinfo:
        _run_hub_job(
            client,
            dataset_id,
            {"name": "net_hub_no_id", "dataloader": "CSVDataLoader"},
        )

    assert str(excinfo.value) == (
        "Error loading dataset: datafile_id is required for hub imports."
    )
    assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR


def test_a_datafile_that_is_not_ready_is_reported_by_id(client, datafile):
    dataset_id = _new_dataset_row(client, "net_hub_not_ready")
    with _session_factory(client)() as db:
        row = db.get(Datafile, datafile["id"])
        row.status = DatafileStatus.DOWNLOADING
        db.commit()

    with pytest.raises(JobError) as excinfo:
        _run_hub_job(
            client, dataset_id, _hub_params("net_hub_not_ready", datafile["id"])
        )

    assert str(excinfo.value) == (
        f"Error loading dataset: Datafile {datafile['id']} is not ready."
    )
    assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR


def test_a_missing_datafile_row_is_also_reported_as_not_ready(client):
    """``hub_row is None`` and ``status != READY`` share one branch and one
    message, so a nonexistent id reads as "not ready"."""
    dataset_id = _new_dataset_row(client, "net_hub_missing_row")

    with pytest.raises(JobError) as excinfo:
        _run_hub_job(client, dataset_id, _hub_params("net_hub_missing_row", 987654))

    assert str(excinfo.value) == "Error loading dataset: Datafile 987654 is not ready."


def test_an_empty_hub_download_directory_says_so(client, tmp_path_factory):
    dataset_id = _new_dataset_row(client, "net_hub_empty")
    empty_dir = tmp_path_factory.mktemp("hub_empty")
    with _session_factory(client)() as db:
        row = Datafile(
            source_name="HuggingFaceDatasetSource",
            dataset_id="net/iris/empty",
            name="empty",
            local_path=str(empty_dir),
            status=DatafileStatus.READY,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        datafile_id = row.id

    with pytest.raises(JobError) as excinfo:
        _run_hub_job(client, dataset_id, _hub_params("net_hub_empty", datafile_id))

    assert str(excinfo.value) == (
        "Error loading dataset: Hub download directory is empty."
    )
    assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR


def test_column_renames_that_collide_list_the_duplicates_sorted(client):
    dataset_id = _new_dataset_row(client, "net_dup_renames")

    with pytest.raises(JobError) as excinfo:
        _run_job(
            client,
            dataset_id,
            _csv_params(
                "net_dup_renames",
                inferred_types=IRIS_SCHEMA,
                column_renames={
                    "SepalWidthCm": "Same",
                    "PetalWidthCm": "Same",
                    "Species": "SepalLengthCm",
                },
            ),
        )

    assert str(excinfo.value) == (
        "Error loading dataset: Invalid column_renames: resulting column names "
        "contain duplicates: ['Same', 'SepalLengthCm']"
    )
    assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR


def test_a_database_error_on_the_final_commit_is_reported_generically(client):
    """The last block (lines 351-368) catches only ``SQLAlchemyError`` and
    replaces it with a fixed message, dropping the database's own text.

    Note the asymmetry with everything above: this one is raised *outside* the
    try at line 153, so it is not prefixed with "Error loading dataset: ".
    """
    from sqlalchemy import exc as sa_exc

    dataset_id = _new_dataset_row(client, "net_db_error")
    datasets_dir = _datasets_dir(client)
    before = _folders_in(datasets_dir)

    real_set_finished = Dataset.set_status_as_finished

    def boom(self):
        raise sa_exc.InvalidRequestError("the database said no")

    Dataset.set_status_as_finished = boom
    try:
        with pytest.raises(JobError) as excinfo:
            _run_job(client, dataset_id, _csv_params("net_db_error"))
    finally:
        Dataset.set_status_as_finished = real_set_finished

    assert str(excinfo.value) == "Internal database error"
    assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR
    # This branch cleans up the folder too.
    assert _folders_in(datasets_dir) == before


# --------------------------------------------------------------------------- #
# side effects of a failure
# --------------------------------------------------------------------------- #


def test_a_failure_after_the_folder_was_created_removes_it(client):
    """The generated folder is created before loading, and the ``except`` at
    line 345 has to clean it up — otherwise every failed import leaks a folder
    under DATASETS_PATH."""
    dataset_id = _new_dataset_row(client, "net_leak_check")
    datasets_dir = _datasets_dir(client)
    before = _folders_in(datasets_dir)

    with pytest.raises(JobError):
        _run_job(
            client,
            dataset_id,
            _csv_params("net_leak_check", dataloader="NoSuchDataLoader"),
        )

    assert _folders_in(datasets_dir) == before
    assert _stored(client, dataset_id)["file_path"] == ""


def test_a_failure_does_not_delete_a_folder_the_job_did_not_create(client, tmp_path):
    """Re-importing into an existing dataset reuses that dataset's own folder
    instead of creating one (the ``n_sample`` branch).

    The cleanup on failure removes the destination folder, which is right when
    the job created it and destructive when it did not: the row survives the
    failure pointing at a path whose contents would be gone.
    """
    existing = tmp_path / "already_stored"
    existing.mkdir()
    (existing / "dataset").mkdir()
    (existing / "dataset" / "data.arrow").write_text("payload", encoding="utf-8")

    with _session_factory(client)() as db:
        entry = Dataset(name="net_reused_folder", file_path=str(existing))
        entry.set_status_as_delivered()
        db.add(entry)
        db.commit()
        db.refresh(entry)
        dataset_id = entry.id

    with pytest.raises(JobError):
        _run_job(
            client,
            dataset_id,
            _csv_params("net_reused_folder", dataloader="NoSuchDataLoader"),
            n_sample=10,
        )

    assert (existing / "dataset" / "data.arrow").read_text(
        encoding="utf-8"
    ) == "payload"
    assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR


def test_the_temp_dir_is_removed_even_on_the_happy_path(client, tmp_path_factory):
    """The ``finally`` removes ``temp_dir`` whether the job worked or not."""
    dataset_id = _new_dataset_row(client, "net_temp_happy")
    temp_dir = tmp_path_factory.mktemp("net_temp_happy")

    _run_job(client, dataset_id, _csv_params("net_temp_happy"), temp_dir=str(temp_dir))

    assert not temp_dir.exists()
    assert _stored(client, dataset_id)["status"] == DatasetStatus.FINISHED

    _cleanup(client, dataset_id)


def test_the_temp_dir_is_removed_after_a_failure(client, tmp_path_factory):
    dataset_id = _new_dataset_row(client, "net_temp_failure")
    temp_dir = tmp_path_factory.mktemp("net_temp_failure")

    with pytest.raises(JobError):
        _run_job(
            client,
            dataset_id,
            _csv_params("net_temp_failure", dataloader="NoSuchDataLoader"),
            temp_dir=str(temp_dir),
        )

    assert not temp_dir.exists()


def test_a_failed_notebook_import_leaves_the_notebook_intact(client, notebook):
    """The cleanup ``rmtree`` targets the *generated* folder. If it ever pointed
    at the loaded path instead, this is what would catch it: the notebook's own
    working copy would be gone."""
    dataset_id = _new_dataset_row(client, "net_notebook_failure")
    notebook_dataset = Path(notebook["file_path"]) / "dataset"
    assert notebook_dataset.exists()

    from DashAI.back.dataloaders.classes import dashai_dataset

    real_save = dashai_dataset.save_dataset

    def fail_to_save(dataset, path):
        raise OSError("disk full")

    dashai_dataset.save_dataset = fail_to_save
    try:
        with pytest.raises(JobError) as excinfo:
            _run_job(
                client,
                dataset_id,
                {"name": "net_notebook_failure"},
                notebook_id=notebook["id"],
                file_path=None,
            )
    finally:
        dashai_dataset.save_dataset = real_save

    # The message gained the destination path, and deliberately kept the
    # original exception's text: a save failure is an infrastructure failure and
    # only the outermost message reaches the user (``huey_job_queue.py:210``
    # stores ``str(exc)``, never the ``__cause__`` chain), so swallowing it would
    # drop the diagnosis exactly when it matters.
    message = str(excinfo.value)
    assert message.startswith("Error loading dataset: Can not save dataset to path ")
    assert message.endswith(": disk full")

    assert notebook_dataset.exists()
    assert load_dataset(str(notebook_dataset)).column_names == IRIS_COLUMNS
    assert _stored(client, dataset_id)["status"] == DatasetStatus.ERROR
