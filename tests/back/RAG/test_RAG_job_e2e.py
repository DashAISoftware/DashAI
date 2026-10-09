"""Expanded E2E tests for RAGJob.

Builds on the StubLLM pattern from test_RAG_job_completes_flow.py to test
multi-document sessions, conversation history, error recovery, extra session
parameter keys, different chunking models, missing/invalid process IDs,
and output verification.
"""

from __future__ import annotations

import contextlib
import json
import os
import uuid

import pytest
from fastapi.testclient import TestClient

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
    TEMPLATES,
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

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------
STUB_ANSWER = "stub answer e2e"

DOC_TEXT_2 = (
    "Retrieval-Augmented Generation (RAG) combines document retrieval with "
    "text generation to produce answers grounded in specific documents. "
    "The pipeline involves chunking documents, indexing them with a retriever, "
    "and then using a language model to generate responses based on retrieved "
    "chunks. " * 50
)


# ---------------------------------------------------------------------------
# Stub LLMs (module-scoped registration)
# ---------------------------------------------------------------------------


class StubLLMSchemaE2E(BaseSchema):
    """Empty schema for the stub model."""


class StubLLME2E(TextToTextGenerationTaskModel):
    """Deterministic stub LLM for E2E tests."""

    SCHEMA = StubLLMSchemaE2E

    def __init__(self, **kwargs):
        self.parameters = {}

    def generate(self, prompt):
        return [STUB_ANSWER]


class HistoryCapturingStubLLMSchema(BaseSchema):
    """Empty schema for the history-capturing stub model."""


class HistoryCapturingStubLLM(TextToTextGenerationTaskModel):
    """Stub LLM that records every prompt it receives.

    Stores the full ``model_input`` list passed to ``generate()`` in a
    class-level list so tests can verify conversation-history propagation.
    """

    SCHEMA = HistoryCapturingStubLLMSchema
    received_prompts: list = []

    def __init__(self, **kwargs):
        self.parameters = {}

    def generate(self, model_input):
        HistoryCapturingStubLLM.received_prompts.append(model_input)
        return [STUB_ANSWER]


@pytest.fixture(scope="module", autouse=True)
def register_stub_llm_e2e(client: TestClient) -> None:
    """Register the stub LLMs in the component registry."""
    registry = client.app.container["component_registry"]
    registry.register_component(StubLLME2E)
    registry.register_component(HistoryCapturingStubLLM)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _session_params(
    doc_ids: list[int],
    chunking_component: str = "CharacterChunkModel",
    chunking_params: dict | None = None,
    extra_keys: dict | None = None,
    generation_component: str = "StubLLME2E",
    generation_params: dict | None = None,
) -> dict:
    """Build session parameters for E2E tests."""
    if chunking_params is None:
        chunking_params = {"chunk_size": 200, "chunk_overlap": 20}
    if generation_params is None:
        # Distinct params keep this module's stub from colliding with records
        # left by other modules in the shared test DB (the LLMService cache
        # key ignores component_name; the shared tmp/ DB is not always removed
        # between modules on Windows). Stub classes still use parameters={}.
        generation_params = {"stub_component": "e2e"}
    params = {
        "documents": doc_ids,
        "chunking_model": {
            "component": chunking_component,
            "params": chunking_params,
        },
        "retriever_model": {
            "component": "BM25Retriever",
            "params": bm25_retriever_params(),
        },
        "generation_model": {
            "component": generation_component,
            "params": generation_params,
        },
        "prompt": {
            "component": "DefaultRAGGenerationPrompt",
            "params": {"language": "en", "template": TEMPLATES["en"]},
        },
    }
    if extra_keys:
        params.update(extra_keys)
    return params


