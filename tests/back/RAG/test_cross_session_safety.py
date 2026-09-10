"""What one session's changes must not do to another.

Documents belong to one session, but two of the rows the cleanup path deletes
are keyed by configuration alone -- `rag_chunking_model` and
`rag_embedding_model` -- so every session that settled on the same components
shares them. Since a new session takes the backend defaults, that is the
ordinary case rather than a corner one.
"""

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import (
    Document,
    GenerativeSession,
    RAGChunkingModel,
    RAGPipeline,
)


def _new_session(client: TestClient, name: str) -> int:
    """Create an empty RAG session and return its id."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = GenerativeSession(
            task_name="RAGTask",
            model_name="RAGPipeline",
            parameters={"documents": []},
            name=name,
        )
        db.add(session)
        db.commit()
        return session.id


def _upload(client: TestClient, session_id: int, content: bytes, name: str):
    """Upload one document into a session."""
    metadata = json.dumps({"file_name": name, "optional_metadata": {}})
    return client.post(
        f"/api/v1/document/session/{session_id}",
        files={"file": (name, content, "text/plain")},
        data={"metadata": metadata},
    )


class TestSharedConfigRows:
    """Cleanup must not delete rows another session's pipeline still uses."""

    def test_chunking_model_survives_another_sessions_change(
        self, client: TestClient
    ) -> None:
        """Two sessions on the same chunking share one row; one may re-configure.

        The cross-session guard this replaces compared document lists, which can
        never match now, so it protected nothing.
        """
        tag = uuid.uuid4().hex[:8]
        keeper = _new_session(client, f"keeper_{tag}")
        changer = _new_session(client, f"changer_{tag}")

        chunking = {
            "component": "CharacterChunkModel",
            "params": {"chunk_size": 400, "chunk_overlap": 40},
        }
        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            shared = RAGChunkingModel(
                class_name=chunking["component"], parameters=chunking["params"]
            )
            db.add(shared)
            db.flush()
            # Both sessions' pipelines point at the one row, the way
            # SetupService's lookup-or-create leaves them.
            for session_id in (keeper, changer):
                db.add(
                    RAGPipeline(
                        session_id=session_id,
                        name=f"pipeline_{session_id}",
                        chunking_model_id=shared.id,
                    )
                )
                db.get(GenerativeSession, session_id).parameters = {
                    "documents": [],
                    "chunking_model": chunking,
                }
            db.commit()
            shared_id = shared.id

        response = client.put(
            f"/api/v1/generative-session/{changer}/parameters",
            json={
                "chunking_model": {
                    "component": "CharacterChunkModel",
                    "params": {"chunk_size": 200, "chunk_overlap": 20},
                }
            },
        )
        assert response.status_code == 200, response.text

        with session_factory() as db:
            assert db.get(RAGChunkingModel, shared_id) is not None, (
                "the other session's pipeline still points at this row"
            )

    def test_chunking_model_goes_once_nothing_uses_it(self, client: TestClient) -> None:
        """The guard must not turn into a leak: a truly orphaned row is dropped."""
        tag = uuid.uuid4().hex[:8]
        lonely = _new_session(client, f"lonely_{tag}")

        chunking = {
            "component": "CharacterChunkModel",
            "params": {"chunk_size": 411, "chunk_overlap": 41},
        }
        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            row = RAGChunkingModel(
                class_name=chunking["component"], parameters=chunking["params"]
            )
            db.add(row)
            db.flush()
            db.add(
                RAGPipeline(
                    session_id=lonely,
                    name=f"pipeline_{lonely}",
                    chunking_model_id=row.id,
                )
            )
            db.get(GenerativeSession, lonely).parameters = {
                "documents": [],
                "chunking_model": chunking,
            }
            db.commit()
            row_id = row.id

        response = client.put(
            f"/api/v1/generative-session/{lonely}/parameters",
            json={
                "chunking_model": {
                    "component": "CharacterChunkModel",
                    "params": {"chunk_size": 222, "chunk_overlap": 22},
                }
            },
        )
        assert response.status_code == 200, response.text

        with session_factory() as db:
            pipeline = db.query(RAGPipeline).filter_by(session_id=lonely).one_or_none()
            # The pipeline is repointed or cleared; either way nothing references
            # the old row, so it should not linger.
            still_referenced = pipeline is not None and (
                pipeline.chunking_model_id == row_id
            )
            if not still_referenced:
                assert db.get(RAGChunkingModel, row_id) is None


class TestUploadRollback:
    """A failed upload must not leave the session holding a text-less document."""

    def test_failed_extraction_leaves_no_document_behind(
        self, client: TestClient
    ) -> None:
        """Undecodable bytes fail extraction; the session must stay as it was."""
        tag = uuid.uuid4().hex[:8]
        session_id = _new_session(client, f"rollback_{tag}")

        # Invalid UTF-8, which PlainTextExtractor cannot decode.
        response = _upload(
            client, session_id, b"caf\xe9 broken bytes", f"broken_{tag}.txt"
        )
        assert response.status_code == 500, response.text

        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            assert db.query(Document).filter_by(session_id=session_id).count() == 0, (
                "a document with no extractable text was left in the session"
            )
            session = db.get(GenerativeSession, session_id)
            assert session.parameters.get("documents") == []

        listed = client.get(f"/api/v1/document/session/{session_id}")
        assert listed.status_code == 200
        assert listed.json() == []

    def test_a_good_upload_still_lands(self, client: TestClient) -> None:
        """The rollback must not swallow successful uploads."""
        tag = uuid.uuid4().hex[:8]
        session_id = _new_session(client, f"rollback_ok_{tag}")

        response = _upload(client, session_id, b"readable text", f"ok_{tag}.txt")
        assert response.status_code == 201, response.text

        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            assert db.query(Document).filter_by(session_id=session_id).count() == 1
            session = db.get(GenerativeSession, session_id)
            assert session.parameters["documents"] == [response.json()["id"]]


class TestBulkDeleteAtomicity:
    """Deleting several sessions is one transaction, files included."""

    @pytest.mark.parametrize("count", [2])
    def test_bulk_delete_removes_every_session_and_its_files(
        self, client: TestClient, count: int
    ) -> None:
        """The happy path still works with deletion deferred past the commit."""
        import os

        tag = uuid.uuid4().hex[:8]
        session_ids = []
        paths = []
        for index in range(count):
            session_id = _new_session(client, f"bulk_{tag}_{index}")
            response = _upload(
                client,
                session_id,
                f"bulk body {index}".encode(),
                f"b_{tag}_{index}.txt",
            )
            assert response.status_code == 201, response.text
            session_ids.append(session_id)
            session_factory = client.app.container["session_factory"]
            with session_factory() as db:
                paths.append(db.get(Document, response.json()["id"]).file_path)

        for path in paths:
            assert os.path.exists(path)

        response = client.request(
            "DELETE", "/api/v1/generative-session/", json={"ids": session_ids}
        )
        assert response.status_code in (200, 204), response.text

        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            for session_id in session_ids:
                assert db.get(GenerativeSession, session_id) is None
                assert db.query(Document).filter_by(session_id=session_id).count() == 0
        for path in paths:
            assert not os.path.exists(path), "the blob outlived its only document"
