"""Tests for the resolved-configuration and index-status endpoints.

Both endpoints exist so the frontend never has to translate class names, guess
defaults, or work out whether a session's documents are already indexed. These
tests pin exactly that: what comes back is renderable as-is.
"""

import contextlib
import os
import tempfile
import uuid

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import RunStatus
from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.dependencies.database.models import (
    GenerativeProcess,
    ProcessData,
)
from DashAI.back.job.RAG_job import RAGJob
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from tests.back.RAG.conftest import RAG_E2E_DOC_TEXT, _create_test_document

STUB_ANSWER = "stub answer"


class StubConfigLLMSchema(BaseSchema):
    """Empty schema — the stub model accepts any (empty) parameter set."""


class StubConfigLLM(TextToTextGenerationTaskModel):
    """Deterministic text-to-text model, so no real inference happens."""

    SCHEMA = StubConfigLLMSchema

    def __init__(self, **kwargs):
        """Store parameters without initialising the base class."""
        self.parameters = {}

    def generate(self, prompt):
        """Return a fixed stub answer."""
        return [STUB_ANSWER]


@pytest.fixture(scope="module", autouse=True)
def register_stub_llm(client: TestClient) -> None:
    """Register the stub generation model used by every session here."""
    client.app.container["component_registry"].register_component(StubConfigLLM)


@pytest.fixture(scope="module")
def indexed_document(client: TestClient) -> int:
    """A document whose file actually exists, so the pipeline can chunk it."""
    suffix = f"_config_{uuid.uuid4().hex[:8]}"
    doc_id = _create_test_document(client, suffix=suffix)
    path = os.path.join(tempfile.gettempdir(), f"test_doc{suffix}.txt")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(RAG_E2E_DOC_TEXT)
    yield doc_id
    with contextlib.suppress(OSError):
        os.remove(path)


def _base_generation_model() -> dict:
    """Return the stub generation model reference used by these tests."""
    return {"component": "StubConfigLLM", "params": {}}


