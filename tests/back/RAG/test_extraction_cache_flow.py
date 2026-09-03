"""Integration tests for document extraction with processed_document_content cache.

Verifies the full flow across txt, md, and pdf file types:
extraction → cache hit/miss → signature invalidation when extractor config changes.
"""

import os
import tempfile
import uuid

import pytest

from DashAI.back.dependencies.database.models import (
    Document,
    GenerativeSession,
    RAGExtractor,
)

_EXTRACTOR_BY_FILE_TYPE = {
    "pdf": "PyMuPDFExtractor",
    "txt": "PlainTextExtractor",
    "md": "PlainTextExtractor",
}


def _make_minimal_pdf(path: str) -> None:
    """Write a minimal valid PDF file to the given path."""
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"  # noqa: E501
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"  # noqa: E501
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n190\n%%EOF"
    )
    with open(path, "wb") as f:
        f.write(content)


def _create_document(client, file_type: str, content: bytes | str) -> int:
    """Create a document in the DB and return its id."""
    session_factory = client.app.container["session_factory"]
    unique_hash = f"cache_flow_{file_type}_{uuid.uuid4().hex[:12]}"
    ext = "pdf" if file_type == "pdf" else file_type

    tmp_path = os.path.join(
        tempfile.gettempdir(), f"test_extract_cache_{file_type}_{unique_hash}.{ext}"
    )

    if file_type == "pdf":
        _make_minimal_pdf(tmp_path)
    else:
        mode = "w" if isinstance(content, str) else "wb"
        with open(tmp_path, mode, encoding="utf-8" if mode == "w" else None) as f:
            f.write(content)

    with session_factory() as db:
        # A document cannot exist without an owning session.
        session = GenerativeSession(
            task_name="RAGTask",
            model_name="RAGPipeline",
            parameters={"documents": []},
            name=f"cache_flow_{unique_hash}",
        )
        db.add(session)
        db.flush()
        extractor = RAGExtractor(
            component_name=_EXTRACTOR_BY_FILE_TYPE[file_type], params={}
        )
        db.add(extractor)
        db.flush()
        doc = Document(
            session_id=session.id,
            file_name=f"test_cache.{ext}",
            file_type=file_type,
            file_path=tmp_path,
            file_hash=unique_hash,
            extractor_id=extractor.id,
        )
        db.add(doc)
        db.flush()
        session.parameters = {"documents": [doc.id]}
        db.commit()
        db.refresh(doc)
        return doc.id


