"""Tests for the /api/v1/documents CRUD endpoints."""

import uuid
from pathlib import Path

from DashAI.back.core.enums.status import DocumentStatus
from DashAI.back.dependencies.database.models import DataDocument

DOCUMENT_LOADERS = {
    "PypdfDocumentDataLoader",
    "PdfPlumberDocumentDataLoader",
    "PdfMinerDocumentDataLoader",
    "PlainTextDocumentDataLoader",
}


def _name() -> str:
    return f"doc_{uuid.uuid4().hex[:8]}"


def _create(client, **overrides):
    payload = {
        "name": _name(),
        "file_name": "notes.txt",
        "dataloader": "PlainTextDocumentDataLoader",
        "dataloader_params": {},
    }
    payload.update(overrides)
    return client.post("/api/v1/documents/", json=payload)


def test_create_returns_a_placeholder_with_resolved_params(client):
    response = _create(client, file_name="Notes.MD")
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == DocumentStatus.NOT_STARTED.value
    assert body["file_name"] == "Notes.MD"
    assert body["file_type"] == "md"
    assert body["file_path"] == ""
    assert body["dataloader_params"] == {"encoding": "utf-8"}


def test_create_rejects_a_duplicate_name(client):
    name = _name()
    assert _create(client, name=name).status_code == 201
    assert _create(client, name=name).status_code == 409


def test_create_rejects_an_empty_name(client):
    assert _create(client, name="   ").status_code == 422


def test_create_rejects_an_unknown_loader(client):
    assert _create(client, dataloader="NopeLoader").status_code == 422


def test_create_rejects_a_dataset_loader(client):
    response = _create(client, dataloader="CSVDataLoader", file_name="iris.csv")
    assert response.status_code == 422
    assert "loads datasets, not documents" in response.json()["detail"]


def test_create_rejects_an_unsupported_extension(client):
    response = _create(
        client, dataloader="PypdfDocumentDataLoader", file_name="notes.txt"
    )
    assert response.status_code == 422
    assert ".pdf" in response.json()["detail"]


def test_create_rejects_invalid_loader_params(client):
    response = _create(
        client,
        dataloader="PdfMinerDocumentDataLoader",
        file_name="paper.pdf",
        dataloader_params={"boxes_flow": 5.0},
    )
    assert response.status_code == 422


def test_list_and_get(client):
    created = _create(client).json()
    listed = client.get("/api/v1/documents/")
    assert listed.status_code == 200
    assert created["id"] in [document["id"] for document in listed.json()]
    fetched = client.get(f"/api/v1/documents/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == created["name"]
    assert client.get("/api/v1/documents/999999").status_code == 404


def test_patch_renames_and_rejects_conflicts(client):
    first = _create(client).json()
    second = _create(client).json()
    new_name = _name()
    renamed = client.patch(
        f"/api/v1/documents/{first['id']}", json={"name": f"  {new_name}  "}
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == new_name
    conflict = client.patch(
        f"/api/v1/documents/{second['id']}", json={"name": new_name}
    )
    assert conflict.status_code == 409
    empty = client.patch(f"/api/v1/documents/{second['id']}", json={"name": "  "})
    assert empty.status_code == 422
    assert (
        client.patch("/api/v1/documents/999999", json={"name": "x"}).status_code == 404
    )


def test_patch_moves_a_document_into_a_folder_and_back(client):
    created = _create(client).json()
    folder = client.post("/api/v1/folder/", json={"name": _name()}).json()
    moved = client.patch(
        f"/api/v1/documents/{created['id']}", json={"folder_id": folder["id"]}
    )
    assert moved.status_code == 200
    assert moved.json()["folder_id"] == folder["id"]
    cleared = client.patch(
        f"/api/v1/documents/{created['id']}", json={"folder_id": None}
    )
    assert cleared.json()["folder_id"] is None
    missing = client.patch(
        f"/api/v1/documents/{created['id']}", json={"folder_id": 999999}
    )
    assert missing.status_code == 404


def test_deleting_a_folder_detaches_its_documents(client):
    created = _create(client).json()
    folder = client.post("/api/v1/folder/", json={"name": _name()}).json()
    client.patch(f"/api/v1/documents/{created['id']}", json={"folder_id": folder["id"]})
    assert client.delete(f"/api/v1/folder/{folder['id']}").status_code == 204
    fetched = client.get(f"/api/v1/documents/{created['id']}")
    assert fetched.json()["folder_id"] is None


def test_upload_through_the_job_endpoint_finishes(upload_document):
    document = upload_document(b"One.\n\nTwo.", file_name="two.txt")
    assert document["status"] == DocumentStatus.FINISHED.value
    assert document["content_counts"] == {"Text": 2}
    assert document["file_name"] == "two.txt"
    assert Path(document["file_path"], "document").is_dir()


def test_delete_placeholder_leaves_the_documents_root_alone(client, upload_document):
    kept = upload_document(b"Keep me.")
    placeholder = _create(client).json()
    documents_root = Path(client.app.container["config"]["DOCUMENTS_PATH"])
    assert client.delete(f"/api/v1/documents/{placeholder['id']}").status_code == 204
    assert documents_root.is_dir()
    assert Path(kept["file_path"]).is_dir()
    assert client.get(f"/api/v1/documents/{placeholder['id']}").status_code == 404


def test_delete_removes_the_document_directory(client, upload_document):
    document = upload_document(b"Remove me.")
    root = Path(document["file_path"])
    assert root.is_dir()
    assert client.delete(f"/api/v1/documents/{document['id']}").status_code == 204
    assert not root.exists()
    assert client.delete(f"/api/v1/documents/{document['id']}").status_code == 404


def test_delete_is_refused_while_parsing(client):
    created = _create(client).json()
    with client.app.container["session_factory"]() as db:
        row = db.get(DataDocument, created["id"])
        row.set_status_as_started()
        db.commit()
    assert client.delete(f"/api/v1/documents/{created['id']}").status_code == 409


def test_component_listing_marks_document_loaders(client):
    components = client.get(
        "/api/v1/component/", params={"select_types": ["DataLoader"]}
    ).json()
    kinds = {c["name"]: c["metadata"]["data_kinds"] for c in components}
    assert {name for name, k in kinds.items() if k == ["document"]} == DOCUMENT_LOADERS
    assert kinds["CSVDataLoader"] == ["dataset"]
