"""Regression test for the LLMService hash-collision bug (now fixed).

``LLMService.get_or_create()`` must cache LLM records by the combination
of ``(class_name, parameters_hash)`` — not by ``parameters_hash`` alone.
Two different LLM components configured with identical parameters (e.g.
both ``{}``) must NOT collide: each ``get_or_create()`` call must return
a model of the requested component class.

This test guards against regressions of the fix that added ``class_name``
to the DB lookup filter in ``llm_service.py``.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from DashAI.back.services.RAG.llm_service import LLMService


class StubACollisionSchema(BaseSchema):
    """Empty schema for collision stub A."""


class StubACollision(TextToTextGenerationTaskModel):
    """First stub LLM used to reproduce the hash collision."""

    SCHEMA = StubACollisionSchema

    def __init__(self, **kwargs):
        self.parameters = {}

    def generate(self, prompt):
        return ["stub A answer"]


class StubBCollisionSchema(BaseSchema):
    """Empty schema for collision stub B."""


class StubBCollision(TextToTextGenerationTaskModel):
    """Second stub LLM with identical empty parameters."""

    SCHEMA = StubBCollisionSchema

    def __init__(self, **kwargs):
        self.parameters = {}

    def generate(self, prompt):
        return ["stub B answer"]


@pytest.fixture(scope="module", autouse=True)
def register_collision_stubs(client: TestClient) -> None:
    """Register both collision stubs in the component registry."""
    registry = client.app.container["component_registry"]
    registry.register_component(StubACollision)
    registry.register_component(StubBCollision)


def test_llm_service_get_or_create_collision(client: TestClient):
    """Two LLM components with identical params must not collide.

    Each ``get_or_create()`` call must return a model of the requested
    component class, even when both use identical empty parameters.
    """
    registry = client.app.container["component_registry"]
    session_factory = client.app.container["session_factory"]

    with session_factory() as db:
        service = LLMService(db, registry)

        result_a = service.get_or_create("StubACollision", {})
        assert isinstance(result_a.model, StubACollision)

        result_b = service.get_or_create("StubBCollision", {})
        assert isinstance(result_b.model, StubBCollision)
