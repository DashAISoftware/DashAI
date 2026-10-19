"""Integration tests for live RAG stage progress through ``RAGJob``.

Runs the full ``RAGJob`` against a real (in-memory) database with stub LLMs.
The generation and decomposition stubs open ``di["session_factory"]`` from
inside ``generate()`` and read the live ``GenerativeProcess.progress`` of the
in-flight process, recording it into a module-level capture list. A wrapper
around ``RAGPipeline.multi_query_retrieval`` captures the same column at
retrieval time — the only moment the short-lived ``retrieving`` payload is
visible, since it is overwritten by ``generating`` before any LLM stub runs.
This proves the pipeline's progress callback reaches the database at every
stage while the run is in flight — the exact mechanism the frontend polls.

Payload literals are asserted verbatim on purpose: the tests pin the wire
contract the frontend consumes, independently of the backend constants.
"""

from __future__ import annotations

import contextlib
import json
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from kink import di

from DashAI.back.core.enums.status import RunStatus
from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.dependencies.database.models import (
    GenerativeProcess,
    GenerativeSession,
    ProcessData,
)
from DashAI.back.job.base_job import JobError
from DashAI.back.job.RAG_job import RAGJob
from DashAI.back.models.RAG.prompts.generation.default_RAG_generation_prompt import (
    TEMPLATES as GEN_TEMPLATES,
)
from DashAI.back.models.RAG.prompts.transformation.default_query_decomposition_prompt import (  # noqa: E501
    TEMPLATES as DECOMP_TEMPLATES,
)
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from tests.back.RAG.conftest import (
    RAG_E2E_DOC_TEXT,
    _create_test_document,
    bm25_retriever_params,
    write_test_doc_file,
)

STUB_ANSWER = "stub progress answer"
SUB_QUERIES = ["progress sub one", "progress sub two"]

#: One entry per LLM ``generate()`` call while a process is being captured.
_PROGRESS_CAPTURE: list = []
#: Process whose live ``progress`` the stubs record; None disables capturing.
_CAPTURE_PROCESS_ID: int | None = None


# ---------------------------------------------------------------------------
# stubs
# ---------------------------------------------------------------------------


class _EmptySchema(BaseSchema):
    """Empty schema for the stubs."""


def _record_progress() -> None:
    """Record the in-flight process's live ``progress`` from its own session.

    Best-effort: any failure while reading is swallowed so a stub never turns a
    test into a false negative for reasons unrelated to progress reporting.
    """
    if _CAPTURE_PROCESS_ID is None:
        return
    with contextlib.suppress(Exception), di["session_factory"]() as db:
        process = db.get(GenerativeProcess, _CAPTURE_PROCESS_ID)
        if process is not None:
            _PROGRESS_CAPTURE.append(process.progress)


class ProgressDecompositionLLM(TextToTextGenerationTaskModel):
    """Decomposition stub that records progress, then answers the call contract."""

    SCHEMA = _EmptySchema

    def __init__(self, **kwargs):
        self.parameters = dict(kwargs)

    def generate(self, prompt):
        _record_progress()
        return [
            json.dumps(
                {"name": "decompose_query", "arguments": {"queries": SUB_QUERIES}}
            )
        ]


class ProgressGenerationLLM(TextToTextGenerationTaskModel):
    """Generation stub that records progress, then returns a fixed answer."""

    SCHEMA = _EmptySchema

    def __init__(self, **kwargs):
        self.parameters = dict(kwargs)

    def generate(self, prompt):
        _record_progress()
        return [STUB_ANSWER]


class FailingProgressGenerationLLM(TextToTextGenerationTaskModel):
    """Generation stub that records progress, then fails the run.

    Used to prove that a failure AFTER a stage was persisted still clears the
    ``progress`` column through the job's error path.
    """

    SCHEMA = _EmptySchema

    def __init__(self, **kwargs):
        self.parameters = dict(kwargs)

    def generate(self, prompt):
        _record_progress()
        raise RuntimeError("failing generation LLM exploded on purpose")


@pytest.fixture(scope="module", autouse=True)
def register_stub_llms(client: TestClient) -> None:
    registry = client.app.container["component_registry"]
    registry.register_component(ProgressDecompositionLLM)
    registry.register_component(ProgressGenerationLLM)
    registry.register_component(FailingProgressGenerationLLM)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _session_params(doc_ids: list[int], with_transformation: bool) -> dict:
    params = {
        "documents": doc_ids,
        "chunking_model": {
            "component": "CharacterChunkModel",
            "params": {"chunk_size": 200, "chunk_overlap": 20},
        },
        "retriever_model": {
            "component": "BM25Retriever",
            "params": bm25_retriever_params(),
        },
        "generation_model": {
            "component": "ProgressGenerationLLM",
            "params": {"stub_component": "job_progress"},
        },
        "prompt": {
            "component": "DefaultRAGGenerationPrompt",
            "params": {"language": "en", "template": GEN_TEMPLATES["en"]},
        },
    }
    if with_transformation:
        params["query_transformation"] = {
            "component": "LLMQueryDecomposer",
            "params": {
                "prompt": {
                    "component": "DefaultQueryDecompositionPrompt",
                    "params": {
                        "language": "en",
                        "template": DECOMP_TEMPLATES["en"],
                    },
                },
                "llm_model": {
                    "component": "ProgressDecompositionLLM",
                    "params": {"stub_marker": "progress_decompose"},
                },
                "history_window": 2,
            },
        }
    return params


