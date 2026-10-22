"""Tests for the lazy lookup-or-create path in ``LLMService``.

The lazy path persists the configuration record and returns a :class:`LazyLLM`
proxy without constructing the backend. The eager path must keep constructing
immediately for every existing caller.
"""

from __future__ import annotations

import contextlib
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    schema_field,
)
from DashAI.back.dependencies.database.models import (
    GenerativeSession,
    RAGGenerationModel,
    RAGRetrievalModel,
)
from DashAI.back.models.lazy_llm import LazyLLM
from DashAI.back.models.RAG.exceptions import (
    RAGComponentNotFoundError,
    RAGGenerationModelError,
)
from DashAI.back.models.RAG.prompts.base_prompt import BasePrompt
from DashAI.back.models.RAG.prompts.generation.default_RAG_generation_prompt import (
    TEMPLATES,
)
from DashAI.back.models.RAG.RAG_pipeline import RAGPipelineConfig
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from DashAI.back.services.RAG.llm_service import LLMService
from DashAI.back.services.RAG.retrieval_llm_service import (
    RetrievalLLMService,
    RetrievalLLMServiceResult,
)
from DashAI.back.services.RAG.setup_service import SetupService
from DashAI.back.services.RAG.utils import build_parameters_hash, normalize_params
from tests.back.RAG.conftest import (
    RAG_E2E_DOC_TEXT,
    _create_test_document,
    bm25_retriever_params,
    write_test_doc_file,
)


class CountingLLMSchema(BaseSchema):
    """Empty schema for the counting stub LLM."""


class CountingLLM(TextToTextGenerationTaskModel):
    """Stub LLM that counts how many real instances were constructed."""

    SCHEMA = CountingLLMSchema
    construction_count = 0

    def __init__(self, **kwargs) -> None:
        type(self).construction_count += 1
        self.parameters = dict(kwargs)
        self.closed = False

    def generate(self, prompt):
        return ["counting answer"]

    def close(self) -> None:
        self.closed = True


class ValidatingLLMSchema(BaseSchema):
    """Schema with a required parameter used to prove assembly-time validation."""

    context_window: schema_field(
        int_field(gt=0),
        placeholder=2048,
        description="Context window used by the validating stub.",
    )  # type: ignore


class ValidatingLLM(TextToTextGenerationTaskModel):
    """Counting stub whose schema rejects malformed parameters."""

    SCHEMA = ValidatingLLMSchema
    construction_count = 0

    def __init__(self, **kwargs) -> None:
        type(self).construction_count += 1
        self.parameters = dict(kwargs)
        self.closed = False

    def generate(self, prompt):
        return ["validating answer"]

    def close(self) -> None:
        self.closed = True


class NotAnLLMPrompt(BasePrompt):
    """Registered non-LLM component rejected by both lookup paths."""

    SCHEMA = CountingLLMSchema

    def __init__(self, **kwargs) -> None:
        pass


@pytest.fixture(scope="module", autouse=True)
def register_lazy_stubs(client: TestClient) -> None:
    """Register the stub components used by every test in this module."""
    registry = client.app.container["component_registry"]
    registry.register_component(CountingLLM)
    registry.register_component(ValidatingLLM)
    registry.register_component(NotAnLLMPrompt)


@pytest.fixture(autouse=True)
def reset_stub_state(client: TestClient) -> None:
    """Reset construction counters and remove rows created by these tests."""
    CountingLLM.construction_count = 0
    ValidatingLLM.construction_count = 0
    session_factory = client.app.container["session_factory"]
    names = ["CountingLLM", "ValidatingLLM", "NotAnLLMPrompt", "RemovedLLM"]
    with session_factory() as db:
        db.query(RAGGenerationModel).filter(
            RAGGenerationModel.class_name.in_(names)
        ).delete(synchronize_session=False)
        db.query(RAGRetrievalModel).filter(
            RAGRetrievalModel.class_name.in_(names)
        ).delete(synchronize_session=False)
        db.commit()


