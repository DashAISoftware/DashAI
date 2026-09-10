"""Tests for eager RAG indexing: the job, the endpoint, and the status it reports.

Indexing used to happen inside the chat job, so the first message paid for the
whole chunking and embedding run. It now runs up front, as ``RAGIndexJob``,
started through ``POST /rag/sessions/{id}/index``. What these tests pin is the
part that is easy to get wrong: the job must not touch the generation model,
the endpoint must not enqueue work twice, and the status must stay honest when
the job pointer goes stale.
"""

import contextlib
import os
import sqlite3
import tempfile
import uuid

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.dependencies.database.models import GenerativeSession
from DashAI.back.job.base_job import JobError
from DashAI.back.job.RAG_index_job import RAGIndexJob
from DashAI.back.models.RAG.RAG_constants import RAG_PARAM_KEYS
from DashAI.back.models.RAG.RAG_models_factory import RAGModelsFactory
from DashAI.back.models.RAG.RAG_pipeline import RAGPipelineConfig
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from DashAI.back.services.RAG.setup_service import SetupService
from tests.back.RAG.conftest import RAG_E2E_DOC_TEXT, _add_document_to_session


class StubIndexLLMSchema(BaseSchema):
    """Empty schema — the stub model accepts any (empty) parameter set."""


class StubIndexLLM(TextToTextGenerationTaskModel):
    """Deterministic model, so indexing tests never run real inference."""

    SCHEMA = StubIndexLLMSchema

    def __init__(self, **kwargs):
        """Store parameters without initialising the base class."""
        self.parameters = {}

    def generate(self, prompt):
        """Return a fixed stub answer."""
        return ["stub answer"]


@pytest.fixture(scope="module", autouse=True)
def _register_stub_llm(client: TestClient):
    """Register the stub generation model for this module's sessions."""
    registry = client.app.container["component_registry"]
    if "StubIndexLLM" not in registry:
        registry.register_component(StubIndexLLM)
    return


@pytest.fixture
def written_documents() -> list:
    """Collect the document files written by a test, and clean them up."""
    paths: list = []
    yield paths
    for path in paths:
        with contextlib.suppress(OSError):
            os.remove(path)


def _attach_indexable_document(
    client: TestClient, session_id: int, written_documents: list
) -> int:
    """Add a document to a session, with a real file the pipeline can chunk."""
    suffix = f"_index_{uuid.uuid4().hex[:8]}"
    doc_id = _add_document_to_session(client, session_id, suffix=suffix)
    path = os.path.join(tempfile.gettempdir(), f"test_doc{suffix}.txt")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(RAG_E2E_DOC_TEXT)
    written_documents.append(path)
    return doc_id