def _create_session_process(
    client: TestClient, session_params: dict, input_text: str
) -> tuple[int, int]:
    """Insert a session + process + input directly. Returns (session_id, pid)."""
    tag = uuid.uuid4().hex[:8]
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = GenerativeSession(
            task_name="RAGTask",
            model_name="RAGPipeline",
            parameters=session_params,
            name=f"job_progress_{tag}",
            description=None,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        process = GenerativeProcess(session_id=session.id, status=RunStatus.NOT_STARTED)
        db.add(process)
        db.commit()
        db.refresh(process)

        db.add(
            ProcessData(
                process_id=process.id,
                is_input=True,
                data=input_text,
                data_type="str",
            )
        )
        db.commit()
        return session.id, process.id


def _run_with_capture(
    client: TestClient, process_id: int, monkeypatch: pytest.MonkeyPatch = None
) -> None:
    """Run ``RAGJob`` while the run is observed from inside every stage.

    The LLM stubs capture progress at the transformation and generation
    checkpoints. ``monkeypatch`` additionally wraps
    ``RAGPipeline.multi_query_retrieval`` so the persisted progress is read at
    retrieval time too — the only way to observe the short-lived ``retrieving``
    payload, which is overwritten by ``generating`` before any LLM stub runs.
    """
    global _CAPTURE_PROCESS_ID
    _PROGRESS_CAPTURE.clear()
    _CAPTURE_PROCESS_ID = process_id
    try:
        if monkeypatch is not None:
            from DashAI.back.models.RAG.RAG_pipeline import RAGPipeline

            original = RAGPipeline.multi_query_retrieval

            def wrapped(self, queries):
                _record_progress()
                return original(self, queries)

            monkeypatch.setattr(RAGPipeline, "multi_query_retrieval", wrapped)
        RAGJob(generative_process_id=process_id).run()
    finally:
        _CAPTURE_PROCESS_ID = None


# ===================================================================
# transformation enabled
# ===================================================================


class TestProgressWithTransformation:
    def test_captures_full_stage_sequence(self, client, monkeypatch):
        tag = uuid.uuid4().hex[:8]
        suffix = f"_progress_transform_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)
        try:
            _session_id, process_id = _create_session_process(
                client, _session_params([doc_id], True), "Decompose this"
            )
            _run_with_capture(client, process_id, monkeypatch)

            assert _PROGRESS_CAPTURE == [
                {"stage": "transforming"},
                {"stage": "retrieving", "queries": SUB_QUERIES},
                {"stage": "generating"},
            ]

            session_factory = client.app.container["session_factory"]
            with session_factory() as db:
                process = db.get(GenerativeProcess, process_id)
                assert process.status == RunStatus.FINISHED, process.status
                assert process.progress is None
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# transformation disabled
# ===================================================================


class TestProgressWithoutTransformation:
    def test_captures_retrieving_then_generating(self, client, monkeypatch):
        tag = uuid.uuid4().hex[:8]
        suffix = f"_progress_plain_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)
        try:
            _session_id, process_id = _create_session_process(
                client, _session_params([doc_id], False), "Plain message"
            )
            _run_with_capture(client, process_id, monkeypatch)

            # No transformation stage: the retrieval queries are the raw
            # message, so "transforming" must never appear.
            assert _PROGRESS_CAPTURE == [
                {"stage": "retrieving", "queries": ["Plain message"]},
                {"stage": "generating"},
            ]

            session_factory = client.app.container["session_factory"]
            with session_factory() as db:
                process = db.get(GenerativeProcess, process_id)
                assert process.status == RunStatus.FINISHED, process.status
                assert process.progress is None
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# GET endpoint exposes the column
# ===================================================================


class TestGetEndpointExposesProgress:
    def test_get_process_includes_progress_key(self, client: TestClient):
        tag = uuid.uuid4().hex[:8]
        suffix = f"_progress_api_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)
        try:
            _session_id, process_id = _create_session_process(
                client, _session_params([doc_id], False), "API message"
            )
            RAGJob(generative_process_id=process_id).run()

            response = client.get(f"/api/v1/generative-process/{process_id}")
            assert response.status_code == 200, response.text
            payload = response.json()
            assert "progress" in payload
            assert payload["progress"] is None
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# error path clears progress
# ===================================================================


class TestProgressErrorPath:
    def test_failure_after_a_stage_clears_progress(self, client: TestClient):
        """A run that fails mid-generation ends ERROR with progress cleared.

        The failing generation LLM first records the in-flight progress, so the
        capture proves the ``generating`` stage was persisted before the
        failure — making the final ``progress is None`` a real assertion of the
        error-path cleanup, not a trivially-true setup failure.
        """
        tag = uuid.uuid4().hex[:8]
        suffix = f"_progress_broken_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)
        try:
            params = _session_params([doc_id], False)
            params["generation_model"] = {
                "component": "FailingProgressGenerationLLM",
                "params": {"broken_marker": "progress_error"},
            }
            _session_id, process_id = _create_session_process(
                client, params, "Broken message"
            )

            with pytest.raises(JobError, match="RAG model generation"):
                _run_with_capture(client, process_id)

            assert _PROGRESS_CAPTURE == [{"stage": "generating"}]

            session_factory = client.app.container["session_factory"]
            with session_factory() as db:
                process = db.get(GenerativeProcess, process_id)
                assert process.status == RunStatus.ERROR, process.status
                assert process.progress is None
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)
