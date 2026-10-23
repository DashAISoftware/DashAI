import os
from datetime import datetime, timedelta

import pyarrow as pa
import pytest
from fastapi.testclient import TestClient

from DashAI.back.converters.base_converter import BaseConverterSchema
from DashAI.back.converters.document_converter import DocumentConverter
from DashAI.back.core.enums.status import ConverterStatus
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.dataloaders.classes.dashai_document import load_document
from DashAI.back.dependencies.database.models import Converter, Notebook
from DashAI.back.job.base_job import JobError
from DashAI.back.job.converter_job import ConverterJob
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Text
from tests.back.document_fixtures import create_document_notebook, image, text

START = datetime(2026, 1, 1)
UNDERSCORES = {"char_to_replace": "_", "replacement_char": " "}


def add_converter(client, notebook_id, name, params, columns, offset=0):
    """Insert a converter row scoped to document items and return its id."""
    with client.app.container["session_factory"]() as db:
        converter = Converter(
            notebook_id=notebook_id,
            converter=name,
            parameters={
                "order": 1,
                "params": params,
                "scope": {
                    "columns": [
                        {"idx": index + 1, **column}
                        for index, column in enumerate(columns)
                    ],
                    "rows": [],
                },
                "target": None,
            },
            created=START + timedelta(seconds=offset),
        )
        db.add(converter)
        db.commit()
        db.refresh(converter)
        return converter.id


def working_document(client, notebook_id):
    """Load the notebook's working copy of its document."""
    with client.app.container["session_factory"]() as db:
        notebook = db.get(Notebook, notebook_id)
        return load_document(os.path.join(notebook.file_path, "document"))


def converter_status(client, converter_id):
    """Read a converter's status."""
    with client.app.container["session_factory"]() as db:
        return db.get(Converter, converter_id).status


def test_the_character_replacer_rewrites_document_text(client: TestClient):
    notebook_id = create_document_notebook(
        client, "job_replace", ["a_b", image(), "c_d"]
    )
    converter_id = add_converter(
        client,
        notebook_id,
        "CharacterReplacer",
        UNDERSCORES,
        [{"columnName": "Text"}],
    )

    ConverterJob(converter_id=converter_id).run()

    document = working_document(client, notebook_id)
    assert document[Text] == ["a b", "c d"]
    assert len(document[DashAIImage]) == 1
    assert converter_status(client, converter_id) == ConverterStatus.FINISHED


def test_only_the_selected_kinds_are_rewritten(client: TestClient):
    notebook_id = create_document_notebook(
        client,
        "job_kinds",
        [text("A_title", kind="title"), "a_b", text("x_y", kind="code")],
    )
    converter_id = add_converter(
        client,
        notebook_id,
        "CharacterReplacer",
        UNDERSCORES,
        [{"columnName": "Text", "kinds": ["paragraph", "title"]}],
    )

    ConverterJob(converter_id=converter_id).run()

    assert working_document(client, notebook_id)[Text] == ["A title", "a b", "x_y"]


def test_a_refused_output_marks_the_converter_as_error(client: TestClient):
    notebook_id = create_document_notebook(client, "job_refused", ["a", image()])
    converter_id = add_converter(
        client,
        notebook_id,
        "CharacterReplacer",
        UNDERSCORES,
        [{"columnName": "Text", "kinds": ["code"]}],
    )

    with pytest.raises(JobError, match="code"):
        ConverterJob(converter_id=converter_id).run()

    assert converter_status(client, converter_id) == ConverterStatus.ERROR
    assert working_document(client, notebook_id)[Text] == ["a"]


def test_the_job_name_uses_the_document_name(client: TestClient):
    notebook_id = create_document_notebook(client, "job_named", ["a"])
    converter_id = add_converter(
        client, notebook_id, "CharacterReplacer", UNDERSCORES, [{"columnName": "Text"}]
    )
    assert (
        ConverterJob(converter_id=converter_id).get_job_name()
        == "CharacterReplacer: job_named"
    )


def test_deleting_the_only_converter_restores_the_original_document(
    client: TestClient,
):
    notebook_id = create_document_notebook(client, "delete_only", ["a_b"])
    converter_id = add_converter(
        client, notebook_id, "CharacterReplacer", UNDERSCORES, [{"columnName": "Text"}]
    )
    ConverterJob(converter_id=converter_id).run()
    assert working_document(client, notebook_id)[Text] == ["a b"]

    response = client.delete(f"/api/v1/converter/{converter_id}")

    assert response.status_code == 200, response.text
    assert response.json() == {"jobId": None}
    assert working_document(client, notebook_id)[Text] == ["a_b"]


