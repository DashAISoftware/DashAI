"""Integration tests for the optional query transformation stage in sessions.

Covers POST validation (structure, subclass checks, template injection),
PUT enable/disable semantics and the GET round trip. Mirrors the fixtures of
``test_RAG_session_validation.py``: the module-scoped ``client`` fixture and a
stub LLM registered into the component registry.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)


class StubTransformationLLMSchema(BaseSchema):
    """Empty schema for the transformation stub LLM."""


class StubTransformationLLM(TextToTextGenerationTaskModel):
    """Deterministic stub LLM for transformation-stage session tests."""

    SCHEMA = StubTransformationLLMSchema

    def __init__(self, **kwargs):
        self.parameters = dict(kwargs)

    def generate(self, prompt):
        return ['{"name": "rewrite_query", "arguments": {"query": "q"}}']


@pytest.fixture(scope="module", autouse=True)
def register_stub_llm(client: TestClient) -> None:
    registry = client.app.container["component_registry"]
    registry.register_component(StubTransformationLLM)


def _base_session_params() -> dict:
    return {
        "model_name": "RAGPipeline",
        "task_name": "RAGTask",
        "name": f"transformation_{uuid.uuid4().hex}",
        "description": None,
        "parameters": {
            "chunking_model": {
                "component": "CharacterChunkModel",
                "params": {"chunk_size": 400, "chunk_overlap": 40},
            },
            "retriever_model": {
                "component": "BM25Retriever",
                "params": {
                    "BM25Vectorizer": {
                        "component": "BM25VectorizerModel",
                        "params": {
                            "strip_accents": None,
                            "lowercase": True,
                            "stop_words": None,
                            "max_df": 1.0,
                            "min_df": 0.0,
                            "max_features": None,
                        },
                    },
                    "k1": 1.5,
                    "b": 0.75,
                    "delta": 0.0,
                    "similarity_function": "cosine",
                    "top_k": 5,
                },
            },
            "generation_model": {
                "component": "Llama32_1BInstruct",
                "params": {
                    "max_tokens": 100,
                    "temperature": 0.7,
                    "frequency_penalty": 0.1,
                    "context_window": 512,
                    "device": "CPU",
                },
            },
            "prompt": {
                "component": "DefaultRAGGenerationPrompt",
                "params": {"language": "en"},
            },
        },
    }


def _rewriter_ref(template: str | None = None) -> dict:
    prompt: dict = {
        "component": "DefaultQueryRewritingPrompt",
        "params": {"language": "en"},
    }
    if template is not None:
        prompt["params"]["template"] = template
    return {
        "component": "LLMQueryRewriter",
        "params": {
            "prompt": prompt,
            "llm_model": {"component": "StubTransformationLLM", "params": {}},
        },
    }


def _qwen_rewriter_ref(llm_params: dict | None = None) -> dict:
    """Return a rewriter reference backed by the real GGUF Qwen component."""
    return {
        "component": "LLMQueryRewriter",
        "params": {
            "prompt": {
                "component": "DefaultQueryRewritingPrompt",
                "params": {"language": "en"},
            },
            "llm_model": {
                "component": "Qwen25_15BInstruct",
                "params": dict(llm_params or {}),
            },
        },
    }


# ===================================================================
# POST — creation with a transformation stage
# ===================================================================


class TestCreateWithTransformation:
    def test_create_with_transformation_injects_default_template(
        self, client: TestClient
    ):
        params = _base_session_params()
        params["parameters"]["query_transformation"] = _rewriter_ref()

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, response.text

        stored = response.json()["parameters"]["query_transformation"]
        assert stored["component"] == "LLMQueryRewriter"
        assert stored["params"]["prompt"]["component"] == "DefaultQueryRewritingPrompt"
        injected = stored["params"]["prompt"]["params"]["template"]
        assert "rewrite_query" in injected

    def test_create_fills_history_window_default(self, client: TestClient):
        params = _base_session_params()
        params["parameters"]["query_transformation"] = _rewriter_ref()

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, response.text
        stored = response.json()["parameters"]["query_transformation"]
        assert stored["params"]["history_window"] == 2

    def test_create_defaults_transformation_llm_context_window(
        self, client: TestClient
    ):
        params = _base_session_params()
        params["parameters"]["query_transformation"] = _qwen_rewriter_ref()

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, response.text
        stored = response.json()["parameters"]["query_transformation"]
        llm_params = stored["params"]["llm_model"]["params"]
        assert llm_params["context_window"] == 2048
        assert llm_params["max_tokens"] == 100

        fetched = client.get("/api/v1/generative-session/" + str(response.json()["id"]))
        assert fetched.status_code == 200, fetched.text
        fetched_llm = fetched.json()["parameters"]["query_transformation"]["params"][
            "llm_model"
        ]["params"]
        assert fetched_llm["context_window"] == 2048

    def test_create_explicit_transformation_llm_context_window_wins(
        self, client: TestClient
    ):
        params = _base_session_params()
        params["parameters"]["query_transformation"] = _qwen_rewriter_ref(
            {"context_window": 4096}
        )

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, response.text
        llm_params = response.json()["parameters"]["query_transformation"]["params"][
            "llm_model"
        ]["params"]
        assert llm_params["context_window"] == 4096

    def test_create_without_transformation_omits_key(self, client: TestClient):
        params = _base_session_params()
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, response.text
        assert "query_transformation" not in response.json()["parameters"]

    def test_explicit_null_is_stored_as_null(self, client: TestClient):
        params = _base_session_params()
        params["parameters"]["query_transformation"] = None
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, response.text
        assert response.json()["parameters"]["query_transformation"] is None

    @pytest.mark.parametrize(
        "bad_value",
        ["not_a_dict", 42, ["x"], {"component": "LLMQueryRewriter"}, {"params": {}}],
    )
    def test_bad_structure_rejected(self, client: TestClient, bad_value):
        params = _base_session_params()
        params["parameters"]["query_transformation"] = bad_value
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, response.text
        assert "query_transformation" in response.text

    def test_unknown_transformation_component_rejected(self, client: TestClient):
        params = _base_session_params()
        ref = _rewriter_ref()
        ref["component"] = "NonExistentTransformer"
        params["parameters"]["query_transformation"] = ref
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, response.text
        assert "not registered" in response.text.lower()

    def test_wrong_nested_prompt_class_rejected(self, client: TestClient):
        params = _base_session_params()
        ref = _rewriter_ref()
        ref["params"]["prompt"] = {
            "component": "DefaultRAGGenerationPrompt",
            "params": {"language": "en"},
        }
        params["parameters"]["query_transformation"] = ref
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, response.text
        assert "QueryTransformationPrompt" in response.text

    def test_missing_llm_model_rejected(self, client: TestClient):
        params = _base_session_params()
        ref = _rewriter_ref()
        del ref["params"]["llm_model"]
        params["parameters"]["query_transformation"] = ref
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, response.text
        assert "llm_model" in response.text

    def test_malformed_nested_template_rejected(self, client: TestClient):
        params = _base_session_params()
        ref = _rewriter_ref()
        ref["params"]["prompt"] = {
            "component": "CustomQueryRewritingPrompt",
            "params": {"template": "no placeholders at all"},
        }
        params["parameters"]["query_transformation"] = ref
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, response.text
        lowered = response.text.lower()
        assert "placeholder" in lowered or "template" in lowered

    @pytest.mark.parametrize("bad_params", ["boom-not-a-dict", ["boom"], 42])
    def test_nested_prompt_params_non_dict_rejected(
        self, client: TestClient, bad_params
    ):
        params = _base_session_params()
        ref = _rewriter_ref()
        ref["params"]["prompt"]["params"] = bad_params
        params["parameters"]["query_transformation"] = ref
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, response.text
        assert "query_transformation.params.prompt" in response.text
        assert "must be a dict" in response.text

    @pytest.mark.parametrize("bad_params", ["boom-not-a-dict", ["boom"], 42])
    def test_nested_llm_params_non_dict_rejected(self, client: TestClient, bad_params):
        params = _base_session_params()
        ref = _rewriter_ref()
        ref["params"]["llm_model"]["params"] = bad_params
        params["parameters"]["query_transformation"] = ref
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, response.text
        assert "query_transformation.params.llm_model" in response.text
        assert "must be a dict" in response.text

    @pytest.mark.parametrize("bad_component", [123, ["x"], True])
    def test_nested_prompt_component_non_str_rejected(
        self, client: TestClient, bad_component
    ):
        params = _base_session_params()
        ref = _rewriter_ref()
        ref["params"]["prompt"]["component"] = bad_component
        params["parameters"]["query_transformation"] = ref
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, response.text
        assert "query_transformation.params.prompt" in response.text
        assert "must be a string" in response.text

    @pytest.mark.parametrize("bad_component", [123, ["x"], True])
    def test_nested_llm_component_non_str_rejected(
        self, client: TestClient, bad_component
    ):
        params = _base_session_params()
        ref = _rewriter_ref()
        ref["params"]["llm_model"]["component"] = bad_component
        params["parameters"]["query_transformation"] = ref
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, response.text
        assert "query_transformation.params.llm_model" in response.text
        assert "must be a string" in response.text

    def test_technique_prompt_family_mismatch_rejected(self, client: TestClient):
        params = _base_session_params()
        ref = _rewriter_ref()
        ref["params"]["prompt"] = {
            "component": "DefaultQueryExpansionPrompt",
            "params": {"language": "en"},
        }
        params["parameters"]["query_transformation"] = ref
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, response.text
        assert "family" in response.text
        assert "LLMQueryRewriter" in response.text
        assert "DefaultQueryExpansionPrompt" in response.text

    def test_custom_prompt_blank_template_rejected(self, client: TestClient):
        params = _base_session_params()
        ref = _rewriter_ref()
        ref["params"]["prompt"] = {
            "component": "CustomQueryRewritingPrompt",
            "params": {"template": "   "},
        }
        params["parameters"]["query_transformation"] = ref
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, response.text
        assert "blank" in response.text.lower()

    def test_custom_prompt_no_template_rejected(self, client: TestClient):
        params = _base_session_params()
        ref = _rewriter_ref()
        ref["params"]["prompt"] = {
            "component": "CustomQueryRewritingPrompt",
            "params": {},
        }
        params["parameters"]["query_transformation"] = ref
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, response.text
        assert "blank" in response.text.lower()

    def test_non_string_template_rejected(self, client: TestClient):
        params = _base_session_params()
        ref = _rewriter_ref()
        ref["params"]["prompt"] = {
            "component": "CustomQueryRewritingPrompt",
            "params": {"template": 42},
        }
        params["parameters"]["query_transformation"] = ref
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, response.text
        assert "must be a string" in response.text

    def test_default_prompt_blank_template_injected(self, client: TestClient):
        params = _base_session_params()
        params["parameters"]["query_transformation"] = _rewriter_ref(template="   ")
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, response.text
        stored = response.json()["parameters"]["query_transformation"]
        template = stored["params"]["prompt"]["params"]["template"]
        assert template.strip()
        assert "rewrite_query" in template

    def test_nested_prompt_language_defaults_resolved(self, client: TestClient):
        params = _base_session_params()
        ref = _rewriter_ref()
        ref["params"]["prompt"] = {
            "component": "DefaultQueryRewritingPrompt",
            "params": {},
        }
        params["parameters"]["query_transformation"] = ref
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, response.text
        stored = response.json()["parameters"]["query_transformation"]
        prompt_params = stored["params"]["prompt"]["params"]
        assert prompt_params["language"] == "en"
        assert prompt_params["template"].strip()
        assert "rewrite_query" in prompt_params["template"]

        session_id = response.json()["id"]
        fetched = client.get(f"/api/v1/generative-session/{session_id}")
        assert fetched.status_code == 200, fetched.text
        fetched_params = fetched.json()["parameters"]["query_transformation"]["params"][
            "prompt"
        ]["params"]
        assert fetched_params["language"] == "en"
        assert fetched_params["template"].strip()


# ===================================================================
# PUT — enable / disable semantics
# ===================================================================


class TestUpdateTransformation:
    @staticmethod
    def _create_session(client: TestClient) -> int:
        params = _base_session_params()
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, response.text
        return response.json()["id"]

    def test_enable_on_existing_session(self, client: TestClient):
        session_id = self._create_session(client)
        response = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"query_transformation": _rewriter_ref()},
        )
        assert response.status_code == 200, response.text
        stored = response.json()["parameters"]["query_transformation"]
        assert stored["component"] == "LLMQueryRewriter"
        assert "rewrite_query" in stored["params"]["prompt"]["params"]["template"]

    def test_enable_defaults_transformation_llm_context_window(
        self, client: TestClient
    ):
        session_id = self._create_session(client)
        response = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"query_transformation": _qwen_rewriter_ref()},
        )
        assert response.status_code == 200, response.text
        llm_params = response.json()["parameters"]["query_transformation"]["params"][
            "llm_model"
        ]["params"]
        assert llm_params["context_window"] == 2048

    def test_disable_with_null(self, client: TestClient):
        session_id = self._create_session(client)
        enabled = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"query_transformation": _rewriter_ref()},
        )
        assert enabled.status_code == 200, enabled.text

        disabled = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"query_transformation": None},
        )
        assert disabled.status_code == 200, disabled.text
        assert disabled.json()["parameters"]["query_transformation"] is None

    def test_get_returns_transformation_config(self, client: TestClient):
        session_id = self._create_session(client)
        client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"query_transformation": _rewriter_ref()},
        )
        fetched = client.get(f"/api/v1/generative-session/{session_id}")
        assert fetched.status_code == 200, fetched.text
        stored = fetched.json()["parameters"]["query_transformation"]
        assert stored["component"] == "LLMQueryRewriter"
        assert stored["params"]["prompt"]["component"] == "DefaultQueryRewritingPrompt"