class TestExtractionCacheFlowTxt:
    """Cache flow tests for .txt files."""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.doc_id = _create_document(
            client, "txt", "Hello from DashAI txt extraction cache test."
        )

    def test_first_extraction_cache_miss(self, client):
        resp = client.post(f"/api/v1/document/{self.doc_id}/extract", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["cached"] is False
        assert "Hello from DashAI txt" in data["text"]

    def test_second_extraction_cache_hit(self, client):
        client.post(f"/api/v1/document/{self.doc_id}/extract", json={})
        resp = client.post(f"/api/v1/document/{self.doc_id}/extract", json={})
        assert resp.status_code == 200
        assert resp.json()["cached"] is True

    def test_different_params_cache_miss(self, client):
        client.post(f"/api/v1/document/{self.doc_id}/extract", json={})
        resp = client.post(
            f"/api/v1/document/{self.doc_id}/extract",
            json={
                "extractor": {
                    "component": "PlainTextExtractor",
                    "params": {"encoding": "latin-1"},
                }
            },
        )
        assert resp.status_code == 200
        assert resp.json()["cached"] is False

    def test_two_entries_persisted(self, client):
        client.post(f"/api/v1/document/{self.doc_id}/extract", json={})
        client.post(
            f"/api/v1/document/{self.doc_id}/extract",
            json={
                "extractor": {
                    "component": "PlainTextExtractor",
                    "params": {"encoding": "latin-1"},
                }
            },
        )
        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            from DashAI.back.dependencies.database.models import (
                ProcessedDocumentContent,
            )

            entries = (
                db.query(ProcessedDocumentContent)
                .filter_by(document_id=self.doc_id)
                .all()
            )
            # 1:1 invariant — re-extraction with different params overwrites
            assert len(entries) == 1
            assert entries[0].signature is not None

    def test_re_extraction_updates_single_row(self, client):
        """Different params update the single content row in place."""
        client.post(f"/api/v1/document/{self.doc_id}/extract", json={})
        resp = client.post(
            f"/api/v1/document/{self.doc_id}/extract",
            json={
                "extractor": {
                    "component": "PlainTextExtractor",
                    "params": {"encoding": "utf-8"},
                }
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["cached"] is False
        assert data["updated"] is True
        assert data["created"] is False

        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            from DashAI.back.dependencies.database.models import (
                ProcessedDocumentContent,
            )

            entries = (
                db.query(ProcessedDocumentContent)
                .filter_by(document_id=self.doc_id)
                .all()
            )
            assert len(entries) == 1

    def test_cascade_on_delete(self, client):
        client.post(f"/api/v1/document/{self.doc_id}/extract", json={})
        session_factory = client.app.container["session_factory"]

        with session_factory() as db:
            from DashAI.back.dependencies.database.models import (
                ProcessedDocumentContent,
            )

            assert (
                db.query(ProcessedDocumentContent)
                .filter_by(document_id=self.doc_id)
                .count()
                >= 1
            )

        resp = client.delete(f"/api/v1/document/{self.doc_id}")
        assert resp.status_code == 204

        with session_factory() as db:
            from DashAI.back.dependencies.database.models import (
                ProcessedDocumentContent,
            )

            assert (
                db.query(ProcessedDocumentContent)
                .filter_by(document_id=self.doc_id)
                .count()
                == 0
            )


class TestExtractionCacheFlowMd:
    """Cache flow tests for .md files (plain text, same extractor as txt)."""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.doc_id = _create_document(
            client, "md", "# DashAI\n\nMarkdown extraction cache test."
        )

    def test_first_extraction_cache_miss(self, client):
        resp = client.post(f"/api/v1/document/{self.doc_id}/extract", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["cached"] is False
        assert "Markdown extraction cache test" in data["text"]

    def test_second_extraction_cache_hit(self, client):
        client.post(f"/api/v1/document/{self.doc_id}/extract", json={})
        resp = client.post(f"/api/v1/document/{self.doc_id}/extract", json={})
        assert resp.status_code == 200
        assert resp.json()["cached"] is True


class TestExtractionCacheFlowPdf:
    """Cache flow tests for .pdf files across all PDF extractors."""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        self.doc_id = _create_document(client, "pdf", b"")

    # ── PypdfExtractor ──

    def test_pypdf2_cache_hit(self, client):
        """PypdfExtractor: cache hit on second extraction."""
        extractor = {"component": "PypdfExtractor", "params": {"strict": False}}
        client.post(
            f"/api/v1/document/{self.doc_id}/extract", json={"extractor": extractor}
        )
        resp = client.post(
            f"/api/v1/document/{self.doc_id}/extract", json={"extractor": extractor}
        )
        assert resp.status_code == 200
        assert resp.json()["cached"] is True

    def test_pypdf2_different_params(self, client):
        """PyMuPDF: different params -> cache miss (no password vs with password)."""
        client.post(
            f"/api/v1/document/{self.doc_id}/extract",
            json={"extractor": {"component": "PyMuPDFExtractor", "params": {}}},
        )
        resp = client.post(
            f"/api/v1/document/{self.doc_id}/extract",
            json={
                "extractor": {
                    "component": "PyMuPDFExtractor",
                    "params": {"password": "test"},
                }
            },
        )
        assert resp.status_code == 200
        assert resp.json()["cached"] is False

    # ── PyMuPDFExtractor ──

    def test_pymupdf_extracts(self, client):
        """PyMuPDFExtractor: should extract from a minimal PDF."""
        resp = client.post(
            f"/api/v1/document/{self.doc_id}/extract",
            json={"extractor": {"component": "PyMuPDFExtractor", "params": {}}},
        )
        assert resp.status_code == 200
        assert "text" in resp.json()
        assert resp.json()["cached"] is False

    def test_pymupdf_cache_hit(self, client):
        """PyMuPDFExtractor: cache hit on second extraction."""
        extractor = {"component": "PyMuPDFExtractor", "params": {}}
        client.post(
            f"/api/v1/document/{self.doc_id}/extract", json={"extractor": extractor}
        )
        resp = client.post(
            f"/api/v1/document/{self.doc_id}/extract", json={"extractor": extractor}
        )
        assert resp.status_code == 200
        assert resp.json()["cached"] is True

    # ── Cross-extractor: different extractors produce different signatures ──

    def test_different_extractors_different_cache(self, client):
        """Different PDF extractors → different signatures → the single row is
        overwritten (1:1)."""
        resp_a = client.post(
            f"/api/v1/document/{self.doc_id}/extract",
            json={
                "extractor": {
                    "component": "PypdfExtractor",
                    "params": {"strict": False},
                }
            },
        )
        resp_b = client.post(
            f"/api/v1/document/{self.doc_id}/extract",
            json={"extractor": {"component": "PyMuPDFExtractor", "params": {}}},
        )
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        assert resp_a.json()["cached"] is False
        assert resp_b.json()["cached"] is False
        assert resp_b.json()["updated"] is True

        # Exactly one cache row remains, holding the latest extraction.
        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            from DashAI.back.dependencies.database.models import (
                ProcessedDocumentContent,
            )

            entries = (
                db.query(ProcessedDocumentContent)
                .filter_by(document_id=self.doc_id)
                .all()
            )
            assert len(entries) == 1

    # ── Incompatible extractor ──

    def test_pdf_extractor_rejected_for_txt(self, client):
        """PDF extractors should be rejected for non-PDF files."""
        txt_id = _create_document(
            client, "txt", "txt content for incompatibility test."
        )
        for component in ("PypdfExtractor", "PyMuPDFExtractor"):
            resp = client.post(
                f"/api/v1/document/{txt_id}/extract",
                json={"extractor": {"component": component, "params": {}}},
            )
            assert resp.status_code == 400, (
                f"{component}: expected 400, got {resp.status_code}"
            )
            assert "does not support" in resp.json()["detail"]


def _create_rag_session(client) -> int:
    """Create an empty RAG session to upload documents into."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = GenerativeSession(
            task_name="RAGTask",
            model_name="RAGPipeline",
            parameters={"documents": []},
            name=f"Test Session {uuid.uuid4().hex[:8]}",
        )
        db.add(session)
        db.commit()
        return session.id


def _upload_document(client, file_name: str, content: bytes, session_id: int):
    """POST a document into a session via the upload endpoint."""
    import json

    metadata = json.dumps(
        {
            "file_name": file_name,
            "optional_metadata": {"name": file_name, "source": "test"},
        }
    )
    return client.post(
        f"/api/v1/document/session/{session_id}",
        files={"file": (file_name, content, "application/octet-stream")},
        data={"metadata": metadata},
    )


class TestDocumentUploadFlow:
    """Upload flow: duplicate detection, force overwrite, extraction errors."""

    def test_duplicate_upload_in_same_session_returns_409(self, client):
        """Re-uploading the same bytes into one session returns 409."""
        session_id = _create_rag_session(client)
        resp1 = _upload_document(client, "dup.txt", b"unique content abc", session_id)
        assert resp1.status_code == 201
        doc_id = resp1.json()["id"]

        resp2 = _upload_document(
            client, "dup_renamed.txt", b"unique content abc", session_id
        )
        assert resp2.status_code == 409
        detail = resp2.json()["detail"]
        assert detail["existing_document"]["id"] == doc_id

    def test_same_file_in_two_sessions_creates_two_documents(self, client):
        """The same bytes in a different session is a separate document.

        Each copy owns its own extractor choice, so changing one must not
        disturb the other. The bytes themselves are stored once, so both rows
        point at the same blob.
        """
        content = b"shared across sessions"
        first = _create_rag_session(client)
        second = _create_rag_session(client)

        resp1 = _upload_document(client, "shared.txt", content, first)
        resp2 = _upload_document(client, "shared.txt", content, second)
        assert resp1.status_code == 201, resp1.text
        assert resp2.status_code == 201, resp2.text

        doc1, doc2 = resp1.json(), resp2.json()
        assert doc1["id"] != doc2["id"]
        assert doc1["session_id"] == first
        assert doc2["session_id"] == second
        assert doc1["file_hash"] == doc2["file_hash"]

    def test_documents_with_the_same_name_do_not_collide(self, client):
        """Two different files sharing a name must both stay readable.

        Files used to be stored under their original name, so the second
        upload silently overwrote the first one's bytes.
        """
        first = _create_rag_session(client)
        second = _create_rag_session(client)

        resp1 = _upload_document(client, "report.txt", b"first report body", first)
        resp2 = _upload_document(client, "report.txt", b"second report body", second)
        assert resp1.status_code == 201, resp1.text
        assert resp2.status_code == 201, resp2.text

        body1 = client.get(f"/api/v1/document/{resp1.json()['id']}/view")
        body2 = client.get(f"/api/v1/document/{resp2.json()['id']}/view")
        assert body1.content == b"first report body"
        assert body2.content == b"second report body"

    def test_duplicate_upload_does_not_modify(self, client):
        """A 409 response must not change the existing document metadata."""
        session_id = _create_rag_session(client)
        resp1 = _upload_document(client, "keep.txt", b"keep this content", session_id)
        assert resp1.status_code == 201
        doc_id = resp1.json()["id"]

        _upload_document(client, "keep_renamed.txt", b"keep this content", session_id)

        resp = client.get(f"/api/v1/document/{doc_id}")
        assert resp.status_code == 200
        assert resp.json()["file_name"] == "keep.txt"

    def test_exactly_one_row_per_document_after_many_extractions(self, client):
        """Multiple extractions always leave exactly one content row."""
        session_id = _create_rag_session(client)
        resp = _upload_document(
            client, "one_row.txt", b"row invariant content", session_id
        )
        assert resp.status_code == 201
        doc_id = resp.json()["id"]

        client.post(f"/api/v1/document/{doc_id}/extract", json={})
        client.post(
            f"/api/v1/document/{doc_id}/extract",
            json={
                "extractor": {
                    "component": "PlainTextExtractor",
                    "params": {"encoding": "utf-8"},
                }
            },
        )
        client.post(
            f"/api/v1/document/{doc_id}/extract",
            json={
                "extractor": {
                    "component": "PlainTextExtractor",
                    "params": {"encoding": "latin-1"},
                }
            },
        )

        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            from DashAI.back.dependencies.database.models import (
                ProcessedDocumentContent,
            )

            count = (
                db.query(ProcessedDocumentContent).filter_by(document_id=doc_id).count()
            )
            assert count == 1

    def test_change_extractor_updates_content_and_invalidates_models(self, client):
        """Changing the extractor updates the single row and wipes RAG artifacts."""
        from DashAI.back.dependencies.database.models import (
            RAGChunkSet,
            RAGChunkSetDocument,
        )

        session_id = _create_rag_session(client)
        resp = _upload_document(
            client, "ext_switch.txt", b"extractor switch text", session_id
        )
        assert resp.status_code == 201
        doc_id = resp.json()["id"]

        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            chunk_set = RAGChunkSet(
                signature=f"cs_{uuid.uuid4().hex[:12]}", parameters={}
            )
            db.add(chunk_set)
            db.flush()
            db.add(RAGChunkSetDocument(chunk_set_id=chunk_set.id, document_id=doc_id))
            db.commit()
            chunk_set_id = chunk_set.id

        # Changing the extractor re-extracts and wipes the chunk set. There is
        # no force flag: a document belongs to one session, so there is nobody
        # else whose index could be destroyed.
        resp = client.put(
            f"/api/v1/document/{doc_id}/extractor",
            json={
                "extractor": {
                    "component": "PlainTextExtractor",
                    "params": {"encoding": "utf-8"},
                },
            },
        )
        assert resp.status_code == 200

        with session_factory() as db:
            from DashAI.back.dependencies.database.models import (
                ProcessedDocumentContent,
            )

            entries = (
                db.query(ProcessedDocumentContent).filter_by(document_id=doc_id).all()
            )
            assert len(entries) == 1
            assert entries[0].content == "extractor switch text"

            assert db.query(RAGChunkSet).get(chunk_set_id) is None
            assert (
                db.query(RAGChunkSetDocument)
                .filter_by(chunk_set_id=chunk_set_id, document_id=doc_id)
                .count()
                == 0
            )

    def test_extraction_failure_during_upload_returns_error(self, client):
        """A file that fails pre-extraction makes the upload return 500."""
        # Invalid UTF-8 bytes cannot be decoded by PlainTextExtractor (utf-8).
        session_id = _create_rag_session(client)
        resp = _upload_document(
            client, "broken.txt", b"caf\xe9 broken bytes", session_id
        )
        assert resp.status_code == 500
        assert "Failed to extract text" in resp.json()["detail"]
