"""API tests for notebooks created from documents."""

import inspect
import io
import uuid
from pathlib import Path
from typing import Tuple

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from DashAI.back.core.enums.status import DatasetStatus, DocumentStatus
from DashAI.back.dataloaders.classes.dashai_document import (
    DashAIDocument,
    DocumentItem,
    save_document,
)
from DashAI.back.dependencies.database.models import DataDocument, Dataset
from DashAI.back.job.base_job import JobError
from DashAI.back.job.dataset_job import DatasetJob
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


def _create_document_notebook(client: TestClient, document_id: int, name: str) -> dict:
    """Create a notebook over a document through the API.

    Parameters
    ----------
    client : TestClient
        Module test client.
    document_id : int
        Source document.
    name : str
        Notebook name.

    Returns
    -------
    dict
        The created notebook.
    """
    response = client.post(
        "/api/v1/notebook/", json={"name": name, "document_id": document_id}
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_deleting_document_notebook_keeps_source(
    client: TestClient, source_document: Tuple[int, Path]
) -> None:
    document_id, document_dir = source_document
    created = _create_document_notebook(client, document_id, "short_lived")
    working_dir = Path(created["file_path"])
    assert working_dir.exists()

    response = client.delete(f"/api/v1/notebook/{created['id']}")

    assert response.status_code == 204, response.text
    assert not working_dir.exists()
    assert (document_dir / "document" / "document.json").exists()


def test_deleting_document_removes_its_notebooks(client: TestClient) -> None:
    document_id, _ = _create_data_document(client, "document_deleted_with_notebooks")
    created = _create_document_notebook(client, document_id, "orphan_candidate")
    working_dir = Path(created["file_path"])

    response = client.delete(f"/api/v1/documents/{document_id}")

    assert response.status_code == 204, response.text
    assert client.get(f"/api/v1/notebook/{created['id']}").status_code == 404
    assert not working_dir.exists()


def test_document_content_reading_order_kinds_and_urls(
    client: TestClient, document_notebook: dict
) -> None:
    notebook_id = document_notebook["id"]

    response = client.get(f"/api/v1/notebook/{notebook_id}/document-content")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["notebook_id"] == notebook_id
    assert body["content_type"] == "all"
    assert body["total"] == 3
    assert [
        (item["type"], item["position"], item["page"], item["kind"], item["attrs"])
        for item in body["items"]
    ] == [
        ("Text", 0, 1, "title", {}),
        ("Image", 1, 1, "image", {}),
        ("Text", 2, 2, "heading", {"level": 2}),
    ]
    assert body["items"][0]["content"] == "Annual report"
    assert body["items"][1]["url"] == (
        f"/api/v1/notebook/{notebook_id}/document-images/1"
    )


def test_document_content_matches_the_source_document(
    client: TestClient, source_document: Tuple[int, Path], document_notebook: dict
) -> None:
    document_id, _ = source_document

    notebook_items = client.get(
        f"/api/v1/notebook/{document_notebook['id']}/document-content"
    ).json()["items"]
    source_items = client.get(f"/api/v1/documents/{document_id}/content").json()[
        "items"
    ]

    def without_url(items: list) -> list:
        return [{k: v for k, v in item.items() if k != "url"} for item in items]

    assert without_url(notebook_items) == without_url(source_items)


def test_document_content_by_type_and_pagination(
    client: TestClient, document_notebook: dict
) -> None:
    url = f"/api/v1/notebook/{document_notebook['id']}/document-content"

    texts = client.get(url, params={"content_type": "Text"}).json()
    window = client.get(url, params={"offset": 1, "limit": 1}).json()

    assert texts["total"] == 2
    assert [item["position"] for item in texts["items"]] == [0, 2]
    assert window["total"] == 3
    assert [item["position"] for item in window["items"]] == [1]


def test_document_content_reads_the_working_copy(
    client: TestClient, source_document: Tuple[int, Path]
) -> None:
    document_id, _ = source_document
    created = _create_document_notebook(client, document_id, "edited_copy")
    save_document(
        DashAIDocument.from_items([DocumentItem(Text, "Rewritten", page=1)]),
        Path(created["file_path"]) / "document",
    )

    notebook_body = client.get(
        f"/api/v1/notebook/{created['id']}/document-content"
    ).json()
    source_body = client.get(f"/api/v1/documents/{document_id}/content").json()

    assert [item["content"] for item in notebook_body["items"]] == ["Rewritten"]
    assert source_body["total"] == 3


def test_document_outline_lists_the_working_copy(
    client: TestClient, document_notebook: dict
) -> None:
    body = client.get(
        f"/api/v1/notebook/{document_notebook['id']}/document-outline"
    ).json()

    assert body["notebook_id"] == document_notebook["id"]
    assert body["total"] == 3
    assert [
        (item["position"], item["kind"], item["level"], item["label"])
        for item in body["items"]
    ] == [
        (0, "title", None, "Annual report"),
        (1, "image", None, None),
        (2, "heading", 2, "Results"),
    ]


def test_document_image_is_served_from_the_working_copy(
    client: TestClient, document_notebook: dict
) -> None:
    base = f"/api/v1/notebook/{document_notebook['id']}/document-images"

    image = client.get(f"{base}/1")

    assert image.status_code == 200, image.text
    assert image.headers["content-type"] == "image/png"
    assert image.headers["cache-control"] == "no-cache"
    assert Image.open(io.BytesIO(image.content)).size == (4, 4)
    assert client.get(f"{base}/0").status_code == 404


def test_document_endpoints_reject_bad_requests(
    client: TestClient, document_notebook: dict, dataset_1: Dataset
) -> None:
    dataset_notebook = client.post(
        "/api/v1/notebook/",
        json={"name": "tabular_for_content", "dataset_id": dataset_1.id},
    ).json()
    base = f"/api/v1/notebook/{document_notebook['id']}"

    unknown_type = client.get(
        f"{base}/document-content", params={"content_type": "Table"}
    )
    bad_limit = client.get(f"{base}/document-content", params={"limit": 0})
    dataset_kind = [
        client.get(f"/api/v1/notebook/{dataset_notebook['id']}/{route}")
        for route in ("document-content", "document-outline", "document-images/0")
    ]
    missing = client.get("/api/v1/notebook/999999/document-content")

    assert unknown_type.status_code == 422, unknown_type.text
    assert bad_limit.status_code == 422, bad_limit.text
    assert [response.status_code for response in dataset_kind] == [422, 422, 422]
    assert dataset_kind[0].json()["detail"] == "Notebook is not a document notebook"
    assert missing.status_code == 404, missing.text


def test_document_endpoints_run_in_the_threadpool() -> None:
    from DashAI.back.api.api_v1.endpoints import notebook

    for handler in (
        notebook.get_notebook_document_content,
        notebook.get_notebook_document_outline,
        notebook.get_notebook_document_image,
    ):
        assert not inspect.iscoroutinefunction(handler)


def test_datasets_only_explorer_rejects_document_notebook(
    client: TestClient, document_notebook: dict
) -> None:
    response = client.post(
        "/api/v1/explorer/",
        json={
            "notebook_id": document_notebook["id"],
            "exploration_type": "HistogramPlotExplorer",
            "columns": [],
            "parameters": {},
        },
    )

    assert response.status_code == 422, response.text
    assert response.json()["detail"] == (
        "Explorer HistogramPlotExplorer cannot run on a document notebook"
    )


def test_datasets_only_converter_rejects_document_notebook(
    client: TestClient, document_notebook: dict
) -> None:
    response = client.post(
        "/api/v1/converter/",
        json={
            "notebook_id": document_notebook["id"],
            "converter": "StandardScaler",
            "parameters": {"order": 0},
        },
    )

    assert response.status_code == 422, response.text
    assert response.json()["detail"] == (
        "Converter StandardScaler cannot run on a document notebook"
    )


def test_dataset_job_rejects_document_notebook(
    client: TestClient, document_notebook: dict
) -> None:
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        dataset = Dataset(name="saved_from_document_notebook", file_path="")
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        dataset_id = dataset.id

    job = DatasetJob(
        job_type="DatasetJob",
        kwargs={
            "dataset_id": dataset_id,
            "notebook_id": document_notebook["id"],
            "params": {},
            "url": "",
            "file_path": None,
        },
    )

    with pytest.raises(JobError, match="document notebook"):
        job.run()

    with session_factory() as db:
        assert db.get(Dataset, dataset_id).status == DatasetStatus.ERROR
