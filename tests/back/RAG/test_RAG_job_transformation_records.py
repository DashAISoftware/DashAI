"""Integration tests for the multi-row RAG process output.

Runs the real ``LLMQueryDecomposer`` with a stub LLM through the full RAGJob,
against a session that has a document. Verifies that a finished process emits
exactly five typed ``ProcessData`` output rows in pipeline order
(``Queries`` → ``Dict`` → ``Trace`` → ``Timings`` → ``str``), that the
``Queries`` row holds the transformed queries (or the one-element
``[input message]`` when the stage is disabled), that the ``Trace`` row is a
real retriever node tree, that the ``Timings`` row carries the four stage
durations, and that the GET endpoints no longer expose a
``transformed_queries`` key. The ``rag_transformed_query`` table itself is
removed.
"""

from __future__ import annotations

import contextlib
import json
import os
import uuid

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import RunStatus
from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.dependencies.database.models import (
    GenerativeProcess,
    ProcessData,
)
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

STUB_ANSWER = "stub transformation answer"
SUB_QUERIES = ["sub query one", "sub query two"]
OUTPUT_TYPES = ["Queries", "Dict", "Trace", "Timings", "str"]


# ---------------------------------------------------------------------------
# stub LLMs
# ---------------------------------------------------------------------------


class _EmptySchema(BaseSchema):
    """Empty schema for the stubs."""


class StubGenerationLLM(TextToTextGenerationTaskModel):
    """Deterministic generation stub."""

    SCHEMA = _EmptySchema

    def __init__(self, **kwargs):
        self.parameters = dict(kwargs)

    def generate(self, prompt):
        return [STUB_ANSWER]


class StubDecompositionLLM(TextToTextGenerationTaskModel):
    """Stub that answers the decomposition function-call contract."""

    SCHEMA = _EmptySchema

    def __init__(self, **kwargs):
        self.parameters = dict(kwargs)

    def generate(self, prompt):
        return [
            json.dumps(
                {"name": "decompose_query", "arguments": {"queries": SUB_QUERIES}}
            )
        ]


@pytest.fixture(scope="module", autouse=True)
def register_stub_llms(client: TestClient) -> None:
    registry = client.app.container["component_registry"]
    registry.register_component(StubGenerationLLM)
    registry.register_component(StubDecompositionLLM)


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
            "component": "StubGenerationLLM",
            "params": {"stub_component": "job_transformation"},
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
                    "component": "StubDecompositionLLM",
                    "params": {"stub_marker": "decompose"},
                },
                "history_window": 2,
            },
        }
    return params


