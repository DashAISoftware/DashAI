"""Attaching Data documents to RAG sessions through the API."""

import uuid
from pathlib import Path

from DashAI.back.core.enums.status import DocumentStatus
from DashAI.back.dependencies.database.models import (
    DataDocument,
    RAGChunkSet,
    RAGChunkSetDocument,
)
from tests.back.RAG.conftest import (
    _create_data_document,
    _create_holder_session,
    _insert_data_document,
)


def _url(session_id, document_id=None) -> str:
    """Build the session documents URL.

    Parameters
    ----------
    session_id : int
        The RAG session.
    document_id : int, optional
        A document, for the detach URL.

    Returns
    -------
    str
        The endpoint path.
    """
    base = f"/api/v1/rag/sessions/{session_id}/documents"
    return base if document_id is None else f"{base}/{document_id}"


def _session(client) -> int:
    """Create an empty RAG session with a unique name.

    Parameters
    ----------
    client : TestClient
        Client of the app under test.

    Returns
    -------
    int
        The session id.
    """
    return _create_holder_session(client, f"api_docs_{uuid.uuid4().hex[:8]}")


def _owned_chunk_set(client, session_id, document_id) -> int:
    """Insert a chunk set of a session over one document.

    Parameters
    ----------
    client : TestClient
        Client of the app under test.
    session_id : int
        Owning session.
    document_id : int
        Member document.

    Returns
    -------
    int
        The chunk set id.
    """
    with client.app.container["session_factory"]() as db:
        chunk_set = RAGChunkSet(
            signature=uuid.uuid4().hex, parameters={}, session_id=session_id
        )
        db.add(chunk_set)
        db.flush()
        db.add(RAGChunkSetDocument(chunk_set_id=chunk_set.id, document_id=document_id))
        db.commit()
        return chunk_set.id


def test_attaching_lists_and_mirrors_the_document(client):
    session_id = _session(client)
    document_id = _create_data_document(client, text="attach me")

    response = client.post(_url(session_id), json={"document_ids": [document_id]})

    assert response.status_code == 200, response.text
    assert [row["id"] for row in response.json()] == [document_id]
    assert response.json()[0]["status"] == DocumentStatus.FINISHED.value
    assert [row["id"] for row in client.get(_url(session_id)).json()] == [document_id]
    session = client.get(f"/api/v1/generative-session/{session_id}").json()
    assert session["parameters"]["documents"] == [document_id]


def test_attaching_unknown_or_unready_documents_is_refused(client):
    session_id = _session(client)
    config = client.app.container["config"]
    with client.app.container["session_factory"]() as db:
        pending_id = _insert_data_document(
            db,
            Path(config["DOCUMENTS_PATH"]),
            f"pending_{uuid.uuid4().hex[:8]}.txt",
            ["x"],
            status=DocumentStatus.STARTED,
        ).id

    assert (
        client.post(_url(session_id), json={"document_ids": [987654]}).status_code
        == 404
    )
    assert (
        client.post(_url(session_id), json={"document_ids": [pending_id]}).status_code
        == 409
    )
    assert client.post(_url(session_id), json={"document_ids": []}).status_code == 422
    assert client.get(_url(987654)).status_code == 404


def test_detaching_keeps_the_document_in_data(client):
    session_id = _session(client)
    document_id = _create_data_document(client, text="detach me")
    client.post(_url(session_id), json={"document_ids": [document_id]})

    assert client.delete(_url(session_id, document_id)).status_code == 204
    assert client.get(_url(session_id)).json() == []
    assert client.delete(_url(session_id, document_id)).status_code == 404
    with client.app.container["session_factory"]() as db:
        assert db.get(DataDocument, document_id) is not None


def test_detaching_from_one_session_keeps_the_other_sessions_index(client):
    first, second = _session(client), _session(client)
    document_id = _create_data_document(client, text="shared")
    client.post(_url(first), json={"document_ids": [document_id]})
    client.post(_url(second), json={"document_ids": [document_id]})
    first_set = _owned_chunk_set(client, first, document_id)
    second_set = _owned_chunk_set(client, second, document_id)

    assert client.delete(_url(first, document_id)).status_code == 204

    with client.app.container["session_factory"]() as db:
        assert db.get(RAGChunkSet, first_set) is None
        assert db.get(RAGChunkSet, second_set) is not None
    assert [row["id"] for row in client.get(_url(second)).json()] == [document_id]


def test_deleting_a_session_keeps_the_document_and_other_links(client):
    first, second = _session(client), _session(client)
    document_id = _create_data_document(client, text="survivor")
    client.post(_url(first), json={"document_ids": [document_id]})
    client.post(_url(second), json={"document_ids": [document_id]})
    second_set = _owned_chunk_set(client, second, document_id)

    assert client.delete(f"/api/v1/generative-session/{first}").status_code == 204

    with client.app.container["session_factory"]() as db:
        assert db.get(DataDocument, document_id) is not None
        assert db.get(RAGChunkSet, second_set) is not None
    assert [row["id"] for row in client.get(_url(second)).json()] == [document_id]
