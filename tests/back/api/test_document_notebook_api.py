"""API tests for notebooks created from documents."""

import io
import uuid
from pathlib import Path
from typing import Tuple

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from DashAI.back.core.enums.status import DocumentStatus
from DashAI.back.dataloaders.classes.dashai_document import (
    DashAIDocument,
    DocumentItem,
    save_document,
)
from DashAI.back.dependencies.database.models import DataDocument, Dataset
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Text


def _png_bytes() -> bytes:
    """Encode a tiny red PNG.

    Returns
    -------
    bytes
        The PNG file content.
    """
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format="PNG")
    return buffer.getvalue()


def _create_data_document(
    client: TestClient,
    name: str,
    status: DocumentStatus = DocumentStatus.FINISHED,
) -> Tuple[int, Path]:
    """Write a parsed three item document to disk and register it.

    The items are a title and an image on page 1 and a level 2 heading on
    page 2, so kinds, attrs, pages and the type interleaving are all
    observable.

    Parameters
    ----------
    client : TestClient
        Test client whose app owns the config and the session factory.
    name : str
        Unique document name.
    status : DocumentStatus
        Status stored on the row.

    Returns
    -------
    Tuple[int, Path]
        The document id and its ``<uuid>`` directory.
    """
    container = client.app.container
    config = container["config"]
    session_factory = container["session_factory"]
    document_dir = Path(config["DOCUMENTS_PATH"]) / uuid.uuid4().hex
    document = DashAIDocument.from_items(
        [
            DocumentItem(Text, "Annual report", page=1, kind="title"),
            DocumentItem(
                DashAIImage,
                DashAIImage(bytes=_png_bytes(), path="figure.png"),
                page=1,
            ),
            DocumentItem(Text, "Results", page=2, kind="heading", attrs={"level": 2}),
        ],
        metadata={"file_name": f"{name}.pdf", "file_type": "pdf", "n_pages": 2},
    )
    save_document(document, document_dir / "document")
    with session_factory() as db:
        row = DataDocument(
            name=name,
            file_name=f"{name}.pdf",
            file_type="pdf",
            file_hash="0" * 64,
            file_path=str(document_dir),
            dataloader="PypdfDocumentDataLoader",
            dataloader_params={},
            content_counts={"Text": 2, "Image": 1},
            total_pages=2,
            status=status,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row.id, document_dir


@pytest.fixture(name="source_document", scope="module")
def fixture_source_document(client: TestClient) -> Tuple[int, Path]:
    """Register the document shared by the notebook tests.

    Parameters
    ----------
    client : TestClient
        Module test client.

    Returns
    -------
    Tuple[int, Path]
        The document id and its directory.
    """
    return _create_data_document(client, "notebook_source_document")


@pytest.fixture(name="document_notebook", scope="module")
def fixture_document_notebook(
    client: TestClient, source_document: Tuple[int, Path]
) -> dict:
    """Create one notebook over the shared document.

    Parameters
    ----------
    client : TestClient
        Module test client.
    source_document : Tuple[int, Path]
        The shared document.

    Returns
    -------
    dict
        The created notebook as returned by the API.
    """
    document_id, _ = source_document
    response = client.post(
        "/api/v1/notebook/",
        json={"name": "document_notebook", "document_id": document_id},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_document_notebook_copies_parsed_content(
    client: TestClient, source_document: Tuple[int, Path], document_notebook: dict
) -> None:
    document_id, document_dir = source_document
    config = client.app.container["config"]

    assert document_notebook["data_kind"] == "document"
    assert document_notebook["document_id"] == document_id
    assert document_notebook["dataset_id"] is None
    working_dir = Path(document_notebook["file_path"])
    assert (
        working_dir.parent.resolve()
        == (Path(config["NOTEBOOK_PATH"]) / "documents").resolve()
    )
    assert working_dir.resolve() != document_dir.resolve()
    assert (working_dir / "document" / "document.json").exists()
    assert not (working_dir / "source").exists()


def test_create_notebook_requires_exactly_one_source(
    client: TestClient, source_document: Tuple[int, Path], dataset_1: Dataset
) -> None:
    document_id, _ = source_document

    both = client.post(
        "/api/v1/notebook/",
        json={"name": "both", "dataset_id": dataset_1.id, "document_id": document_id},
    )
    neither = client.post("/api/v1/notebook/", json={"name": "neither"})

    assert both.status_code == 422, both.text
    assert neither.status_code == 422, neither.text


def test_create_notebook_rejects_unfinished_document(client: TestClient) -> None:
    document_id, _ = _create_data_document(
        client, "unfinished_document", status=DocumentStatus.STARTED
    )

    response = client.post(
        "/api/v1/notebook/", json={"name": "early", "document_id": document_id}
    )

    assert response.status_code == 422, response.text
    assert response.json()["detail"] == "Document is not ready"


def test_create_notebook_unknown_sources(client: TestClient) -> None:
    missing_document = client.post(
        "/api/v1/notebook/", json={"name": "ghost", "document_id": 999999}
    )
    missing_dataset = client.post(
        "/api/v1/notebook/", json={"name": "ghost", "dataset_id": 999999}
    )

    assert missing_document.status_code == 404, missing_document.text
    assert missing_dataset.status_code == 404, missing_dataset.text


def test_dataset_notebook_reports_dataset_kind(
    client: TestClient, dataset_1: Dataset
) -> None:
    response = client.post(
        "/api/v1/notebook/",
        json={"name": "dataset_kind", "dataset_id": dataset_1.id},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["data_kind"] == "dataset"
    assert body["document_id"] is None
    assert (Path(body["file_path"]) / "dataset").exists()


def test_list_and_rename_document_notebook(
    client: TestClient, document_notebook: dict
) -> None:
    listed = client.get("/api/v1/notebook/")
    renamed = client.patch(
        f"/api/v1/notebook/{document_notebook['id']}",
        json={"name": "document_notebook_renamed"},
    )
    fetched = client.get(f"/api/v1/notebook/{document_notebook['id']}")

    assert listed.status_code == 200, listed.text
    kinds = {item["id"]: item["data_kind"] for item in listed.json()}
    assert kinds[document_notebook["id"]] == "document"
    assert renamed.status_code == 200, renamed.text
    assert fetched.json()["name"] == "document_notebook_renamed"
    assert fetched.json()["data_kind"] == "document"
