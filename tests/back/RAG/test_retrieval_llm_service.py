"""Tests for ``RetrievalLLMService`` lookup-or-create persistence.

Mirrors ``test_RAG_llm_service_collision.py``: the service must reuse a
record when the same component and parameters are requested, create a new
one otherwise, persist the columns in ``rag_retrieval_model`` and reject a
registered component that is not a ``TextToTextGenerationTaskModel``.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.dependencies.database.models import RAGRetrievalModel
from DashAI.back.models.RAG.exceptions import RAGGenerationModelError
from DashAI.back.models.RAG.prompts.base_prompt import BasePrompt
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from DashAI.back.services.RAG.retrieval_llm_service import (
    RetrievalLLMService,
    RetrievalLLMServiceResult,
)


class StubRetrievalLLMSchema(BaseSchema):
    """Empty schema for the retrieval stub LLM."""


class StubRetrievalLLM(TextToTextGenerationTaskModel):
    """Minimal LLM stub used to exercise the retrieval table."""

    SCHEMA = StubRetrievalLLMSchema

    def __init__(self, **kwargs):
        self.parameters = {}

    def generate(self, prompt):
        return ["stub retrieval answer"]


class StubOtherRetrievalLLM(TextToTextGenerationTaskModel):
    """Second LLM stub with a distinct class name."""

    SCHEMA = StubRetrievalLLMSchema

    def __init__(self, **kwargs):
        self.parameters = {}

    def generate(self, prompt):
        return ["stub other answer"]


class NotAnLLMPrompt(BasePrompt):
    """Registered Prompt component that must be rejected by the service."""

    SCHEMA = StubRetrievalLLMSchema

    def __init__(self, **kwargs):
        pass


@pytest.fixture(scope="module", autouse=True)
def register_retrieval_stubs(client: TestClient) -> None:
    """Register the stub components used by every test in this module."""
    registry = client.app.container["component_registry"]
    registry.register_component(StubRetrievalLLM)
    registry.register_component(StubOtherRetrievalLLM)
    registry.register_component(NotAnLLMPrompt)


@pytest.fixture(autouse=True)
def clean_retrieval_table(client: TestClient) -> None:
    """Empty ``rag_retrieval_model`` so each test starts from a clean slate."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        db.query(RAGRetrievalModel).delete()
        db.commit()


def _service(client: TestClient, db):
    registry = client.app.container["component_registry"]
    return RetrievalLLMService(db, registry)


def test_get_or_create_reuses_same_record(client: TestClient):
    """The same component and params yield the same DB record id."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = _service(client, db)
        before = db.query(RAGRetrievalModel).count()
        first = service.get_or_create("StubRetrievalLLM", {"temperature": 0.2})
        second = service.get_or_create("StubRetrievalLLM", {"temperature": 0.2})

        assert isinstance(first, RetrievalLLMServiceResult)
        assert isinstance(first.model, StubRetrievalLLM)
        assert first.db_record_id == second.db_record_id
        assert db.query(RAGRetrievalModel).count() == before + 1


def test_get_or_create_different_params_inserts_new_row(client: TestClient):
    """Different parameters produce a distinct record."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = _service(client, db)
        before = db.query(RAGRetrievalModel).count()
        first = service.get_or_create("StubRetrievalLLM", {"temperature": 0.2})
        second = service.get_or_create("StubRetrievalLLM", {"temperature": 0.9})

        assert first.db_record_id != second.db_record_id
        assert db.query(RAGRetrievalModel).count() == before + 2


def test_get_or_create_different_component_same_params(client: TestClient):
    """Same params on different LLM classes must not collide."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = _service(client, db)
        before = db.query(RAGRetrievalModel).count()
        first = service.get_or_create("StubRetrievalLLM", {})
        second = service.get_or_create("StubOtherRetrievalLLM", {})

        assert isinstance(first.model, StubRetrievalLLM)
        assert isinstance(second.model, StubOtherRetrievalLLM)
        assert first.db_record_id != second.db_record_id
        assert db.query(RAGRetrievalModel).count() == before + 2


def test_persisted_columns_round_trip(client: TestClient):
    """``class_name`` and the normalised ``parameters`` are persisted."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = _service(client, db)
        result = service.get_or_create("StubRetrievalLLM", {"z": 1, "a": 2})

        row = db.query(RAGRetrievalModel).filter_by(id=result.db_record_id).one()
        assert row.class_name == "StubRetrievalLLM"
        assert row.parameters == {"a": 2, "z": 1}
        assert row.parameters_hash


def test_non_llm_component_raises(client: TestClient):
    """A registered non-LLM component raises ``RAGGenerationModelError``."""
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = _service(client, db)
        with pytest.raises(RAGGenerationModelError):
            service.get_or_create("NotAnLLMPrompt", {})
