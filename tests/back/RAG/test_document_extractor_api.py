"""Tests for the document extractor API endpoints."""

import json
import os
import tempfile

from DashAI.back.dependencies.database.models import Document, RAGExtractor
from DashAI.back.models.RAG.documents import DocumentFileType


def _create_document(
    db, file_name: str, file_hash: str, content: str = "content"
) -> int:
    """Create a txt test document (with extractor) in the DB and return its ID."""
    tmp_path = os.path.join(tempfile.gettempdir(), file_name)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    extractor = RAGExtractor(component_name="PlainTextExtractor", params={})
    db.add(extractor)
    db.flush()
    doc = Document(
        file_name=file_name,
        file_type="txt",
        file_path=tmp_path,
        file_hash=file_hash,
        extractor_id=extractor.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc.id


class TestExtractEndpoint:
    """Tests for POST /api/v1/document/{id}/extract."""

    def test_extract_with_stored_extractor(self, client):
        """Extract text using the document's stored/default extractor."""
        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            doc_id = _create_document(
                db,
                "test_extract_doc.txt",
                "extract_test_hash_001",
                "Test content for extraction.",
            )

        resp = client.post(f"/api/v1/document/{doc_id}/extract", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "text" in data
        assert "extractor" in data
        assert "char_count" in data
        assert data["text"] == "Test content for extraction."

    def test_extract_with_specific_extractor(self, client):
        """Extract text using a specific extractor by name."""
        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            doc_id = _create_document(
                db,
                "test_extract_specific.txt",
                "extract_specific_hash_002",
                "Plain text extracted.",
            )

        resp = client.post(
            f"/api/v1/document/{doc_id}/extract",
            json={"extractor": {"component": "PlainTextExtractor", "params": {}}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["text"] == "Plain text extracted."
        assert data["extractor"]["component"] == "PlainTextExtractor"

    def test_extract_incompatible_extractor(self, client):
        """Using an extractor incompatible with the file type returns 400."""
        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            doc_id = _create_document(
                db, "test_incompat.txt", "incompat_hash_003", "text content"
            )

        # PDF extractors should not work with txt files
        resp = client.post(
            f"/api/v1/document/{doc_id}/extract",
            json={"extractor": {"component": "PyMuPDFExtractor", "params": {}}},
        )
        assert resp.status_code == 400
        assert "does not support" in resp.json()["detail"]

    def test_extract_document_not_found(self, client):
        resp = client.post("/api/v1/document/99999/extract", json={})
        assert resp.status_code == 404


class TestUploadWarmsExtractionCache:
    """Uploading a document warms the extraction cache (best-effort)."""

    def _upload(self, client, file_name: str, content: bytes):
        """POST a document via the upload endpoint."""
        metadata = json.dumps(
            {
                "file_name": file_name,
                "optional_metadata": {"name": file_name, "source": "test"},
            }
        )
        return client.post(
            "/api/v1/document/",
            files={"file": (file_name, content, "text/plain")},
            data={"metadata": metadata},
        )

    def test_upload_txt_warms_cache(self, client):
        """Uploading a txt file makes the default extractor cache warm."""
        resp = self._upload(client, "warm_cache.txt", b"Cache warming text.")
        assert resp.status_code == 201
        doc_id = resp.json()["id"]

        # Immediate extract with no body should hit the cache warmed at upload.
        extract_resp = client.post(f"/api/v1/document/{doc_id}/extract", json={})
        assert extract_resp.status_code == 200
        data = extract_resp.json()
        assert data["cached"] is True
        assert data["text"] == "Cache warming text."
        assert data["extractor"]["component"] == "PlainTextExtractor"

    def test_upload_dedup_returns_409_without_force(self, client):
        """Re-uploading the same file (hash dedup) returns 409 + existing doc."""
        resp1 = self._upload(client, "dup_file.txt", b"Duplicate file content.")
        assert resp1.status_code == 201
        resp2 = self._upload(client, "dup_file_renamed.txt", b"Duplicate file content.")
        assert resp2.status_code == 409
        detail = resp2.json()["detail"]
        assert detail["detail"] == "Document already exists"
        assert detail["existing_document"]["file_hash"] == resp1.json()["file_hash"]

    def test_upload_dedup_with_force_updates(self, client):
        """Re-uploading the same file with force=true overwrites the existing doc."""
        resp1 = self._upload(client, "force_file.txt", b"Force overwrite content.")
        assert resp1.status_code == 201
        resp2 = client.post(
            "/api/v1/document/",
            files={
                "file": (
                    "force_file_renamed.txt",
                    b"Force overwrite content.",
                    "text/plain",
                )
            },  # noqa: E501
            data={
                "metadata": json.dumps(
                    {"file_name": "force_file_renamed.txt", "optional_metadata": {}}
                )
            },
            params={"force": "true"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["id"] == resp1.json()["id"]
        assert resp2.json()["file_name"] == "force_file_renamed.txt"

    def test_upload_unsupported_type_rejected(self, client):
        """Uploading an unsupported extension returns 400 before extraction."""
        resp = self._upload(client, "notes.exe", b"not a supported type")
        assert resp.status_code == 400
        assert "Unsupported file type" in resp.json()["detail"]

    def test_upload_rejection_names_the_supported_types(self, client):
        """The rejection says which formats *are* accepted.

        "Unsupported file type: ipynb" on its own leaves the user guessing, so
        the message has to carry the list the enum defines.
        """
        resp = self._upload(client, "analysis.ipynb", b'{"cells": []}')
        assert resp.status_code == 400

        detail = resp.json()["detail"]
        assert "ipynb" in detail
        for extension in DocumentFileType.supported_extensions():
            assert extension in detail, (
                f"the rejection does not mention '{extension}': {detail}"
            )

    def test_upload_without_extension_rejected(self, client):
        """A name with no extension is rejected rather than read as empty."""
        resp = self._upload(client, "README", b"no extension here")
        assert resp.status_code == 400
        assert "Unsupported file type" in resp.json()["detail"]


class TestUpdateExtractorEndpoint:
    """Tests for PUT /api/v1/document/{id}/extractor."""

    def test_update_without_pipelines(self, client):
        """Update extractor for a document not linked to any pipeline."""
        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            doc_id = _create_document(db, "test_update_ext.txt", "update_ext_hash_010")

        resp = client.put(
            f"/api/v1/document/{doc_id}/extractor",
            json={
                "extractor": {"component": "PlainTextExtractor", "params": {}},
                "force": False,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["extractor"]["component"] == "PlainTextExtractor"

    def test_update_invalid_component(self, client):
        """Using a non-existent extractor name returns 400."""
        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            doc_id = _create_document(
                db, "test_invalid_comp.txt", "invalid_comp_hash_012"
            )

        resp = client.put(
            f"/api/v1/document/{doc_id}/extractor",
            json={"extractor": {"component": "NonExistentExtractor", "params": {}}},
        )
        assert resp.status_code == 400

    def test_update_document_not_found(self, client):
        resp = client.put(
            "/api/v1/document/99999/extractor",
            json={"extractor": {"component": "PlainTextExtractor", "params": {}}},
        )
        assert resp.status_code == 404
