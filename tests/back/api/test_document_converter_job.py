import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import ConverterStatus
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