def _service(client: TestClient, db) -> LLMService:
    registry = client.app.container["component_registry"]
    return LLMService(db, registry)


def test_get_or_create_lazy_defers_construction_and_persists(client: TestClient):
    """The proxy is returned, the row exists, and construction waits for use."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = _service(client, db)
        result = service.get_or_create_lazy("CountingLLM", {"temperature": 0.2})

        assert isinstance(result.model, LazyLLM)
        assert result.model.is_loaded is False
        assert CountingLLM.construction_count == 0

        row = db.query(RAGGenerationModel).filter_by(id=result.db_record_id).one()
        assert row.class_name == "CountingLLM"
        assert row.parameters == {"temperature": 0.2}

        output = result.model.generate([{"role": "user", "content": "hi"}])

        assert output == ["counting answer"]
        assert CountingLLM.construction_count == 1
        assert result.model.is_loaded is True


def test_get_or_create_lazy_reuses_record_without_constructing(client: TestClient):
    """A repeated lazy lookup reuses the id and still constructs nothing."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = _service(client, db)
        first = service.get_or_create_lazy("CountingLLM", {"b": 1, "a": 2})
        second = service.get_or_create_lazy("CountingLLM", {"a": 2, "b": 1})

        assert first.db_record_id == second.db_record_id
        assert isinstance(second.model, LazyLLM)
        assert second.model.is_loaded is False
        assert CountingLLM.construction_count == 0
        assert (
            db.query(RAGGenerationModel).filter_by(class_name="CountingLLM").count()
            == 1
        )


def test_get_or_create_still_constructs_eagerly(client: TestClient):
    """The eager path keeps its original observable behavior."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = _service(client, db)
        result = service.get_or_create("CountingLLM", {"temperature": 0.1})

        assert CountingLLM.construction_count == 1
        assert isinstance(result.model, CountingLLM)
        assert not isinstance(result.model, LazyLLM)


def test_non_llm_component_raises_in_both_paths(client: TestClient):
    """A registered non-LLM component is rejected by eager and lazy lookups."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = _service(client, db)

        with pytest.raises(RAGGenerationModelError):
            service.get_or_create_lazy("NotAnLLMPrompt", {})
        assert (
            db.query(RAGGenerationModel).filter_by(class_name="NotAnLLMPrompt").count()
            == 0
        )

        with pytest.raises(RAGGenerationModelError):
            service.get_or_create("NotAnLLMPrompt", {})


def test_get_or_create_lazy_rejects_invalid_params_without_constructing(
    client: TestClient,
):
    """Invalid parameters fail during assembly, before a row or a model exists."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = _service(client, db)

        with pytest.raises(ValidationError):
            service.get_or_create_lazy(
                "ValidatingLLM", {"context_window": "not-a-number"}
            )

        assert ValidatingLLM.construction_count == 0
        assert (
            db.query(RAGGenerationModel).filter_by(class_name="ValidatingLLM").count()
            == 0
        )


def test_get_or_create_lazy_accepts_valid_params_without_constructing(
    client: TestClient,
):
    """Valid parameters still build a lazy proxy and construct nothing."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = _service(client, db)
        result = service.get_or_create_lazy("ValidatingLLM", {"context_window": 2048})

        assert isinstance(result.model, LazyLLM)
        assert result.model.is_loaded is False
        assert ValidatingLLM.construction_count == 0
        assert db.query(RAGGenerationModel).filter_by(
            id=result.db_record_id
        ).one().parameters == {"context_window": 2048}


