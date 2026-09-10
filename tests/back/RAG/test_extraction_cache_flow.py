"""Integration tests for document extraction with processed_document_content cache.

Verifies the full flow across txt, md, and pdf file types:
extraction → cache hit/miss → signature invalidation when extractor config changes.
"""

import os
import tempfile
import uuid

import pytest

from DashAI.back.dependencies.database.models import Document, RAGExtractor

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
        extractor = RAGExtractor(
            component_name=_EXTRACTOR_BY_FILE_TYPE[file_type], params={}
        )
        db.add(extractor)
        db.flush()
        doc = Document(
            file_name=f"test_cache.{ext}",
            file_type=file_type,
            file_path=tmp_path,
            file_hash=unique_hash,
            extractor_id=extractor.id,
        )
        db.add(doc)
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


def _upload_document(client, file_name: str, content: bytes, force: bool = False):
    """POST a document via the upload endpoint."""
    import json

    metadata = json.dumps(
        {
            "file_name": file_name,
            "optional_metadata": {"name": file_name, "source": "test"},
        }
    )
    return client.post(
        "/api/v1/document/",
        files={"file": (file_name, content, "application/octet-stream")},
        data={"metadata": metadata},
        params={"force": "true"} if force else {},
    )


def _link_document_to_session(client, doc_id: int) -> int:
    """Link a document to a RAG session+pipeline and return the session id."""
    from DashAI.back.dependencies.database.models import (
        GenerativeSession,
        RAGDocumentPipelineSessionLink,
        RAGPipeline,
    )

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = GenerativeSession(
            task_name="RAGTask",
            model_name="RAGPipeline",
            parameters={"documents": [doc_id]},
            name=f"Test Session {uuid.uuid4().hex[:8]}",
        )
        db.add(session)
        db.flush()
        pipeline = RAGPipeline(session_id=session.id, name="Test Pipeline")
        db.add(pipeline)
        db.flush()
        db.add(
            RAGDocumentPipelineSessionLink(
                document_id=doc_id,
                session_id=session.id,
                pipeline_id=pipeline.id,
            )
        )
        db.commit()
        return session.id


class TestDocumentUploadFlow:
    """Upload flow: duplicate detection, force overwrite, extraction errors."""

    def test_duplicate_upload_returns_409(self, client):
        """Re-uploading the same file returns 409 with existing doc + sessions."""
        resp1 = _upload_document(client, "dup.txt", b"unique content abc")
        assert resp1.status_code == 201
        doc_id = resp1.json()["id"]
        session_id = _link_document_to_session(client, doc_id)

        resp2 = _upload_document(client, "dup_renamed.txt", b"unique content abc")
        assert resp2.status_code == 409
        body = resp2.json()
        detail = body["detail"]
        assert detail["detail"] == "Document already exists"
        assert detail["existing_document"]["id"] == doc_id
        assert session_id in {s["id"] for s in detail["affected_sessions"]}

    def test_duplicate_upload_without_force_does_not_modify(self, client):
        """A 409 response must not change the existing document metadata."""
        resp1 = _upload_document(client, "keep.txt", b"keep this content")
        assert resp1.status_code == 201
        doc_id = resp1.json()["id"]

        _upload_document(client, "keep_renamed.txt", b"keep this content")

        resp = client.get(f"/api/v1/document/{doc_id}")
        assert resp.status_code == 200
        assert resp.json()["file_name"] == "keep.txt"

    def test_duplicate_upload_force_updates_content(self, client):
        """Uploading the same file with force=true overwrites and re-extracts."""
        resp1 = _upload_document(client, "force.txt", b"force overwrite me")
        assert resp1.status_code == 201
        doc_id = resp1.json()["id"]

        resp2 = _upload_document(
            client, "force_renamed.txt", b"force overwrite me", force=True
        )
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["id"] == doc_id
        assert data["file_name"] == "force_renamed.txt"

        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            from DashAI.back.dependencies.database.models import (
                ProcessedDocumentContent,
            )

            entries = (
                db.query(ProcessedDocumentContent).filter_by(document_id=doc_id).all()
            )
            assert len(entries) == 1

    def test_exactly_one_row_per_document_after_many_extractions(self, client):
        """Multiple extractions always leave exactly one content row."""
        resp = _upload_document(client, "one_row.txt", b"row invariant content")
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

        resp = _upload_document(client, "ext_switch.txt", b"extractor switch text")
        assert resp.status_code == 201
        doc_id = resp.json()["id"]
        _link_document_to_session(client, doc_id)

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

        # Change extractor with force → content re-extracted, chunk set wiped.
        resp = client.put(
            f"/api/v1/document/{doc_id}/extractor",
            json={
                "extractor": {
                    "component": "PlainTextExtractor",
                    "params": {"encoding": "utf-8"},
                },
                "force": True,
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
        resp = _upload_document(client, "broken.txt", b"caf\xe9 broken bytes")
        assert resp.status_code == 500
        assert "Failed to extract text" in resp.json()["detail"]