def _create_session_and_process(
    client: TestClient,
    session_params: dict,
    input_text: str = "Tell me about DashAI",
    name_suffix: str = "",
) -> int:
    """Create a generative session + process + input, return process ID."""
    tag = uuid.uuid4().hex[:8]
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = GenerativeSession(
            task_name="RAGTask",
            model_name="RAGPipeline",
            parameters=session_params,
            name=f"e2e_{name_suffix}_{tag}",
            description=None,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        process = GenerativeProcess(
            session_id=session.id,
            status=RunStatus.NOT_STARTED,
        )
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


# ===================================================================
# Multi-document session
# ===================================================================


class TestRAGJobMultiDocument:
    """RAGJob with 2+ documents in the session."""

    def test_two_documents_completes(self, client: TestClient):
        """RAGJob with two documents finishes successfully."""
        tag = uuid.uuid4().hex[:8]
        suffix_a = f"_multiA_{tag}"
        suffix_b = f"_multiB_{tag}"
        doc_a = _create_test_document(client, suffix=suffix_a)
        doc_b = _create_test_document(client, suffix=suffix_b)
        path_a = write_test_doc_file(suffix_a, RAG_E2E_DOC_TEXT)
        path_b = write_test_doc_file(suffix_b, DOC_TEXT_2)

        try:
            params = _session_params([doc_a, doc_b])
            process_id = _create_session_and_process(
                client, params, name_suffix="multi_doc"
            )
            RAGJob(generative_process_id=process_id).run()

            session_factory = client.app.container["session_factory"]
            with session_factory() as db:
                process = db.get(GenerativeProcess, process_id)
                assert process.status == RunStatus.FINISHED, (
                    f"Expected FINISHED, got {process.status}"
                )
                assert any(
                    o.data_type == "str" and STUB_ANSWER in o.data
                    for o in process.output
                ), "Expected a str output containing the stub answer."
        finally:
            for p in (path_a, path_b):
                with contextlib.suppress(OSError):
                    os.remove(p)


# ===================================================================
# Conversation history
# ===================================================================


class TestRAGJobConversationHistory:
    """Sequential RAGJobs on the same session — history propagation."""

    def test_second_job_includes_history(self, client: TestClient):
        """Running two RAGJobs on the same session: the second job must pass
        the first Q&A pair as conversation history to the LLM."""
        HistoryCapturingStubLLM.received_prompts.clear()
        tag = uuid.uuid4().hex[:8]
        suffix = f"_history_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)

        try:
            # Distinct params so HistoryCapturingStubLLM does not collide with
            # StubLLME2E (both registered in this module) in the LLMService
            # cache, which keys by parameters_hash only.
            params = _session_params(
                [doc_id],
                generation_component="HistoryCapturingStubLLM",
                generation_params={"capture_marker": "history"},
            )
            session_factory = client.app.container["session_factory"]

            # Create session
            with session_factory() as db:
                session = GenerativeSession(
                    task_name="RAGTask",
                    model_name="RAGPipeline",
                    parameters=params,
                    name=f"e2e_history_{tag}",
                    description=None,
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                session_id = session.id

            # First process
            with session_factory() as db:
                p1 = GenerativeProcess(
                    session_id=session_id,
                    status=RunStatus.NOT_STARTED,
                )
                db.add(p1)
                db.commit()
                db.refresh(p1)
                db.add(
                    ProcessData(
                        process_id=p1.id,
                        is_input=True,
                        data="What is DashAI?",
                        data_type="str",
                    )
                )
                db.commit()
                pid1 = p1.id

            RAGJob(generative_process_id=pid1).run()

            with session_factory() as db:
                p1 = db.get(GenerativeProcess, pid1)
                assert p1.status == RunStatus.FINISHED, (
                    f"First process should be FINISHED, got {p1.status}"
                )

            # Second process (should include history from first)
            with session_factory() as db:
                p2 = GenerativeProcess(
                    session_id=session_id,
                    status=RunStatus.NOT_STARTED,
                )
                db.add(p2)
                db.commit()
                db.refresh(p2)
                db.add(
                    ProcessData(
                        process_id=p2.id,
                        is_input=True,
                        data="Tell me more about its features",
                        data_type="str",
                    )
                )
                db.commit()
                pid2 = p2.id

            RAGJob(generative_process_id=pid2).run()

            with session_factory() as db:
                p2 = db.get(GenerativeProcess, pid2)
                assert p2.status == RunStatus.FINISHED, (
                    f"Second process should be FINISHED, got {p2.status}"
                )
                assert any(
                    o.data_type == "str" and STUB_ANSWER in o.data for o in p2.output
                ), "Expected a str output containing the stub answer."

            # The second job's LLM call must include the first Q&A pair as history
            assert len(HistoryCapturingStubLLM.received_prompts) >= 2, (
                "Expected at least two LLM calls (one per job), "
                f"got {len(HistoryCapturingStubLLM.received_prompts)}"
            )
            second_model_input = HistoryCapturingStubLLM.received_prompts[-1]
            assert any(
                m.get("role") == "user" and m.get("content") == "What is DashAI?"
                for m in second_model_input
            ), "Second job's LLM input is missing the first question in history."
            assert any(
                m.get("role") == "assistant" and STUB_ANSWER in m.get("content", "")
                for m in second_model_input
            ), "Second job's LLM input is missing the first answer in history."
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# Error recovery
# ===================================================================


class TestRAGJobErrorRecovery:
    """RAGJob with broken components → ERROR status."""

    def test_broken_generation_model_sets_error(self, client: TestClient):
        """A session referencing a non-existent generation model component
        causes RAGJob to set the process status to ERROR.
        """
        tag = uuid.uuid4().hex[:8]
        suffix = f"_broken_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)

        try:
            params = _session_params([doc_id])
            # Distinct params avoid a hash collision with StubLLME2E's
            # empty-params record (see the LLMService cache-key bug). Without
            # this, get_or_create() would silently reuse the stub and the
            # pipeline would succeed instead of failing.
            params["generation_model"] = {
                "component": "NonExistentLLM_999",
                "params": {"broken_marker": "non_existent_llm"},
            }
            process_id = _create_session_and_process(
                client, params, name_suffix="broken_gen"
            )

            # Run the job — an unknown component must raise JobError
            with pytest.raises(JobError, match="pipeline setup|Error during"):
                RAGJob(generative_process_id=process_id).run()

            session_factory = client.app.container["session_factory"]
            with session_factory() as db:
                process = db.get(GenerativeProcess, process_id)
                assert process.status == RunStatus.ERROR, (
                    f"Expected ERROR status for broken component, got {process.status}"
                )
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# Extra session parameter keys
# ===================================================================


class TestRAGJobExtraKeys:
    """RAGJob with extra non-RAG keys in session parameters."""

    def test_extra_keys_filtered_and_completes(self, client: TestClient):
        """Session parameters with extra keys (e.g. 'prompt_id') are
        filtered by RAGJob and the pipeline still completes."""
        tag = uuid.uuid4().hex[:8]
        suffix = f"_extra_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)

        try:
            params = _session_params(
                [doc_id],
                extra_keys={"prompt_id": 999, "custom_metadata": "extra"},
            )
            process_id = _create_session_and_process(
                client, params, name_suffix="extra_keys"
            )
            RAGJob(generative_process_id=process_id).run()

            session_factory = client.app.container["session_factory"]
            with session_factory() as db:
                process = db.get(GenerativeProcess, process_id)
                assert process.status == RunStatus.FINISHED, (
                    f"Expected FINISHED despite extra keys, got {process.status}"
                )
                assert any(
                    o.data_type == "str" and STUB_ANSWER in o.data
                    for o in process.output
                ), "Expected a str output containing the stub answer."
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# Different chunking models
# ===================================================================


class TestRAGJobDifferentChunking:
    """RAGJob with different chunking model configurations."""

    def test_recursive_character_chunk_model(self, client: TestClient):
        """RAGJob with RecursiveCharacterChunkModel completes."""
        tag = uuid.uuid4().hex[:8]
        suffix = f"_recchar_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)

        try:
            params = _session_params(
                [doc_id],
                chunking_component="RecursiveCharacterChunkModel",
                chunking_params={
                    "chunk_size": 300,
                    "chunk_overlap": 30,
                    "separators": ["\n\n", "\n", ".", " ", ""],
                },
            )
            process_id = _create_session_and_process(
                client, params, name_suffix="recchar"
            )
            RAGJob(generative_process_id=process_id).run()

            session_factory = client.app.container["session_factory"]
            with session_factory() as db:
                process = db.get(GenerativeProcess, process_id)
                assert process.status == RunStatus.FINISHED, (
                    f"Expected FINISHED, got {process.status}"
                )
                assert any(
                    o.data_type == "str" and STUB_ANSWER in o.data
                    for o in process.output
                ), "Expected a str output containing the stub answer."
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# Missing / invalid process ID
# ===================================================================


class TestRAGJobMissingProcessID:
    """RAGJob without or with invalid generative_process_id."""

    def test_missing_process_id_raises(self, client: TestClient):
        """RAGJob without generative_process_id → JobError."""
        with pytest.raises(JobError, match="generative_process_id"):
            RAGJob().run()

    def test_nonexistent_process_id_raises(self, client: TestClient):
        """RAGJob with non-existent process ID → JobError."""
        with pytest.raises(JobError, match="not found"):
            RAGJob(generative_process_id=999999).run()


# ===================================================================
# Output verification
# ===================================================================


class TestRAGJobOutputVerification:
    """Verify the output stored in the DB after RAGJob completes."""

    def test_output_has_str_and_dict(self, client: TestClient):
        """After RAGJob, the process output contains both a str (message)
        and a Dict (chunks JSON)."""
        tag = uuid.uuid4().hex[:8]
        suffix = f"_output_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)

        try:
            params = _session_params([doc_id])
            process_id = _create_session_and_process(
                client, params, name_suffix="output_verify"
            )
            RAGJob(generative_process_id=process_id).run()

            session_factory = client.app.container["session_factory"]
            with session_factory() as db:
                process = db.get(GenerativeProcess, process_id)
                assert process.status == RunStatus.FINISHED

                outputs = process.output
                assert len(outputs) >= 2, (
                    f"Expected at least 2 outputs (str + Dict), got {len(outputs)}"
                )

                # Find the str output
                str_outputs = [o for o in outputs if o.data_type == "str"]
                assert len(str_outputs) >= 1, "Expected at least one str output"
                assert STUB_ANSWER in str_outputs[0].data

                # Find the Dict output
                dict_outputs = [o for o in outputs if o.data_type == "Dict"]
                assert len(dict_outputs) >= 1, "Expected at least one Dict output"
                # The Dict output should be valid JSON
                chunks_data = json.loads(dict_outputs[0].data)
                assert isinstance(chunks_data, dict)
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)

    def test_output_chunks_reference_documents(self, client: TestClient):
        """Chunk references in the output contain document metadata."""
        tag = uuid.uuid4().hex[:8]
        suffix = f"_chunksref_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)

        try:
            params = _session_params([doc_id])
            process_id = _create_session_and_process(
                client, params, name_suffix="chunks_ref"
            )
            RAGJob(generative_process_id=process_id).run()

            session_factory = client.app.container["session_factory"]
            with session_factory() as db:
                process = db.get(GenerativeProcess, process_id)
                dict_outputs = [o for o in process.output if o.data_type == "Dict"]
                if dict_outputs:
                    chunks_data = json.loads(dict_outputs[0].data)
                    for _key, chunk_ref in chunks_data.items():
                        assert "document_id" in chunk_ref
                        assert "document_name" in chunk_ref
                        assert "document_position" in chunk_ref
                        assert "text" in chunk_ref
                        assert chunk_ref["document_id"] == doc_id
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)