def _create_minimal_session(client: TestClient, doc_id: int, name: str) -> int:
    """Create a RAG session from the minimum the API accepts."""
    response = client.post(
        "/api/v1/generative-session/",
        json={
            "model_name": "RAGPipeline",
            "task_name": "RAGTask",
            "name": name,
            "parameters": {
                "documents": [doc_id],
                "generation_model": {"component": "StubConfigLLM", "params": {}},
            },
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _run_one_chat_turn(client: TestClient, session_id: int) -> None:
    """Drive a single RAGJob turn, which is what actually indexes documents."""
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        process = GenerativeProcess(session_id=session_id, status=RunStatus.NOT_STARTED)
        db.add(process)
        db.commit()
        db.refresh(process)
        process_id = process.id
        db.add(
            ProcessData(
                process_id=process_id,
                is_input=True,
                data="Tell me about DashAI",
                data_type="str",
            )
        )
        db.commit()
    RAGJob(generative_process_id=process_id).run()


# ===================================================================
# Resolved configuration
# ===================================================================


def test_configuration_never_exposes_class_names(
    client: TestClient, indexed_document: int
):
    session_id = _create_minimal_session(
        client, indexed_document, "config_no_class_names"
    )

    response = client.get(f"/api/v1/rag/sessions/{session_id}/configuration")
    assert response.status_code == 200, response.text
    data = response.json()

    for key in ("chunking_model", "retriever_model", "prompt"):
        section = data[key]
        assert section["registered"] is True
        assert section["display_name"] != section["component"], (
            f"{key} still shows the raw class name {section['component']!r}"
        )
        assert section["section_name"]


def test_configuration_labels_every_parameter(
    client: TestClient, indexed_document: int
):
    session_id = _create_minimal_session(client, indexed_document, "config_labels")
    data = client.get(f"/api/v1/rag/sessions/{session_id}/configuration").json()

    chunking_params = {p["name"]: p for p in data["chunking_model"]["params"]}
    assert chunking_params["chunk_size"]["label"] == "Chunk size"
    assert chunking_params["chunk_size"]["value"] == 500
    assert chunking_params["chunk_overlap"]["label"] == "Chunk overlap"


def test_configuration_names_the_matching_presets(
    client: TestClient, indexed_document: int
):
    session_id = _create_minimal_session(client, indexed_document, "config_presets")
    data = client.get(f"/api/v1/rag/sessions/{session_id}/configuration").json()

    assert data["chunking_model"]["preset_key"] == "paragraph"
    assert data["chunking_model"]["preset_display_name"] == "Paragraph length"
    assert data["retriever_model"]["preset_key"] == "keyword"
    assert data["retriever_model"]["preset_display_name"] == "Keyword"


def test_configuration_is_localized(client: TestClient, indexed_document: int):
    session_id = _create_minimal_session(client, indexed_document, "config_localized")
    data = client.get(
        f"/api/v1/rag/sessions/{session_id}/configuration",
        headers={"Accept-Language": "es"},
    ).json()

    assert data["chunking_model"]["section_name"] == "Fragmentación"
    assert data["chunking_model"]["preset_display_name"] == "Largo de un párrafo"
    label = data["chunking_model"]["params"][0]["label"]
    assert isinstance(label, str), "labels must arrive as plain strings"


def test_configuration_reports_the_context_budget(
    client: TestClient, indexed_document: int
):
    session_id = _create_minimal_session(client, indexed_document, "config_budget")
    budget = client.get(f"/api/v1/rag/sessions/{session_id}/configuration").json()[
        "context_budget"
    ]

    # 500-character chunks ≈ 125 tokens each, times the default top_k of 10.
    assert budget["used_by_chunks"] == 125 * 10
    assert budget["available"] > 0
    assert budget["is_valid"] is True
    assert (
        budget["available"]
        == budget["context_window"]
        - budget["used_by_chunks"]
        - budget["used_by_prompt"]
        - budget["max_tokens"]
    )


def test_default_session_context_budget_is_usable(
    client: TestClient, indexed_document: int
):
    """A session created from the defaults must actually fit in its context.

    Every text-generation model ships a 512-token ``context_window``
    placeholder, which no RAG configuration fits. The backend widens it for RAG
    sessions; if that stops happening, a brand-new session opens with a red
    "insufficient context" warning.
    """
    session_id = _create_minimal_session(
        client, indexed_document, "config_default_budget"
    )
    budget = client.get(f"/api/v1/rag/sessions/{session_id}/configuration").json()[
        "context_budget"
    ]

    assert budget["is_valid"] is True, (
        f"the default configuration does not fit its context window: {budget}"
    )
    assert budget["available"] > 0


def test_explicit_context_window_survives_the_override(
    client: TestClient, indexed_document: int
):
    """A context window the caller sets is never overridden."""
    base = _base_generation_model()
    base["params"] = {"context_window": 4096}
    response = client.post(
        "/api/v1/generative-session/",
        json={
            "model_name": "RAGPipeline",
            "task_name": "RAGTask",
            "name": "config_explicit_window",
            "parameters": {
                "documents": [indexed_document],
                "generation_model": base,
            },
        },
    )
    assert response.status_code == 201, response.text
    stored = response.json()["parameters"]["generation_model"]["params"]
    assert stored["context_window"] == 4096


def test_configuration_survives_an_unregistered_component(
    client: TestClient, indexed_document: int
):
    """An uninstalled plugin must degrade to a raw name, not break the page."""
    session_id = _create_minimal_session(client, indexed_document, "config_unknown")
    response = client.put(
        f"/api/v1/generative-session/{session_id}/parameters",
        json={
            "chunking_model": {
                "component": "CharacterChunkModel",
                "params": {"chunk_size": 321, "chunk_overlap": 32},
            }
        },
    )
    assert response.status_code == 200, response.text

    session_factory = client.app.container["session_factory"]
    from DashAI.back.dependencies.database.models import GenerativeSession

    with session_factory() as db:
        session = db.get(GenerativeSession, session_id)
        parameters = dict(session.parameters)
        parameters["chunking_model"] = {"component": "GoneAwayChunker", "params": {}}
        session.parameters = parameters
        db.commit()

    data = client.get(f"/api/v1/rag/sessions/{session_id}/configuration").json()
    assert data["chunking_model"]["registered"] is False
    assert data["chunking_model"]["display_name"] == "GoneAwayChunker"


def test_configuration_404s_for_an_unknown_session(client: TestClient):
    assert client.get("/api/v1/rag/sessions/999999/configuration").status_code == 404


# ===================================================================
# Index status
# ===================================================================


def test_index_status_starts_not_indexed(client: TestClient, indexed_document: int):
    session_id = _create_minimal_session(client, indexed_document, "index_fresh")

    data = client.get(f"/api/v1/rag/sessions/{session_id}/index-status").json()
    assert data["status"] == "not_indexed"
    assert data["total_chunks"] == 0
    assert data["retriever_ready"] is False
    assert [d["document_id"] for d in data["documents"]] == [indexed_document]
    assert data["documents"][0]["indexed"] is False
    assert data["documents"][0]["file_name"]
    assert isinstance(data["message"], str)
    assert data["message"]


def test_index_status_becomes_indexed_then_stale(
    client: TestClient, indexed_document: int
):
    session_id = _create_minimal_session(client, indexed_document, "index_lifecycle")

    _run_one_chat_turn(client, session_id)

    data = client.get(f"/api/v1/rag/sessions/{session_id}/index-status").json()
    assert data["status"] == "indexed", data
    assert data["total_chunks"] > 0
    assert data["retriever_ready"] is True
    assert data["documents"][0]["chunks"] == data["total_chunks"]

    # Changing the chunking strategy invalidates the index for the new config,
    # but the session has been indexed before — that is the "stale" case.
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

    data = client.get(
        f"/api/v1/rag/sessions/{session_id}/index-status",
        headers={"Accept-Language": "es"},
    ).json()
    assert data["status"] == "stale", data
    assert data["total_chunks"] == 0
    assert "reindexar" in data["message"]


def test_index_status_404s_for_an_unknown_session(client: TestClient):
    assert client.get("/api/v1/rag/sessions/999999/index-status").status_code == 404
