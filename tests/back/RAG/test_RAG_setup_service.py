"""Integration tests for SetupService.build_pipeline().

Tests the full pipeline assembly: DB record creation, document loading,
chunking, retriever setup, prompt resolution, and LLM creation. Uses
the StubLLM pattern to avoid real inference.
"""

from __future__ import annotations

import contextlib
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.dependencies.database.models import (
    GenerativeSession,
    RAGChunkSet,
)
from DashAI.back.dependencies.database.models import (
    RAGPipeline as PipelineDBModel,
)
from DashAI.back.models.RAG.prompts.generation.default_RAG_generation_prompt import (
    TEMPLATES,
)
from DashAI.back.models.RAG.RAG_pipeline import RAGPipeline, RAGPipelineConfig
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from DashAI.back.services.RAG.setup_service import SetupService
from tests.back.RAG.conftest import (
    RAG_E2E_DOC_TEXT,
    _create_test_document,
    bm25_retriever_params,
    write_test_doc_file,
)

# ---------------------------------------------------------------------------
# Stub LLM
# ---------------------------------------------------------------------------


class StubLLMSetupSchema(BaseSchema):
    """Empty schema for the setup stub."""


class StubLLMSetup(TextToTextGenerationTaskModel):
    """Stub LLM for setup service tests."""

    SCHEMA = StubLLMSetupSchema

    def __init__(self, **kwargs):
        self.parameters = {}

    def generate(self, prompt):
        return ["setup stub answer"]


@pytest.fixture(scope="module", autouse=True)
def register_stub_llm_setup(client: TestClient) -> None:
    """Register StubLLMSetup in the component registry."""
    client.app.container["component_registry"].register_component(StubLLMSetup)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _create_session(db, name: str, doc_ids: list[int]) -> int:
    """Create a RAG generative session in the DB and return its ID."""
    session = GenerativeSession(
        task_name="RAGTask",
        model_name="RAGPipeline",
        parameters={
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
                "component": "StubLLMSetup",
                "params": {"stub_component": "setup"},
            },
            "prompt": {
                "component": "DefaultRAGGenerationPrompt",
                "params": {"language": "en", "template": TEMPLATES["en"]},
            },
        },
        name=name,
        description=None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session.id


def _make_pipeline_config(
    db, registry, config_app, session_id: int, doc_ids: list[int]
):
    """Build a RAGPipelineConfig for the given session and documents."""
    return RAGPipelineConfig.from_kwargs(
        session_id=session_id,
        db=db,
        component_registry=registry,
        env_RAG_path=config_app["RAG_PATH"],
        documents=doc_ids,
        prompt={
            "component": "DefaultRAGGenerationPrompt",
            "params": {"language": "en", "template": TEMPLATES["en"]},
        },
        chunking_model={
            "component": "CharacterChunkModel",
            "params": {"chunk_size": 200, "chunk_overlap": 20},
        },
        retriever_model={
            "component": "BM25Retriever",
            "params": bm25_retriever_params(),
        },
        generation_model={
            "component": "StubLLMSetup",
            "params": {"stub_component": "setup"},
        },
    )


# ===================================================================
# Full assembly
# ===================================================================


class TestSetupServiceBuildPipeline:
    """Test that build_pipeline() returns a valid RAGPipeline."""

    def test_full_assembly_returns_pipeline(self, client: TestClient):
        """build_pipeline() with all components returns a RAGPipeline."""
        tag = uuid.uuid4().hex[:8]
        suffix = f"_setup_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)

        try:
            session_factory = client.app.container["session_factory"]
            registry = client.app.container["component_registry"]
            config_app = client.app.container["config"]

            with session_factory() as db:
                session_id = _create_session(db, f"setup_test_{tag}", [doc_id])

                pipeline_config = _make_pipeline_config(
                    db, registry, config_app, session_id, [doc_id]
                )
                setup_service = SetupService(db, registry, config_app["RAG_PATH"])
                pipeline = setup_service.build_pipeline(pipeline_config)

                assert isinstance(pipeline, RAGPipeline)
                assert pipeline.session_id == session_id
                assert doc_id in pipeline.documents
                assert pipeline.retriever is not None
                assert pipeline.llm_model is not None
                assert pipeline.prompt_model is not None
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# Pipeline DB record creation
# ===================================================================


