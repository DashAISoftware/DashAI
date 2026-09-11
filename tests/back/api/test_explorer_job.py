"""End-to-end regression net for ``ExplorerJob``.

Written before the job is decomposed into atomic units, and asserted against the
monolithic implementation, so that the refactor has something to be measured
against. The assertions are deliberately explicit — exact status values, exact
files on disk, exact error message fragments — instead of the looser
``status in ["finished", "error"]`` style used elsewhere in this suite, which
cannot tell a unit that silently stopped doing part of its work from one that
did it.

``ExplorerJob`` had no tests at all before this file.

Tests named ``test_currently_*`` pin behaviour that is known to be wrong. They
exist so the refactor can be proven behaviour-preserving first; the fix lands
afterwards as its own change, which flips the assertion and renames the test.

Lives under ``tests/back/api`` to reuse the ``client`` and ``dataset_1``
fixtures from this package's ``conftest.py``.
"""

import pathlib
import shutil

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import ExplorerStatus
from DashAI.back.dependencies.database.models import Explorer
from DashAI.back.job.base_job import JobError
from DashAI.back.job.explorer_job import ExplorerJob

#: ``DescribeExplorer.__init__`` reads these three keys unconditionally, and the
#: schema declares no defaults, so a valid configuration always carries all of
#: them.
DESCRIBE_PARAMETERS = {"percentiles": "25, 50, 75", "include": "all", "exclude": None}

SEPAL_LENGTH = [{"columnName": "SepalLengthCm"}]