def _create_session(client: TestClient, name: str) -> int:
    """Create an empty RAG session wired to the stub generation model."""
    response = client.post(
        "/api/v1/generative-session/",
        json={
            "model_name": "RAGPipeline",
            "task_name": "RAGTask",
            "name": f"{name}_{uuid.uuid4().hex[:8]}",
            "parameters": {
                "generation_model": {"component": "StubIndexLLM", "params": {}},
            },
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_session_with_document(
    client: TestClient, name: str, written_documents: list
) -> "tuple[int, int]":
    session_id = _create_session(client, name)
    document_id = _attach_indexable_document(client, session_id, written_documents)
    return session_id, document_id


@contextlib.contextmanager
def _setup_service(client: TestClient, session_id: int):
    """Yield ``(service, make_config)`` for a session, sharing one DB session.

    ``RAGPipelineConfig`` holds the live SQLAlchemy session, so the config and
    the service it is passed to have to be built inside the same ``with``.
    """
    container = client.app.container
    with container["session_factory"]() as db:

        def make_config() -> RAGPipelineConfig:
            session = db.get(GenerativeSession, session_id)
            clean = {
                k: v
                for k, v in dict(session.parameters or {}).items()
                if k in RAG_PARAM_KEYS
            }
            return RAGPipelineConfig.from_kwargs(
                db=db,
                component_registry=container["component_registry"],
                session_id=session_id,
                env_RAG_path=container["config"]["RAG_PATH"],
                **clean,
            )

        yield (
            SetupService(
                db,
                container["component_registry"],
                container["config"]["RAG_PATH"],
            ),
            make_config,
        )


def _queue_rows(client: TestClient) -> list:
    """Read the job queue's task_copy rows directly."""
    return client.app.container["job_queue"].to_list()


# ===================================================================
# build_index — the indexing half of the pipeline
# ===================================================================


def test_build_index_never_builds_the_generation_model(
    client: TestClient, written_documents: list, monkeypatch: pytest.MonkeyPatch
):
    """The whole point of splitting build_index out of build_pipeline.

    Indexing that instantiated the LLM would load model weights it never uses,
    which is exactly the cost this change exists to avoid.
    """
    session_id, _ = _create_session_with_document(
        client, "index_no_llm", written_documents
    )

    def _explode(*args, **kwargs):
        raise AssertionError("build_index must not instantiate the generation model")

    monkeypatch.setattr(RAGModelsFactory, "create_llm", _explode)

    with _setup_service(client, session_id) as (service, make_config):
        result = service.build_index(make_config())

    assert result.total_chunks > 0
    assert result.chunk_set_id
    assert result.retriever.model is not None


def test_build_index_reports_progress_monotonically(
    client: TestClient, written_documents: list
):
    session_id, _ = _create_session_with_document(
        client, "index_progress", written_documents
    )
    seen: list = []

    with _setup_service(client, session_id) as (service, make_config):
        service.build_index(make_config(), progress=lambda f, m: seen.append((f, m)))

    fractions = [f for f, _ in seen]
    assert fractions, "build_index reported no progress at all"
    assert fractions == sorted(fractions)
    assert fractions[-1] == 1.0
    assert all(message for _, message in seen)


def test_build_pipeline_reuses_what_build_index_created(
    client: TestClient, written_documents: list
):
    """The two paths must not drift: build_pipeline delegates, it does not redo."""
    session_id, _ = _create_session_with_document(
        client, "index_shared_path", written_documents
    )

    with _setup_service(client, session_id) as (service, make_config):
        indexed = service.build_index(make_config())
        pipeline = service.build_pipeline(make_config())

    assert pipeline.pipeline_id == indexed.pipeline_id
    assert pipeline.chunking_model_id == indexed.chunking_model_id

    data = client.get(f"/api/v1/rag/sessions/{session_id}/index-status").json()
    assert data["status"] == "indexed", data
    assert data["total_chunks"] == indexed.total_chunks


# ===================================================================
# RAGIndexJob
# ===================================================================


def test_index_job_makes_a_session_indexed(client: TestClient, written_documents: list):
    session_id, _ = _create_session_with_document(
        client, "index_job_run", written_documents
    )

    before = client.get(f"/api/v1/rag/sessions/{session_id}/index-status").json()
    assert before["status"] == "not_indexed", before

    RAGIndexJob(session_id=session_id).run()

    after = client.get(f"/api/v1/rag/sessions/{session_id}/index-status").json()
    assert after["status"] == "indexed", after
    assert after["total_chunks"] > 0
    assert after["retriever_ready"] is True


def test_index_job_refuses_a_session_with_no_documents(client: TestClient):
    session_id = _create_session(client, "index_job_empty")

    with pytest.raises(JobError, match="no documents"):
        RAGIndexJob(session_id=session_id).run()


def test_index_job_refuses_an_unknown_session(client: TestClient):
    with pytest.raises(JobError, match="not found"):
        RAGIndexJob(session_id=999999).run()


def test_index_job_names_itself_after_the_session(client: TestClient):
    session_id = _create_session(client, "index_job_naming")
    name = RAGIndexJob(session_id=session_id).get_job_name()
    assert name.startswith("Indexing: index_job_naming")


# ===================================================================
# The index endpoint
# ===================================================================


def test_index_endpoint_indexes_a_fresh_session(
    client: TestClient, written_documents: list
):
    session_id, _ = _create_session_with_document(
        client, "index_endpoint", written_documents
    )

    response = client.post(f"/api/v1/rag/sessions/{session_id}/index")
    assert response.status_code == 202, response.text

    # The queue runs jobs immediately in tests, so the work is already done.
    data = client.get(f"/api/v1/rag/sessions/{session_id}/index-status").json()
    assert data["status"] == "indexed", data
    assert data["total_chunks"] > 0


def test_index_endpoint_is_a_no_op_without_documents(client: TestClient):
    session_id = _create_session(client, "index_endpoint_empty")
    before = len(_queue_rows(client))

    response = client.post(f"/api/v1/rag/sessions/{session_id}/index")
    assert response.status_code == 202, response.text
    assert response.json()["status"] == "no_documents"
    assert response.json()["job_id"] is None
    assert len(_queue_rows(client)) == before

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        assert db.get(GenerativeSession, session_id).index_job_id is None


def test_index_endpoint_short_circuits_when_already_indexed(
    client: TestClient, written_documents: list
):
    session_id, _ = _create_session_with_document(
        client, "index_endpoint_twice", written_documents
    )

    assert client.post(f"/api/v1/rag/sessions/{session_id}/index").status_code == 202
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        first_job = db.get(GenerativeSession, session_id).index_job_id
    assert first_job

    # Nothing changed, so the second call must not queue a second run.
    response = client.post(f"/api/v1/rag/sessions/{session_id}/index")
    assert response.status_code == 202, response.text
    assert response.json()["status"] == "indexed"

    with session_factory() as db:
        assert db.get(GenerativeSession, session_id).index_job_id == first_job


def test_index_endpoint_404s_for_an_unknown_session(client: TestClient):
    assert client.post("/api/v1/rag/sessions/999999/index").status_code == 404


# ===================================================================
# Status reporting around a live / stale job pointer
# ===================================================================


def _write_queue_row(client: TestClient, job_id: str, status: str) -> None:
    """Insert a task_copy row by hand.

    Far simpler than orchestrating a genuinely slow job, and it exercises the
    exact thing the status service reads.
    """
    queue = client.app.container["job_queue"]
    with sqlite3.connect(queue.db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO task_copy "
            "(id, task_type, job_name, enqueued_at, status, last_update, progress) "
            "VALUES (?, ?, ?, STRFTIME('%Y-%m-%d %H:%M:%f','now'), ?, "
            "STRFTIME('%Y-%m-%d %H:%M:%f','now'), ?)",
            (job_id, "RAGIndexJob", "Indexing: test", status, 42.0),
        )


def _point_session_at_job(client: TestClient, session_id: int, job_id) -> None:
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.get(GenerativeSession, session_id).index_job_id = job_id
        db.commit()


@pytest.mark.parametrize("queue_status", ["not_started", "started"])
def test_status_reports_indexing_while_the_job_is_live(
    client: TestClient, written_documents: list, queue_status: str
):
    session_id, _ = _create_session_with_document(
        client, f"index_live_{queue_status}", written_documents
    )
    job_id = f"live-{queue_status}-{uuid.uuid4().hex[:8]}"
    _write_queue_row(client, job_id, queue_status)
    _point_session_at_job(client, session_id, job_id)

    data = client.get(f"/api/v1/rag/sessions/{session_id}/index-status").json()
    assert data["status"] == "indexing", data
    assert data["job_id"] == job_id
    assert data["job"]["progress"] == 42.0


def test_indexing_beats_indexed_so_a_reindex_is_not_reported_as_done(
    client: TestClient, written_documents: list
):
    """A re-index finds the old rows still in place; saying "ready" would lie."""
    session_id, _ = _create_session_with_document(
        client, "index_precedence", written_documents
    )
    assert client.post(f"/api/v1/rag/sessions/{session_id}/index").status_code == 202
    assert (
        client.get(f"/api/v1/rag/sessions/{session_id}/index-status").json()["status"]
        == "indexed"
    )

    job_id = f"live-again-{uuid.uuid4().hex[:8]}"
    _write_queue_row(client, job_id, "started")
    _point_session_at_job(client, session_id, job_id)

    data = client.get(f"/api/v1/rag/sessions/{session_id}/index-status").json()
    assert data["status"] == "indexing", data


def test_a_failed_job_stays_visible_without_blocking_the_status(
    client: TestClient, written_documents: list
):
    session_id, _ = _create_session_with_document(
        client, "index_failed", written_documents
    )
    job_id = f"failed-{uuid.uuid4().hex[:8]}"
    _write_queue_row(client, job_id, "error")
    _point_session_at_job(client, session_id, job_id)

    data = client.get(f"/api/v1/rag/sessions/{session_id}/index-status").json()
    # The index genuinely is not there, so the status must say so...
    assert data["status"] == "not_indexed", data
    # ...but the failure has to remain visible after a reload.
    assert data["job"]["status"] == "error"


def test_a_dangling_job_pointer_does_not_break_the_status(
    client: TestClient, written_documents: list
):
    """The column is a pointer, not the truth: a vanished job must not 500."""
    session_id, _ = _create_session_with_document(
        client, "index_dangling", written_documents
    )
    _point_session_at_job(client, session_id, "job-that-never-existed")

    response = client.get(f"/api/v1/rag/sessions/{session_id}/index-status")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "not_indexed", data
    assert data["job"] is None
    assert data["job_id"] is None


def test_a_dangling_pointer_does_not_block_a_new_index(
    client: TestClient, written_documents: list
):
    session_id, _ = _create_session_with_document(
        client, "index_dangling_retry", written_documents
    )
    _point_session_at_job(client, session_id, "job-that-never-existed")

    assert client.post(f"/api/v1/rag/sessions/{session_id}/index").status_code == 202
    data = client.get(f"/api/v1/rag/sessions/{session_id}/index-status").json()
    assert data["status"] == "indexed", data


# ===================================================================
# Cancelling a live index before invalidating what it writes
# ===================================================================


def test_changing_parameters_cancels_a_live_index(
    client: TestClient, written_documents: list
):
    """The cleanup deletes the rows a running job is writing, so it must stop."""
    session_id, _ = _create_session_with_document(
        client, "index_cancel_params", written_documents
    )
    job_id = f"live-cancel-{uuid.uuid4().hex[:8]}"
    _write_queue_row(client, job_id, "started")
    _point_session_at_job(client, session_id, job_id)

    response = client.put(
        f"/api/v1/generative-session/{session_id}/parameters",
        json={
            "chunking_model": {
                "component": "CharacterChunkModel",
                "params": {"chunk_size": 250, "chunk_overlap": 25},
            }
        },
    )
    assert response.status_code == 200, response.text

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        assert db.get(GenerativeSession, session_id).index_job_id is None


def test_deleting_a_document_cancels_a_live_index(
    client: TestClient, written_documents: list
):
    session_id, document_id = _create_session_with_document(
        client, "index_cancel_delete", written_documents
    )
    job_id = f"live-del-{uuid.uuid4().hex[:8]}"
    _write_queue_row(client, job_id, "started")
    _point_session_at_job(client, session_id, job_id)

    assert client.delete(f"/api/v1/document/{document_id}").status_code == 204

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        assert db.get(GenerativeSession, session_id).index_job_id is None
