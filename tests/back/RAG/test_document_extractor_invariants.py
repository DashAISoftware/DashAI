"""Invariants of changing a document's extractor.

Committing an extractor choice re-extracts the text and throws away everything
fitted over the previous extraction. These tests pin down the three properties
that used to be missing: it happens unconditionally, it is atomic, and doing it
twice with the same configuration is a no-op.
"""

import json
import os
import uuid
from typing import ClassVar, Final, List

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.dependencies.database.models import (
    Chunk,
    GenerativeSession,
    ProcessedDocumentContent,
    RAGChunkSet,
    RAGChunkSetDocument,
    RAGExtractor,
)
from DashAI.back.models.RAG.extractors.base_extractor import BaseExtractor


class ExplodingExtractorSchema(BaseSchema):
    """Empty schema — the stub takes no parameters."""


class ExplodingExtractor(BaseExtractor):
    """An extractor that always fails, standing in for a malformed file."""

    TYPE: Final[str] = "Extractor"
    SCHEMA: ClassVar[BaseSchema] = ExplodingExtractorSchema
    SUPPORTED_FILE_TYPES: List[str] = ["txt"]

    def __init__(self, **kwargs):
        """Accept and ignore any parameters."""

    def extract(self, file_path: str) -> str:
        """Fail the way a broken PDF would."""
        raise OSError("cannot read this file")


@pytest.fixture(scope="module", autouse=True)
def register_exploding_extractor(client: TestClient) -> None:
    """Make the failing extractor selectable through the API."""
    client.app.container["component_registry"].register_component(ExplodingExtractor)


