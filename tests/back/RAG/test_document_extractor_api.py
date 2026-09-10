"""Tests for the document extractor API endpoints."""

import json
import os
import tempfile
import uuid

from DashAI.back.dependencies.database.models import (
    Document,
    GenerativeSession,
    RAGExtractor,
)
from DashAI.back.models.RAG.documents import DocumentFileType


def _create_session(db, name: str) -> int:
    """Create an empty RAG session to own documents."""
    session = GenerativeSession(
        task_name="RAGTask",
        model_name="RAGPipeline",
        parameters={"documents": []},
        name=name,
    )
    db.add(session)
    db.commit()
    return session.id


def _create_document(
    db, file_name: str, file_hash: str, content: str = "content"
) -> int:
    """Create a txt test document in its own session and return its ID."""
    tmp_path = os.path.join(tempfile.gettempdir(), file_name)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    session_id = _create_session(db, f"owner_of_{file_hash}")
    extractor = RAGExtractor(component_name="PlainTextExtractor", params={})
    db.add(extractor)
    db.flush()
    doc = Document(
        session_id=session_id,
        file_name=file_name,
        file_type="txt",
        file_path=tmp_path,
        file_hash=file_hash,
        extractor_id=extractor.id,
    )
    db.add(doc)
    db.flush()
    session = db.get(GenerativeSession, session_id)
    session.parameters = {"documents": [doc.id]}
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

    def _session(self, client, name: str) -> int:
        """Create an empty RAG session to upload into."""
        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            return _create_session(db, name)

    def _upload(self, client, file_name: str, content: bytes, session_id=None):
        """POST a document into a session via the upload endpoint."""
        if session_id is None:
            # Session names are unique, so keep them distinct per upload.
            session_id = self._session(
                client, f"upload_{file_name}_{uuid.uuid4().hex[:8]}"
            )
        metadata = json.dumps(
            {
                "file_name": file_name,
                "optional_metadata": {"name": file_name, "source": "test"},
            }
        )
        return client.post(
            f"/api/v1/document/session/{session_id}",
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

    def test_upload_dedup_within_a_session_returns_409(self, client):
        """The same bytes twice in one session returns 409 + the existing doc."""
        session_id = self._session(client, "dedup_session")
        resp1 = self._upload(
            client, "dup_file.txt", b"Duplicate file content.", session_id
        )
        assert resp1.status_code == 201
        resp2 = self._upload(
            client, "dup_file_renamed.txt", b"Duplicate file content.", session_id
        )
        assert resp2.status_code == 409
        detail = resp2.json()["detail"]
        assert detail["existing_document"]["file_hash"] == resp1.json()["file_hash"]

    def test_upload_same_bytes_in_another_session_is_allowed(self, client):
        """Dedup is per session: another session gets its own document."""
        content = b"Duplicate across sessions."
        first = self._upload(client, "across.txt", content)
        second = self._upload(client, "across.txt", content)
        assert first.status_code == 201, first.text
        assert second.status_code == 201, second.text
        assert first.json()["id"] != second.json()["id"]
        assert first.json()["session_id"] != second.json()["session_id"]

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

    def test_update_extractor_needs_no_confirmation(self, client):
        """Committing an extractor choice just works -- there is no force flag.

        A document belongs to exactly one session, so changing its extractor
        cannot destroy anybody else's index.
        """
        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            doc_id = _create_document(db, "test_update_ext.txt", "update_ext_hash_010")

        resp = client.put(
            f"/api/v1/document/{doc_id}/extractor",
            json={"extractor": {"component": "PlainTextExtractor", "params": {}}},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["extractor"]["component"] == "PlainTextExtractor"

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