def test_get_or_create_lazy_existing_row_with_removed_component(
    client: TestClient,
):
    """An existing row whose component is gone raises the not-found error."""
    session_factory = client.app.container["session_factory"]
    params = {"temperature": 0.5}

    with session_factory() as db:
        sorted_params = normalize_params(params)
        db.add(
            RAGGenerationModel(
                class_name="RemovedLLM",
                parameters=sorted_params,
                parameters_hash=build_parameters_hash(
                    {"__class__": "RemovedLLM", **sorted_params}
                ),
            )
        )
        db.commit()

        service = _service(client, db)

        with pytest.raises(RAGComponentNotFoundError):
            service.get_or_create_lazy("RemovedLLM", params)


def test_retrieval_service_inherits_the_lazy_path(client: TestClient):
    """``RetrievalLLMService`` keeps its own table and result type."""
    registry = client.app.container["component_registry"]
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = RetrievalLLMService(db, registry)
        result = service.get_or_create_lazy("CountingLLM", {})

        assert isinstance(result, RetrievalLLMServiceResult)
        assert isinstance(result.model, LazyLLM)
        assert CountingLLM.construction_count == 0

        row = db.query(RAGRetrievalModel).filter_by(id=result.db_record_id).one()
        assert row.class_name == "CountingLLM"


def test_build_pipeline_rejects_invalid_nested_llm_without_constructing(
    client: TestClient,
):
    """Pipeline assembly fails on bad nested LLM params without loading weights."""
    tag = uuid.uuid4().hex[:8]
    suffix = f"_lazy_validation_{tag}"
    document_id = _create_test_document(client, suffix=suffix)
    document_path = write_test_doc_file(suffix, RAG_E2E_DOC_TEXT)

    try:
        session_factory = client.app.container["session_factory"]
        registry = client.app.container["component_registry"]
        config = client.app.container["config"]

        with session_factory() as db:
            session = GenerativeSession(
                task_name="RAGTask",
                model_name="RAGPipeline",
                parameters={"documents": [document_id]},
                name=f"lazy_validation_{tag}",
                description=None,
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            pipeline_config = RAGPipelineConfig.from_kwargs(
                session_id=session.id,
                db=db,
                component_registry=registry,
                env_RAG_path=config["RAG_PATH"],
                documents=[document_id],
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
                    "component": "CountingLLM",
                    "params": {"temperature": 0.2},
                },
                query_transformation={
                    "component": "LLMQueryRewriter",
                    "params": {
                        "prompt": {
                            "component": "DefaultQueryRewritingPrompt",
                            "params": {"language": "en"},
                        },
                        "llm_model": {
                            "component": "ValidatingLLM",
                            "params": {"context_window": "not-a-number"},
                        },
                        "history_window": 2,
                    },
                },
            )

            ValidatingLLM.construction_count = 0
            setup_service = SetupService(db, registry, config["RAG_PATH"])

            with pytest.raises(ValidationError):
                setup_service.build_pipeline(pipeline_config)

            assert ValidatingLLM.construction_count == 0
    finally:
        with contextlib.suppress(OSError):
            os.remove(document_path)


def test_lazy_probe_lifecycle(client: TestClient):
    """Direct probe: 0 constructed at lookup, 1 after use, 0 live after close."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = _service(client, db)
        result = service.get_or_create_lazy("CountingLLM", {"temperature": 0.3})
        row_exists = (
            db.query(RAGGenerationModel).filter_by(id=result.db_record_id).count() == 1
        )
        print(
            "\n[probe] after get_or_create_lazy: "
            f"constructed={CountingLLM.construction_count} "
            f"loaded={result.model.is_loaded} row_exists={row_exists}"
        )
        assert CountingLLM.construction_count == 0
        assert row_exists

        result.model.generate([{"role": "user", "content": "hi"}])
        print(
            "[probe] after generate: "
            f"constructed={CountingLLM.construction_count} "
            f"loaded={result.model.is_loaded}"
        )
        assert CountingLLM.construction_count == 1

        result.model.close()
        print(
            "[probe] after close: "
            f"constructed={CountingLLM.construction_count} "
            f"loaded={result.model.is_loaded}"
        )
        assert result.model.is_loaded is False