def _create_session_process(
    client: TestClient, session_params: dict, input_text: str
) -> tuple[int, int]:
    """Insert a session + process + input directly. Returns (session_id, pid)."""
    from DashAI.back.dependencies.database.models import GenerativeSession, ProcessData

    tag = uuid.uuid4().hex[:8]
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = GenerativeSession(
            task_name="RAGTask",
            model_name="RAGPipeline",
            parameters=session_params,
            name=f"job_transformation_{tag}",
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


def _add_process(client: TestClient, session_id: int, input_text: str) -> int:
    from DashAI.back.dependencies.database.models import ProcessData

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        process = GenerativeProcess(session_id=session_id, status=RunStatus.NOT_STARTED)
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
        return process.id


def _output_rows(client: TestClient, process_id: int) -> list[tuple[str, str]]:
    """Return the finished process output as ``(data_type, data)`` pairs."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        process = db.get(GenerativeProcess, process_id)
        return [(row.data_type, row.data) for row in process.output]


# ===================================================================
# transformation enabled
# ===================================================================


class TestJobWritesTypedOutputRows:
    def test_enabled_stage_writes_queries_dict_str(self, client: TestClient):
        tag = uuid.uuid4().hex[:8]
        suffix = f"_jtransform_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)
        try:
            _session_id, process_id = _create_session_process(
                client, _session_params([doc_id], True), "Decompose this"
            )
            RAGJob(generative_process_id=process_id).run()

            session_factory = client.app.container["session_factory"]
            with session_factory() as db:
                process = db.get(GenerativeProcess, process_id)
                assert process.status == RunStatus.FINISHED, process.status

            rows = _output_rows(client, process_id)
            assert [data_type for data_type, _data in rows] == OUTPUT_TYPES
            assert json.loads(rows[0][1]) == SUB_QUERIES
            chunks = json.loads(rows[1][1])
            assert isinstance(chunks, dict)
            assert len(chunks) >= 1
            trace = json.loads(rows[2][1])
            assert [entry["query"] for entry in trace] == SUB_QUERIES
            assert trace[0]["retriever"]["name"] == "BM25Retriever"
            timings = json.loads(rows[3][1])
            assert set(timings) == {
                "transformation_ms",
                "retrieval_ms",
                "generation_ms",
                "total_ms",
            }
            assert rows[4][1] == STUB_ANSWER
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)

    def test_second_message_also_writes_typed_rows(self, client: TestClient):
        tag = uuid.uuid4().hex[:8]
        suffix = f"_jtransform2_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)
        try:
            _session_id, pid1 = _create_session_process(
                client, _session_params([doc_id], True), "First"
            )
            RAGJob(generative_process_id=pid1).run()

            pid2 = _add_process(client, _session_id, "Second")
            RAGJob(generative_process_id=pid2).run()

            first_rows = _output_rows(client, pid1)
            second_rows = _output_rows(client, pid2)
            assert [data_type for data_type, _data in first_rows] == OUTPUT_TYPES
            assert [data_type for data_type, _data in second_rows] == OUTPUT_TYPES
            assert json.loads(second_rows[0][1]) == SUB_QUERIES
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)

    def test_get_endpoints_drop_transformed_queries_key(self, client: TestClient):
        tag = uuid.uuid4().hex[:8]
        suffix = f"_jtransform_api_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)
        try:
            session_id, process_id = _create_session_process(
                client, _session_params([doc_id], True), "Decompose this"
            )
            RAGJob(generative_process_id=process_id).run()

            by_session = client.get(f"/api/v1/generative-process/session/{session_id}")
            assert by_session.status_code == 200, by_session.text
            by_id = {p["id"]: p for p in by_session.json()}
            assert "transformed_queries" not in by_id[process_id]

            single = client.get(f"/api/v1/generative-process/{process_id}")
            assert single.status_code == 200, single.text
            assert "transformed_queries" not in single.json()
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# transformation disabled
# ===================================================================


class TestJobWithoutTransformation:
    def test_disabled_stage_writes_message_as_single_query(self, client: TestClient):
        tag = uuid.uuid4().hex[:8]
        suffix = f"_jnotransform_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)
        try:
            session_id, process_id = _create_session_process(
                client, _session_params([doc_id], False), "Plain message"
            )
            RAGJob(generative_process_id=process_id).run()

            session_factory = client.app.container["session_factory"]
            with session_factory() as db:
                process = db.get(GenerativeProcess, process_id)
                assert process.status == RunStatus.FINISHED, process.status

            rows = _output_rows(client, process_id)
            assert [data_type for data_type, _data in rows] == OUTPUT_TYPES
            assert json.loads(rows[0][1]) == ["Plain message"]
            assert json.loads(rows[2][1])[0]["query"] == "Plain message"
            timings = json.loads(rows[3][1])
            assert timings["transformation_ms"] == 0.0
            assert rows[4][1] == STUB_ANSWER

            response = client.get(f"/api/v1/generative-process/session/{session_id}")
            assert response.status_code == 200, response.text
            by_id = {p["id"]: p for p in response.json()}
            assert "transformed_queries" not in by_id[process_id]
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# the rag_transformed_query table is gone
# ===================================================================


class TestRemovedTransformedQueryTable:
    def test_table_is_not_created(self, client: TestClient):
        session_factory = client.app.container["session_factory"]
        with session_factory() as db:
            engine = db.get_bind()
            assert "rag_transformed_query" not in sa.inspect(engine).get_table_names()


# ===================================================================
# delete paths still remove the process output rows
# ===================================================================


class TestDeleteRemovesOutputRows:
    def test_delete_process_removes_its_output_rows(self, client: TestClient):
        tag = uuid.uuid4().hex[:8]
        suffix = f"_jdelete_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)
        try:
            _session_id, process_id = _create_session_process(
                client, _session_params([doc_id], True), "Delete me"
            )
            RAGJob(generative_process_id=process_id).run()
            assert len(_output_rows(client, process_id)) == 5

            response = client.delete(f"/api/v1/generative-process/{process_id}")
            assert response.status_code == 204, response.text

            session_factory = client.app.container["session_factory"]
            with session_factory() as db:
                remaining = (
                    db.query(ProcessData).filter_by(process_id=process_id).count()
                )
            assert remaining == 0
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# manual end-to-end probe (run with -s to inspect the printed evidence)
# ===================================================================


def test_manual_probe_prints_output_rows(client: TestClient, capsys):
    """Print the persisted five output rows with parsed payloads."""
    tag = uuid.uuid4().hex[:8]
    suffix = f"_jprobe_{tag}"
    doc_id = _create_test_document(client, suffix=suffix)
    path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)
    try:
        _session_id, process_id = _create_session_process(
            client, _session_params([doc_id], True), "Probe decomposition"
        )
        RAGJob(generative_process_id=process_id).run()

        rows = _output_rows(client, process_id)
        print("\n=== process output rows ===")
        for data_type, data in rows:
            payload = json.loads(data) if data_type != "str" else data
            print({"data_type": data_type, "payload": payload})

        assert [data_type for data_type, _data in rows] == OUTPUT_TYPES
        assert json.loads(rows[0][1]) == SUB_QUERIES
        assert json.loads(rows[2][1])[0]["retriever"]["name"] == "BM25Retriever"
        timings = json.loads(rows[3][1])
        assert set(timings) == {
            "transformation_ms",
            "retrieval_ms",
            "generation_ms",
            "total_ms",
        }
        assert rows[4][1] == STUB_ANSWER
    finally:
        with contextlib.suppress(OSError):
            os.remove(path)