def _upload(client: TestClient, content: bytes) -> dict:
    """Create a session and upload one txt document into it."""
    tag = uuid.uuid4().hex[:8]
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = GenerativeSession(
            task_name="RAGTask",
            model_name="RAGPipeline",
            parameters={"documents": []},
            name=f"extractor_invariants_{tag}",
        )
        db.add(session)
        db.commit()
        session_id = session.id

    metadata = json.dumps({"file_name": f"doc_{tag}.txt", "optional_metadata": {}})
    response = client.post(
        f"/api/v1/document/session/{session_id}",
        files={"file": (f"doc_{tag}.txt", content, "text/plain")},
        data={"metadata": metadata},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _give_it_a_chunk_set(client: TestClient, document_id: int) -> int:
    """Attach a chunk set with one chunk, standing in for a built index."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        chunk_set = RAGChunkSet(signature=f"cs_{uuid.uuid4().hex[:12]}", parameters={})
        db.add(chunk_set)
        db.flush()
        db.add(RAGChunkSetDocument(chunk_set_id=chunk_set.id, document_id=document_id))
        db.add(
            Chunk(
                chunk_set_id=chunk_set.id,
                document_id=document_id,
                chunk_index=0,
                text="a chunk of the old extraction",
            )
        )
        db.commit()
        return chunk_set.id


def _put_extractor(client: TestClient, document_id: int, component: str, **params):
    """Commit an extractor choice for a document."""
    return client.put(
        f"/api/v1/document/{document_id}/extractor",
        json={"extractor": {"component": component, "params": params}},
    )


def test_changing_the_extractor_invalidates_the_index(client: TestClient):
    """Chunks fitted over the old extraction go, with no confirmation step.

    The old ``force`` flag guarded this, but it asked a table nothing ever
    wrote to which sessions were affected, so it never triggered.
    """
    document = _upload(client, b"invalidation subject")
    chunk_set_id = _give_it_a_chunk_set(client, document["id"])

    response = _put_extractor(
        client, document["id"], "PlainTextExtractor", encoding="latin-1"
    )
    assert response.status_code == 200, response.text

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        assert db.get(RAGChunkSet, chunk_set_id) is None
        assert db.query(Chunk).filter_by(chunk_set_id=chunk_set_id).count() == 0


def test_a_failing_extraction_changes_nothing(client: TestClient):
    """The document keeps its extractor, its text and its index.

    The extractor id used to be committed before re-extracting, so a failure
    left the document pointing at an extractor that had never produced its
    text, still serving the previous extractor's chunks.
    """
    document = _upload(client, b"atomicity subject")
    chunk_set_id = _give_it_a_chunk_set(client, document["id"])
    before = document["extractor"]

    response = _put_extractor(client, document["id"], "ExplodingExtractor")
    assert response.status_code == 422, response.text

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        cached = (
            db.query(ProcessedDocumentContent)
            .filter_by(document_id=document["id"])
            .one()
        )
        assert cached.content == "atomicity subject"
        assert db.get(RAGChunkSet, chunk_set_id) is not None

    current = client.get(f"/api/v1/document/{document['id']}").json()
    assert current["extractor"] == before


def test_recommitting_the_same_extractor_is_a_no_op(client: TestClient):
    """Saving an unchanged choice must not throw away a good index.

    With invalidation now unconditional, pressing Save without changing
    anything would otherwise re-index the whole session for nothing.
    """
    document = _upload(client, b"idempotence subject")
    stored = document["extractor"]
    chunk_set_id = _give_it_a_chunk_set(client, document["id"])

    response = _put_extractor(
        client, document["id"], stored["component"], **stored["params"]
    )
    assert response.status_code == 200, response.text

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        assert db.get(RAGChunkSet, chunk_set_id) is not None


def test_extractor_records_are_reused(client: TestClient):
    """One configuration means one ``rag_extractor`` row, not one per save.

    Every commit used to insert a new row, and none of them could be removed
    while any document still referenced one.
    """
    first = _upload(client, b"dedup subject one")
    second = _upload(client, b"dedup subject two")

    def rows() -> int:
        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            return (
                db.query(RAGExtractor)
                .filter_by(component_name="PlainTextExtractor")
                .filter(RAGExtractor.params == {"encoding": "cp1252"})
                .count()
            )

    for document in (first, second):
        assert (
            _put_extractor(
                client, document["id"], "PlainTextExtractor", encoding="cp1252"
            ).status_code
            == 200
        )

    assert rows() == 1


def test_previewing_twice_hits_the_cache(client: TestClient):
    """A second preview is cached, and does not destroy the index.

    ``extract_text`` used to build its cache signature from empty params while
    instantiating the extractor with the stored ones, so the signature never
    matched itself: every preview missed the cache and re-invalidated the
    index.
    """
    document = _upload(client, b"signature subject")
    assert (
        _put_extractor(
            client, document["id"], "PlainTextExtractor", encoding="latin-1"
        ).status_code
        == 200
    )
    chunk_set_id = _give_it_a_chunk_set(client, document["id"])

    first = client.post(f"/api/v1/document/{document['id']}/extract", json={})
    assert first.status_code == 200, first.text
    second = client.post(f"/api/v1/document/{document['id']}/extract", json={})
    assert second.status_code == 200, second.text
    assert second.json()["cached"] is True, second.json()

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        assert db.get(RAGChunkSet, chunk_set_id) is not None


def test_deleting_a_document_takes_its_artifacts(client: TestClient):
    """Deleting a document removes its chunks, its blob and its extractor row."""
    document = _upload(client, b"deletion subject")
    chunk_set_id = _give_it_a_chunk_set(client, document["id"])

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        from DashAI.back.dependencies.database.models import Document

        file_path = db.get(Document, document["id"]).file_path
    assert os.path.exists(file_path)

    response = client.delete(f"/api/v1/document/{document['id']}")
    assert response.status_code == 204, response.text

    with session_factory() as db:
        assert db.get(RAGChunkSet, chunk_set_id) is None
        assert (
            db.query(ProcessedDocumentContent)
            .filter_by(document_id=document["id"])
            .count()
            == 0
        )
        assert (
            db.query(RAGChunkSetDocument).filter_by(document_id=document["id"]).count()
            == 0
        )
    assert not os.path.exists(file_path)


def test_a_shared_blob_survives_deleting_one_copy(client: TestClient):
    """Two sessions holding the same file share one blob, deleted once.

    The bytes are stored content-addressed, so removing one session's copy
    must not pull the file out from under the other.
    """
    content = b"shared blob subject"
    first = _upload(client, content)
    second = _upload(client, content)
    assert first["id"] != second["id"]

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        from DashAI.back.dependencies.database.models import Document

        path_one = db.get(Document, first["id"]).file_path
        path_two = db.get(Document, second["id"]).file_path
    assert path_one == path_two, "identical content should resolve to one blob"

    assert client.delete(f"/api/v1/document/{first['id']}").status_code == 204
    assert os.path.exists(path_two), "the surviving document lost its file"

    still_readable = client.get(f"/api/v1/document/{second['id']}/view")
    assert still_readable.status_code == 200
    assert still_readable.content == content

    assert client.delete(f"/api/v1/document/{second['id']}").status_code == 204
    assert not os.path.exists(path_two)


def test_documents_go_when_their_session_does(client: TestClient):
    """Deleting a session removes its documents and their files."""
    document = _upload(client, b"session deletion subject")
    session_id = document["session_id"]

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        from DashAI.back.dependencies.database.models import Document

        file_path = db.get(Document, document["id"]).file_path

    response = client.delete(f"/api/v1/generative-session/{session_id}")
    assert response.status_code in (200, 204), response.text

    with session_factory() as db:
        from DashAI.back.dependencies.database.models import Document

        assert db.get(Document, document["id"]) is None
    assert not os.path.exists(file_path)


def test_chatting_without_documents_is_refused(client: TestClient):
    """An empty session says so, instead of failing inside the retriever."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = GenerativeSession(
            task_name="RAGTask",
            model_name="RAGPipeline",
            parameters={"documents": []},
            name=f"empty_session_{uuid.uuid4().hex[:8]}",
        )
        db.add(session)
        db.commit()
        session_id = session.id

    response = client.post(
        "/api/v1/generative-process/",
        data={"session_id": str(session_id), "input_0": "what does it say?"},
    )
    assert response.status_code == 400, response.text
    assert "document" in response.json()["detail"].lower()