@pytest.fixture(name="notebook")
def create_notebook(client: TestClient, dataset_1):
    """A notebook holding its own copy of the iris dataset.

    ``POST /notebook/`` copies the dataset folder, so an exploration always
    reads the notebook's copy and never the source dataset.
    """
    response = client.post(
        "/api/v1/notebook/",
        json={"dataset_id": dataset_1.id, "name": "explorer job test"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_explorer(client, notebook_id, columns=None, parameters=None):
    """Create an Explorer row through the API, which validates it."""
    response = client.post(
        "/api/v1/explorer/",
        json={
            "notebook_id": notebook_id,
            "exploration_type": "DescribeExplorer",
            "columns": columns if columns is not None else SEPAL_LENGTH,
            "parameters": (
                parameters if parameters is not None else DESCRIBE_PARAMETERS
            ),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _insert_explorer_row(client, **fields):
    """Insert an Explorer row straight into the database.

    ``POST /explorer/`` validates the exploration type, the parameters and the
    columns, so the branches of ``run()`` that react to an invalid row can only
    be reached by writing the row directly.
    """
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        explorer = Explorer(**fields)
        db.add(explorer)
        db.commit()
        db.refresh(explorer)
        return explorer.id


def _stored_explorer(client, explorer_id):
    """Read the Explorer row straight from the database."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        explorer = db.get(Explorer, explorer_id)
        return {
            "status": explorer.status,
            "exploration_path": explorer.exploration_path,
            "start_time": explorer.start_time,
            "end_time": explorer.end_time,
        }


def _notebook_folder(client, notebook_id):
    return pathlib.Path(client.app.container["config"]["NOTEBOOK_PATH"]) / str(
        notebook_id
    )


def test_the_notebook_starts_as_a_readable_copy_of_the_dataset(client, notebook):
    """Guards the fixture itself: the assertions below mean nothing if the
    notebook copy is not a loadable iris dataset."""
    from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

    dataset = load_dataset(f"{notebook['file_path']}/dataset")

    assert "SepalLengthCm" in dataset.column_names
    assert len(dataset) == 150


def test_explorer_job_writes_the_result_and_finishes(client, notebook):
    """The happy path, end to end: status transitions and the file on disk.

    ``DescribeExplorer`` writes ``{explorer_id}.json`` under the notebook's own
    folder, and the row records that exact path.
    """
    explorer_id = _create_explorer(client, notebook["id"])

    ExplorerJob(explorer_id=explorer_id).run()

    stored = _stored_explorer(client, explorer_id)
    assert stored["status"] == ExplorerStatus.FINISHED
    assert stored["start_time"] is not None
    assert stored["end_time"] is not None

    expected = _notebook_folder(client, notebook["id"]) / f"{explorer_id}.json"
    assert expected.exists()
    assert stored["exploration_path"] == expected.as_posix()


def test_two_explorations_on_one_notebook_keep_separate_files(client, notebook):
    """The save path is keyed by explorer id, so runs never overwrite each
    other's result. Any decomposition has to keep that key."""
    first = _create_explorer(client, notebook["id"])
    second = _create_explorer(
        client, notebook["id"], columns=[{"columnName": "PetalWidthCm"}]
    )

    ExplorerJob(explorer_id=first).run()
    ExplorerJob(explorer_id=second).run()

    first_path = _stored_explorer(client, first)["exploration_path"]
    second_path = _stored_explorer(client, second)["exploration_path"]

    assert first_path != second_path
    assert pathlib.Path(first_path).exists()
    assert pathlib.Path(second_path).exists()


def test_a_missing_explorer_row_reports_it_by_id(client):
    with pytest.raises(JobError, match="Explorer with id 999999 not found."):
        ExplorerJob(explorer_id=999999).run()


def test_a_missing_notebook_leaves_the_row_in_error(client, notebook):
    """A notebook that is gone must not leave the exploration stuck in STARTED.

    The "not found" error used to be raised inside a ``try`` whose only handler
    was ``except exc.SQLAlchemyError``, so ``set_status_as_error`` never ran and
    the UI showed the exploration as still running. Nothing else would have
    fixed it: the Huey error signal writes only to its own ``task_copy`` table
    and never touches the ``Explorer`` row, and ``_execute_base_job`` calls
    ``job.run()`` with no handler at all.

    The message still has to be the specific one, not a generic wrapper.
    """
    explorer_id = _create_explorer(client, notebook["id"])

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        explorer = db.get(Explorer, explorer_id)
        explorer.notebook_id = 999999
        db.commit()

    with pytest.raises(JobError, match="Notebook with id 999999 not found."):
        ExplorerJob(explorer_id=explorer_id).run()

    assert _stored_explorer(client, explorer_id)["status"] == ExplorerStatus.ERROR


def test_a_dataset_that_cannot_be_loaded_leaves_the_row_in_error(client, notebook):
    """A load failure must not leave the explorer stuck in STARTED."""
    explorer_id = _create_explorer(client, notebook["id"])
    shutil.rmtree(f"{notebook['file_path']}/dataset")

    with pytest.raises(JobError, match="Can not load dataset from path"):
        ExplorerJob(explorer_id=explorer_id).run()

    assert _stored_explorer(client, explorer_id)["status"] == ExplorerStatus.ERROR


def test_an_unknown_exploration_type_reports_it_and_errors(client, notebook):
    """The registry lookup error names the culprit and reaches the user intact.

    Unlike ``ConverterJob``, nothing wraps this message on the way out.
    """
    explorer_id = _insert_explorer_row(
        client,
        notebook_id=notebook["id"],
        exploration_type="ThisExplorerDoesNotExist",
        columns=SEPAL_LENGTH,
        parameters={},
    )

    with pytest.raises(
        JobError,
        match="Explorer ThisExplorerDoesNotExist not found in the registry.",
    ):
        ExplorerJob(explorer_id=explorer_id).run()

    assert _stored_explorer(client, explorer_id)["status"] == ExplorerStatus.ERROR


def test_parameters_the_explorer_cannot_accept_report_an_instancing_error(
    client, notebook
):
    """``DescribeExplorer.__init__`` reads its three keys unconditionally."""
    explorer_id = _insert_explorer_row(
        client,
        notebook_id=notebook["id"],
        exploration_type="DescribeExplorer",
        columns=SEPAL_LENGTH,
        parameters={},
    )

    with pytest.raises(
        JobError, match="Error instancing the explorer DescribeExplorer."
    ):
        ExplorerJob(explorer_id=explorer_id).run()

    assert _stored_explorer(client, explorer_id)["status"] == ExplorerStatus.ERROR


def test_a_column_absent_from_the_dataset_reports_a_preparation_error(client, notebook):
    """``prepare_dataset`` selects the requested columns and fails loudly.

    The column list is resolved against the dataset the job just loaded, which
    is the behaviour any decomposition has to keep: nothing may resolve these
    names ahead of time against a different dataset.
    """
    explorer_id = _insert_explorer_row(
        client,
        notebook_id=notebook["id"],
        exploration_type="DescribeExplorer",
        columns=[{"columnName": "ThisColumnDoesNotExist"}],
        parameters=DESCRIBE_PARAMETERS,
    )

    with pytest.raises(
        JobError,
        match="Error preparing the dataset for the exploration DescribeExplorer.",
    ):
        ExplorerJob(explorer_id=explorer_id).run()

    assert _stored_explorer(client, explorer_id)["status"] == ExplorerStatus.ERROR


def test_set_status_as_delivered_marks_the_row(client, notebook):
    """The enqueue path marks the row before the worker ever picks it up."""
    explorer_id = _create_explorer(client, notebook["id"])

    ExplorerJob(explorer_id=explorer_id).set_status_as_delivered()

    stored = _stored_explorer(client, explorer_id)
    assert stored["status"] == ExplorerStatus.DELIVERED


def test_set_status_as_delivered_reports_a_missing_row(client):
    with pytest.raises(JobError, match="Explorer with id 999999 not found."):
        ExplorerJob(explorer_id=999999).set_status_as_delivered()