def test_deleting_a_later_converter_replays_the_earlier_one(client: TestClient):
    notebook_id = create_document_notebook(client, "delete_replay", ["a_b_c"])
    first = add_converter(
        client,
        notebook_id,
        "CharacterReplacer",
        UNDERSCORES,
        [{"columnName": "Text"}],
        offset=0,
    )
    ConverterJob(converter_id=first).run()
    second = add_converter(
        client,
        notebook_id,
        "CharacterReplacer",
        {"char_to_replace": " ", "replacement_char": "+"},
        [{"columnName": "Text"}],
        offset=1,
    )
    ConverterJob(converter_id=second).run()
    assert working_document(client, notebook_id)[Text] == ["a+b+c"]

    response = client.delete(f"/api/v1/converter/{second}")

    assert response.status_code == 200, response.text
    assert working_document(client, notebook_id)[Text] == ["a b c"]


def test_replayed_converters_are_delivered_before_they_run(client, monkeypatch):
    notebook_id = create_document_notebook(client, "delete_status", ["a_b"])
    first = add_converter(
        client,
        notebook_id,
        "CharacterReplacer",
        UNDERSCORES,
        [{"columnName": "Text"}],
        offset=0,
    )
    ConverterJob(converter_id=first).run()
    second = add_converter(
        client,
        notebook_id,
        "CharacterReplacer",
        UNDERSCORES,
        [{"columnName": "Text"}],
        offset=1,
    )
    ConverterJob(converter_id=second).run()

    job_queue = client.app.container["job_queue"]
    put = job_queue.put
    statuses = []

    def recording_put(job):
        statuses.append(converter_status(client, job.kwargs["converter_id"]))
        return put(job)

    monkeypatch.setattr(job_queue, "put", recording_put)

    response = client.delete(f"/api/v1/converter/{second}")

    assert response.status_code == 200, response.text
    assert statuses == [ConverterStatus.DELIVERED]
    assert converter_status(client, first) == ConverterStatus.FINISHED


def test_only_the_picked_items_are_rewritten(client: TestClient):
    notebook_id = create_document_notebook(
        client, "job_positions", ["a_1", "a_2", image(), "a_3"]
    )
    converter_id = add_converter(
        client,
        notebook_id,
        "CharacterReplacer",
        UNDERSCORES,
        [{"columnName": "Text", "positions": [0, 3]}],
    )

    ConverterJob(converter_id=converter_id).run()

    assert working_document(client, notebook_id)[Text] == ["a 1", "a_2", "a 3"]


class LineSplitter(DocumentConverter):
    """Splits each Text item into one item per line."""

    SCHEMA = BaseConverterSchema
    metadata = {"allowed_types": [Text]}

    def get_output_type(self, column_name=None):
        return Text(arrow_type=pa.string())

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        contents, sources = [], []
        for index, value in enumerate(x.arrow_table.column(0).to_pylist()):
            for line in value.split("\n"):
                contents.append(line)
                sources.append(index)
        return DashAIDataset(
            pa.table(
                {
                    "content": pa.array(contents, type=pa.string()),
                    "source": pa.array(sources, type=pa.int64()),
                }
            ),
            types={"content": Text(arrow_type=pa.string())},
        )


@pytest.fixture(name="line_splitter")
def fixture_line_splitter(client: TestClient):
    registry = client.app.container["component_registry"]
    registry.register_component(LineSplitter)
    yield "LineSplitter"
    registry.unregister_component(LineSplitter)


def test_a_document_converter_splits_items_in_a_job(client, line_splitter):
    notebook_id = create_document_notebook(
        client, "job_split", ["x_1\nx_2", image(), "x_3"]
    )
    converter_id = add_converter(
        client, notebook_id, line_splitter, {}, [{"columnName": "Text"}]
    )

    ConverterJob(converter_id=converter_id).run()

    document = working_document(client, notebook_id)
    assert document[Text] == ["x_1", "x_2", "x_3"]
    assert [item.position for item in document.items()] == [0, 1, 2, 3]
    assert document.items()[2].type is DashAIImage


def test_deleting_a_pick_after_a_split_replays_the_split(client, line_splitter):
    notebook_id = create_document_notebook(client, "split_replay", ["x_1\nx_2", "x_3"])
    first = add_converter(
        client, notebook_id, line_splitter, {}, [{"columnName": "Text"}], offset=0
    )
    ConverterJob(converter_id=first).run()
    second = add_converter(
        client,
        notebook_id,
        "CharacterReplacer",
        UNDERSCORES,
        [{"columnName": "Text", "positions": [1]}],
        offset=1,
    )
    ConverterJob(converter_id=second).run()
    assert working_document(client, notebook_id)[Text] == ["x_1", "x 2", "x_3"]

    response = client.delete(f"/api/v1/converter/{second}")

    assert response.status_code == 200, response.text
    assert working_document(client, notebook_id)[Text] == ["x_1", "x_2", "x_3"]