def test_index_status_reports_an_empty_session(client: TestClient):
    """A session with no documents is not merely "not indexed" yet."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = GenerativeSession(
            task_name="RAGTask",
            model_name="RAGPipeline",
            parameters={"documents": []},
            name=f"status_session_{uuid.uuid4().hex[:8]}",
        )
        db.add(session)
        db.commit()
        session_id = session.id

    response = client.get(f"/api/v1/rag/sessions/{session_id}/index-status")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "no_documents", body
    assert body["message"]


def test_uploading_into_a_non_rag_session_is_refused(client: TestClient):
    """Only RAG sessions hold documents."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = GenerativeSession(
            task_name="TextToTextGenerationTask",
            model_name="SomeModel",
            parameters={},
            name=f"not_rag_{uuid.uuid4().hex[:8]}",
        )
        db.add(session)
        db.commit()
        session_id = session.id

    metadata = json.dumps({"file_name": "nope.txt", "optional_metadata": {}})
    response = client.post(
        f"/api/v1/document/session/{session_id}",
        files={"file": ("nope.txt", b"not for you", "text/plain")},
        data={"metadata": metadata},
    )
    assert response.status_code == 400, response.text


def test_upload_writes_a_content_addressed_blob(client: TestClient):
    """Files are named by content hash, so equal names cannot collide."""
    document = _upload(client, b"blob naming subject")
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        from DashAI.back.dependencies.database.models import Document

        stored = db.get(Document, document["id"])
        assert os.path.basename(stored.file_path) == stored.file_hash
        assert os.path.basename(os.path.dirname(stored.file_path)) == "blobs"
