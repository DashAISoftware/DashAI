"""End-to-end regression net for ``ConverterJob``.

Written before the job is decomposed into atomic units, and asserted against the
monolithic implementation, so that the refactor has something to be measured
against. The assertions are deliberately explicit — exact status values, exact
column names on disk, exact error message fragments — instead of the looser
``status in ["finished", "error"]`` style used elsewhere in this suite, which
cannot tell a unit that silently stopped doing part of its work from one that
did it.

Lives under ``tests/back/api`` to reuse the ``client`` and ``dataset_1``
fixtures from this package's ``conftest.py``.
"""

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import ConverterStatus
from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
from DashAI.back.dependencies.database.models import Converter
from DashAI.back.job.base_job import JobError
from DashAI.back.job.converter_job import ConverterJob

IRIS_COLUMNS = [
    "SepalLengthCm",
    "SepalWidthCm",
    "PetalLengthCm",
    "PetalWidthCm",
    "Species",
]
IRIS_ROWS = 150


@pytest.fixture(name="notebook")
def create_notebook(client: TestClient, dataset_1):
    """A notebook holding its own copy of the iris dataset.

    ``POST /notebook/`` copies the dataset folder, so every converter run
    mutates the notebook's copy and never the source dataset.
    """
    response = client.post(
        "/api/v1/notebook/",
        json={"dataset_id": dataset_1.id, "name": "converter job test"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_converter(client, notebook_id, converter_name, scope=None, target=None):
    """Create a Converter row through the API and return its id."""
    response = client.post(
        "/api/v1/converter/",
        json={
            "notebook_id": notebook_id,
            "converter": converter_name,
            "parameters": {
                "order": 0,
                "params": {},
                "scope": scope if scope is not None else {"columns": [], "rows": []},
                "target": target,
            },
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _stored_converter(client, converter_id):
    """Read the Converter row straight from the database."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        converter = db.get(Converter, converter_id)
        return {
            "status": converter.status,
            "start_time": converter.start_time,
            "end_time": converter.end_time,
        }


def _notebook_dataset(notebook):
    return load_dataset(f"{notebook['file_path']}/dataset")


def test_the_notebook_starts_as_an_untouched_copy_of_the_dataset(notebook):
    """Guards the fixture itself: the assertions below mean nothing if the
    notebook copy does not start out as the full iris dataset."""
    dataset = _notebook_dataset(notebook)

    assert dataset.column_names == IRIS_COLUMNS
    assert len(dataset) == IRIS_ROWS


def test_converter_job_removes_the_scoped_column_and_finishes(client, notebook):
    """The happy path, end to end: status transitions and the dataset on disk.

    ``ColumnRemover`` deletes whatever is in scope, so a one-column scope is
    directly observable in the saved dataset.
    """
    converter_id = _create_converter(
        client,
        notebook["id"],
        "ColumnRemover",
        scope={"columns": [{"idx": 2}], "rows": []},
    )

    ConverterJob(converter_id=converter_id).run()

    stored = _stored_converter(client, converter_id)
    assert stored["status"] == ConverterStatus.FINISHED
    assert stored["start_time"] is not None
    assert stored["end_time"] is not None

    dataset = _notebook_dataset(notebook)
    assert dataset.column_names == [
        "SepalLengthCm",
        "PetalLengthCm",
        "PetalWidthCm",
        "Species",
    ]
    assert len(dataset) == IRIS_ROWS


def test_two_converters_chained_see_the_columns_the_previous_one_left(client, notebook):
    """Column scope is resolved by index against the *current* dataset.

    Each converter is its own row and its own job invocation, and the second
    one's ``idx`` must be read against the four columns the first one left
    behind, not against the original five. This is the behaviour any atomic
    decomposition has to keep: nothing may cache the original column list.
    """
    first = _create_converter(
        client,
        notebook["id"],
        "ColumnRemover",
        scope={"columns": [{"idx": 1}], "rows": []},
    )
    ConverterJob(converter_id=first).run()

    assert _notebook_dataset(notebook).column_names == [
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
        "Species",
    ]

    # idx 1 now means SepalWidthCm, not SepalLengthCm.
    second = _create_converter(
        client,
        notebook["id"],
        "ColumnRemover",
        scope={"columns": [{"idx": 1}], "rows": []},
    )
    ConverterJob(converter_id=second).run()

    assert _stored_converter(client, second)["status"] == ConverterStatus.FINISHED
    assert _notebook_dataset(notebook).column_names == [
        "PetalLengthCm",
        "PetalWidthCm",
        "Species",
    ]


def test_a_changes_row_count_converter_replaces_the_whole_dataset(client, notebook):
    """``CHANGES_ROW_COUNT`` takes the transform output as the new dataset.

    ``NanRemover`` returns only the scoped columns, so the columns outside the
    scope are dropped — the documented consequence of replacing the dataset
    instead of merging the transformed columns back in.
    """
    converter_id = _create_converter(
        client,
        notebook["id"],
        "NanRemover",
        scope={"columns": [{"idx": 1}, {"idx": 5}], "rows": []},
    )

    ConverterJob(converter_id=converter_id).run()

    assert _stored_converter(client, converter_id)["status"] == (
        ConverterStatus.FINISHED
    )

    dataset = _notebook_dataset(notebook)
    assert dataset.column_names == ["SepalLengthCm", "Species"]
    # iris has no missing values, so no row is dropped.
    assert len(dataset) == IRIS_ROWS


def test_an_empty_column_scope_means_every_column(client, notebook):
    """An empty scope is not "no columns"; it is "all of them"."""
    converter_id = _create_converter(
        client,
        notebook["id"],
        "NanRemover",
        scope={"columns": [], "rows": []},
    )

    ConverterJob(converter_id=converter_id).run()

    assert _stored_converter(client, converter_id)["status"] == (
        ConverterStatus.FINISHED
    )
    assert _notebook_dataset(notebook).column_names == IRIS_COLUMNS


def test_a_row_scope_fits_on_the_subset_and_transforms_the_whole_dataset(
    client, notebook
):
    """A row scope narrows ``fit`` only; ``transform`` still sees every row."""
    converter_id = _create_converter(
        client,
        notebook["id"],
        "NanRemover",
        scope={"columns": [{"idx": 1}], "rows": [1, 2, 3]},
    )

    ConverterJob(converter_id=converter_id).run()

    assert _stored_converter(client, converter_id)["status"] == (
        ConverterStatus.FINISHED
    )

    dataset = _notebook_dataset(notebook)
    assert dataset.column_names == ["SepalLengthCm"]
    assert len(dataset) == IRIS_ROWS


def test_a_target_column_is_resolved_and_passed_to_the_converter(client, notebook):
    """The supervised path builds y and hands it to fit/transform."""
    converter_id = _create_converter(
        client,
        notebook["id"],
        "NanRemover",
        scope={"columns": [{"idx": 1}], "rows": []},
        target={"idx": 5},
    )

    ConverterJob(converter_id=converter_id).run()

    assert _stored_converter(client, converter_id)["status"] == (
        ConverterStatus.FINISHED
    )
    assert _notebook_dataset(notebook).column_names == ["SepalLengthCm"]


def test_a_missing_converter_row_reports_it_by_id(client, notebook):
    with pytest.raises(JobError, match="Converter with id 999999 not found"):
        ConverterJob(converter_id=999999).run()


def test_an_unknown_converter_name_fails_with_the_wrapped_message(client, notebook):
    """The registry lookup error is reported inside the outer wrapper.

    Both halves matter: the import error names the culprit, the wrapper is what
    the jobs UI actually shows.
    """
    converter_id = _create_converter(
        client, notebook["id"], "ThisConverterDoesNotExist"
    )

    with pytest.raises(JobError) as excinfo:
        ConverterJob(converter_id=converter_id).run()

    message = str(excinfo.value)
    assert "Error applying converters to dataset" in message
    assert "Error importing converter ThisConverterDoesNotExist" in message

    assert _stored_converter(client, converter_id)["status"] == ConverterStatus.ERROR
    # The dataset must be left untouched when the converter never ran.
    assert _notebook_dataset(notebook).column_names == IRIS_COLUMNS


def test_an_out_of_bounds_target_index_reports_cannot_load_dataset(client, notebook):
    """The "out of bounds" text is swallowed; only the wrapper reaches the user.

    The inner JobError is re-caught by the surrounding ``except Exception`` and
    replaced, surviving only as ``__cause__``. Locking this in because it is an
    easy detail to "fix" by accident while refactoring.
    """
    converter_id = _create_converter(
        client,
        notebook["id"],
        "ColumnRemover",
        scope={"columns": [{"idx": 1}], "rows": []},
        target={"idx": 99},
    )

    with pytest.raises(JobError, match="Cannot load dataset from") as excinfo:
        ConverterJob(converter_id=converter_id).run()

    assert "Target column index 99 is out of bounds" in str(excinfo.value.__cause__)

    assert _stored_converter(client, converter_id)["status"] == ConverterStatus.ERROR
    assert _notebook_dataset(notebook).column_names == IRIS_COLUMNS


def test_a_dataset_that_cannot_be_loaded_still_leaves_the_row_in_error(
    client, notebook
):
    """A load failure must not leave the converter stuck in STARTED.

    Nothing else would fix it: the Huey error signal writes only to its own
    ``task_copy`` table and never touches the ``Converter`` row, and the job
    runs with no outer handler. Before this, only ``SQLAlchemyError`` was
    caught here, so an unreadable dataset left the row STARTED forever and the
    UI showed the converter as still running.
    """
    import shutil

    converter_id = _create_converter(client, notebook["id"], "ColumnRemover")
    shutil.rmtree(f"{notebook['file_path']}/dataset")

    with pytest.raises(JobError, match="Can not load dataset from path"):
        ConverterJob(converter_id=converter_id).run()

    assert _stored_converter(client, converter_id)["status"] == ConverterStatus.ERROR


def test_a_failing_converter_leaves_the_dataset_untouched(client, notebook):
    """``ColumnRemover`` raises when asked for a column that is not there.

    Reaching that requires a scope index past the end of the dataset, which is
    exactly what a stale column list would produce in a chained run.
    """
    converter_id = _create_converter(
        client,
        notebook["id"],
        "ColumnRemover",
        scope={"columns": [{"idx": 99}], "rows": []},
    )

    with pytest.raises(JobError, match="Error applying converters to dataset"):
        ConverterJob(converter_id=converter_id).run()

    assert _stored_converter(client, converter_id)["status"] == ConverterStatus.ERROR
    assert _notebook_dataset(notebook).column_names == IRIS_COLUMNS