class TestSetupServiceDBRecord:
    """Verify that build_pipeline() creates a RAGPipeline DB record."""

    def test_pipeline_db_record_created(self, client: TestClient):
        """After build_pipeline(), a RAGPipeline DB row exists for the session."""
        tag = uuid.uuid4().hex[:8]
        suffix = f"_dbrec_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)

        try:
            session_factory = client.app.container["session_factory"]
            registry = client.app.container["component_registry"]
            config_app = client.app.container["config"]

            with session_factory() as db:
                session_id = _create_session(db, f"setup_dbrec_{tag}", [doc_id])

                pipeline_config = _make_pipeline_config(
                    db, registry, config_app, session_id, [doc_id]
                )
                setup_service = SetupService(db, registry, config_app["RAG_PATH"])
                setup_service.build_pipeline(pipeline_config)

                record = (
                    db.query(PipelineDBModel).filter_by(session_id=session_id).first()
                )
                assert record is not None, (
                    "Expected a RAGPipeline DB record for the session"
                )
                assert record.session_id == session_id
                # After build_pipeline, FK columns should be populated
                assert record.chunking_model_id is not None
                assert record.prompt_id is not None
                assert record.generation_model_id is not None
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# Pipeline DB record reuse
# ===================================================================


class TestSetupServiceDBRecordReuse:
    """Calling build_pipeline twice with same session reuses the DB record."""

    def test_same_pipeline_record_reused(self, client: TestClient):
        """Two build_pipeline() calls on the same session return the same
        pipeline DB record ID."""
        tag = uuid.uuid4().hex[:8]
        suffix = f"_reuse_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)

        try:
            session_factory = client.app.container["session_factory"]
            registry = client.app.container["component_registry"]
            config_app = client.app.container["config"]

            with session_factory() as db:
                session_id = _create_session(db, f"setup_reuse_{tag}", [doc_id])

                def _build():
                    pipeline_config = _make_pipeline_config(
                        db, registry, config_app, session_id, [doc_id]
                    )
                    setup_service = SetupService(db, registry, config_app["RAG_PATH"])
                    return setup_service.build_pipeline(pipeline_config)

                pipeline1 = _build()
                pipeline2 = _build()

                # Both pipelines should reference the same pipeline_id
                assert pipeline1.pipeline_id == pipeline2.pipeline_id, (
                    "Expected the same pipeline DB record to be reused"
                )
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# Chunking cache
# ===================================================================


class TestSetupServiceChunkingCache:
    """Verify that chunks are cached across build_pipeline() calls."""

    def test_chunks_cached_on_second_call(self, client: TestClient):
        """Second build_pipeline() with same config should reuse cached chunks.
        We verify this by checking that the chunk set signature matches."""
        tag = uuid.uuid4().hex[:8]
        suffix = f"_cache_{tag}"
        doc_id = _create_test_document(client, suffix=suffix)
        path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)

        try:
            session_factory = client.app.container["session_factory"]
            registry = client.app.container["component_registry"]
            config_app = client.app.container["config"]

            with session_factory() as db:
                session_id = _create_session(db, f"setup_cache_{tag}", [doc_id])

                def _build():
                    pipeline_config = _make_pipeline_config(
                        db, registry, config_app, session_id, [doc_id]
                    )
                    setup_service = SetupService(db, registry, config_app["RAG_PATH"])
                    return setup_service.build_pipeline(pipeline_config)

                _build()

                # Count chunk sets after first build
                count_after_first = db.query(RAGChunkSet).count()

                _build()

                # Count chunk sets after second build — should be the same
                count_after_second = db.query(RAGChunkSet).count()

                assert count_after_first == count_after_second, (
                    "Expected chunk set count to remain the same "
                    f"({count_after_first}), but got {count_after_second} "
                    "after second build. "
                    "Chunks should be cached, not recomputed."
                )
        finally:
            with contextlib.suppress(OSError):
                os.remove(path)


# ===================================================================
# Missing document
# ===================================================================


class TestSetupServiceMissingDocument:
    """Calling build_pipeline with a non-existent document ID."""

    def test_missing_document_raises(self, client: TestClient):
        """build_pipeline() with a non-existent document ID → ValueError."""
        session_factory = client.app.container["session_factory"]
        registry = client.app.container["component_registry"]
        config_app = client.app.container["config"]

        with session_factory() as db:
            session_id = _create_session(
                db,
                f"setup_missing_doc_{uuid.uuid4().hex[:8]}",
                [999999],
            )
            pipeline_config = _make_pipeline_config(
                db, registry, config_app, session_id, [999999]
            )
            setup_service = SetupService(db, registry, config_app["RAG_PATH"])
            with pytest.raises(ValueError, match="not found|does not exist"):
                setup_service.build_pipeline(pipeline_config)
