"""Saving the working copy of a document notebook as a new document."""

import json
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import ConverterStatus, DocumentStatus
from DashAI.back.dataloaders.classes.dashai_document import load_document
from DashAI.back.dependencies.database.models import Converter, Dataset
from DashAI.back.job.converter_job import ConverterJob
from DashAI.back.types.value_types import Text
from tests.back.document_fixtures import create_document_notebook, image, text

URL = "/api/v1/documents/from-notebook"


def _name() -> str:
    return f"saved_{uuid.uuid4().hex[:8]}"


def _add_converter(client, notebook_id, status=None):
    with client.app.container["session_factory"]() as db:
        converter = Converter(
            notebook_id=notebook_id,
            converter="CharacterReplacer",
            parameters={
                "order": 1,
                "params": {"char_to_replace": "_", "replacement_char": " "},
                "scope": {"columns": [{"idx": 1, "columnName": "Text"}], "rows": []},
                "target": None,
            },
        )
        if status is not None:
            converter.status = status
        db.add(converter)
        db.commit()
        db.refresh(converter)
        return converter.id


def test_the_converted_working_copy_becomes_a_new_document(client: TestClient):
    notebook_id = create_document_notebook(
        client, _name(), [text("A_title", kind="title"), "a_b", image()]
    )
    ConverterJob(converter_id=_add_converter(client, notebook_id)).run()
    name = _name()

    response = client.post(URL, json={"name": f"  {name} ", "notebook_id": notebook_id})

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == name
    assert body["status"] == DocumentStatus.FINISHED.value
    assert body["content_counts"] == {"Text": 2, "Image": 1}
    folder = Path(body["file_path"])
    assert not (folder / "source").exists()
    saved = load_document(str(folder / "document"))
    assert saved[Text] == ["A title", "a b"]
    assert [item.kind for item in saved.items()] == ["title", "paragraph", "image"]
    assert saved.metadata["derived_from"]["notebook_id"] == notebook_id


def test_the_new_document_serves_its_content(client: TestClient):
    notebook_id = create_document_notebook(client, _name(), ["one", "two"])
    created = client.post(URL, json={"name": _name(), "notebook_id": notebook_id})
    document_id = created.json()["id"]

    content = client.get(f"/api/v1/documents/{document_id}/content").json()

    assert [item["content"] for item in content["items"]] == ["one", "two"]
    assert client.get(f"/api/v1/documents/{document_id}/source").status_code == 404


def test_the_notebook_working_copy_is_left_alone(client: TestClient):
    notebook_id = create_document_notebook(client, _name(), ["keep"])
    created = client.post(URL, json={"name": _name(), "notebook_id": notebook_id})
    assert created.status_code == 201, created.text

    notebook = client.get(f"/api/v1/notebook/{notebook_id}").json()
    working = Path(notebook["file_path"]) / "document" / "document.json"
    assert "derived_from" not in json.loads(working.read_text("utf-8"))["metadata"]


def test_a_taken_name_is_refused(client: TestClient):
    notebook_id = create_document_notebook(client, _name(), ["a"])
    name = _name()
    assert (
        client.post(URL, json={"name": name, "notebook_id": notebook_id}).status_code
        == 201
    )
    response = client.post(URL, json={"name": name, "notebook_id": notebook_id})
    assert response.status_code == 409, response.text


def test_an_empty_name_is_refused(client: TestClient):
    notebook_id = create_document_notebook(client, _name(), ["a"])
    response = client.post(URL, json={"name": "  ", "notebook_id": notebook_id})
    assert response.status_code == 422, response.text


def test_an_unknown_notebook_is_not_found(client: TestClient):
    response = client.post(URL, json={"name": _name(), "notebook_id": 987654})
    assert response.status_code == 404, response.text


def test_a_dataset_notebook_is_refused(client: TestClient, dataset_1: Dataset):
    notebook = client.post(
        "/api/v1/notebook/", json={"name": _name(), "dataset_id": dataset_1.id}
    ).json()
    response = client.post(URL, json={"name": _name(), "notebook_id": notebook["id"]})
    assert response.status_code == 422, response.text


def test_saving_waits_for_running_converters(client: TestClient):
    notebook_id = create_document_notebook(client, _name(), ["a_b"])
    _add_converter(client, notebook_id, status=ConverterStatus.STARTED)
    response = client.post(URL, json={"name": _name(), "notebook_id": notebook_id})
    assert response.status_code == 409, response.text
