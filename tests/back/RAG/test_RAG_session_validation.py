"""Exhaustive integration tests for RAG session creation and parameter update.

Tests cover:
  - POST /api/v1/generative-session/  — RAG session creation with validation
  - PUT  /api/v1/generative-session/{id}/parameters — partial parameter updates
  - POST /api/v1/prompt/            — prompt template validation

Architecture notes
------------------
The RAGPipelineSchema (used for both POST and PUT validation) only validates
the *structure* of component fields: every ``component_field(parent=...)``
requires a dict with ``{"component": str, "params": dict}``.  It does NOT
resolve component names against the registry — unknown names are stored as-is
and validated at pipeline runtime.

Document existence is only enforced during POST (via
``DocumentService.validate_exist``), NOT during PUT.
"""

import pytest
from fastapi.testclient import TestClient

from tests.back.RAG.conftest import _create_test_document

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def test_doc_id(client: TestClient) -> int:
    """Module-scoped test document shared across all tests in this file."""
    return _create_test_document(client, suffix="_session_validation")


def _base_session_params(test_doc_id: int) -> dict:
    """Return the minimal valid RAG session payload (BM25 + Llama + DefaultPrompt)."""
    return {
        "model_name": "RAGPipeline",
        "task_name": "RAGTask",
        "parameters": {
            "documents": [test_doc_id],
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
        "name": "Session Validation Test",
        "description": None,
    }


# ===================================================================
# POST  /api/v1/generative-session/
# ===================================================================


class TestCreateRAGSession:
    """RAG session creation — structural and business-rule validation."""

    # ------------------------------------------------------------------
    # Valid creation
    # ------------------------------------------------------------------

    def test_create_valid_rag_session(self, client: TestClient, test_doc_id: int):
        """Creates a session with ALL valid RAG parameters, asserts 201 and
        the full response shape."""
        params = _base_session_params(test_doc_id)
        params["name"] = "test_create_valid_rag_session"

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code}: {response.text}"
        )

        data = response.json()
        # --- top-level fields ---
        assert data["id"] is not None
        assert isinstance(data["id"], int)
        assert data["id"] > 0
        assert data["model_name"] == "RAGPipeline"
        assert data["task_name"] == "RAGTask"
        assert data["name"] == "test_create_valid_rag_session"
        assert data["description"] is None
        assert "created" in data
        assert "last_modified" in data
        assert data["created"] == data["last_modified"]  # initial creation
        assert "display_name" in data  # resolved from component_registry

        # --- parameters ---
        params_data = data["parameters"]
        assert params_data["documents"] == [test_doc_id]
        assert params_data["prompt"]["component"] == "DefaultRAGGenerationPrompt"
        assert params_data["chunking_model"]["component"] == "CharacterChunkModel"
        assert params_data["retriever_model"]["component"] == "BM25Retriever"
        assert params_data["generation_model"]["component"] == "Llama32_1BInstruct"

    def test_create_rag_session_with_custom_description(
        self, client: TestClient, test_doc_id: int
    ):
        """Session creation with a non-None description is stored correctly."""
        params = _base_session_params(test_doc_id)
        params["name"] = "test_create_with_description"
        params["description"] = "A test session for RAG validation"

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, response.text
        assert response.json()["description"] == "A test session for RAG validation"

    @pytest.mark.parametrize("missing_key", ["model_name", "task_name", "name"])
    def test_create_rag_session_missing_top_level_field(
        self, client: TestClient, test_doc_id: int, missing_key: str
    ):
        """Omitting a top-level required field returns 422 Unprocessable Entity."""
        params = _base_session_params(test_doc_id)
        params["name"] = f"test_missing_{missing_key}"
        del params[missing_key]

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 422, (
            f"Missing '{missing_key}' should yield 422, "
            f"got {response.status_code}: {response.text}"
        )

    # ------------------------------------------------------------------
    # Missing parameter keys: required ones fail, defaulted ones are filled
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "missing_param_key",
        ["generation_model", "documents"],
    )
    def test_create_rag_session_missing_required_parameter(
        self, client: TestClient, test_doc_id: int, missing_param_key: str
    ):
        """Omitting a key with no sensible default returns 400."""
        params = _base_session_params(test_doc_id)
        params["name"] = f"test_missing_param_{missing_param_key}"
        del params["parameters"][missing_param_key]

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, (
            f"Missing parameter '{missing_param_key}' should yield 400, "
            f"got {response.status_code}: {response.text}"
        )
        # The error detail should mention the missing field
        assert missing_param_key in response.text.lower()

    @pytest.mark.parametrize(
        "missing_param_key",
        ["prompt", "chunking_model", "retriever_model"],
    )
    def test_create_rag_session_defaults_missing_parameter(
        self, client: TestClient, test_doc_id: int, missing_param_key: str
    ):
        """Omitting a defaulted key succeeds and stores the backend default."""
        params = _base_session_params(test_doc_id)
        params["name"] = f"test_defaulted_param_{missing_param_key}"
        del params["parameters"][missing_param_key]

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, (
            f"Missing parameter '{missing_param_key}' should be defaulted, "
            f"got {response.status_code}: {response.text}"
        )
        stored = response.json()["parameters"][missing_param_key]
        assert stored["component"], f"{missing_param_key} was not resolved"
        assert isinstance(stored["params"], dict)

    def test_create_rag_session_with_only_documents_and_model(
        self, client: TestClient, test_doc_id: int
    ):
        """Name, documents and a generation model are enough to create a session."""
        base = _base_session_params(test_doc_id)
        params = {
            "model_name": base["model_name"],
            "task_name": base["task_name"],
            "name": "test_minimal_creation",
            "parameters": {
                "documents": base["parameters"]["documents"],
                "generation_model": base["parameters"]["generation_model"],
            },
        }

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, response.text

        stored = response.json()["parameters"]
        for key in ("prompt", "chunking_model", "retriever_model"):
            assert stored[key]["component"], f"{key} was not defaulted"

    # ------------------------------------------------------------------
    # Component-structure validation
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("component_key", "bad_value"),
        [
            ("prompt", {"component": "CustomRAGGenerationPrompt"}),  # missing 'params'
            ("prompt", {"params": {"language": "en"}}),  # missing 'component'
            ("prompt", "not_a_dict"),  # wrong type
            (
                "chunking_model",
                {"component": "CharacterChunkModel"},
            ),  # missing 'params'
            ("chunking_model", 42),  # wrong type
        ],
    )
    def test_create_rag_session_bad_component_structure(
        self, client: TestClient, test_doc_id: int, component_key: str, bad_value
    ):
        """Malformed component dict (missing keys / wrong type) returns 400."""
        params = _base_session_params(test_doc_id)
        params["name"] = f"test_bad_struct_{component_key}"
        params["parameters"][component_key] = bad_value

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, (
            f"Bad '{component_key}' structure should yield 400, "
            f"got {response.status_code}: {response.text}"
        )

    # ------------------------------------------------------------------
    # Invalid component names  (now rejected with 400)
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("component_key", "invalid_name"),
        [
            ("prompt", "NonExistentPrompt"),
            ("chunking_model", "NonExistentChunker"),
            ("retriever_model", "NonExistentRetriever"),
            ("generation_model", "NonExistentLLM"),
        ],
    )
    def test_create_rag_session_invalid_component_name(
        self,
        client: TestClient,
        test_doc_id: int,
        component_key: str,
        invalid_name: str,
    ):
        """Non-existent component names now return 400 (validated against registry)."""
        params = _base_session_params(test_doc_id)
        params["name"] = f"test_bad_comp_{component_key}"

        # Replace the target component with an invalid one
        params["parameters"][component_key] = {
            "component": invalid_name,
            "params": _dummy_params_for(component_key),
        }

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, (
            f"Invalid component name '{invalid_name}' for '{component_key}' "
            f"should return 400, "
            f"got {response.status_code}: {response.text}"
        )
        assert "not registered" in response.text.lower()

    # ------------------------------------------------------------------
    # Invalid model / task name  (caught by registry lookup → 400)
    # ------------------------------------------------------------------

    def test_create_rag_session_invalid_model_name(
        self, client: TestClient, test_doc_id: int
    ):
        """A non-registered model_name returns 400."""
        params = _base_session_params(test_doc_id)
        params["name"] = "test_invalid_model_name"
        params["model_name"] = "TotallyNotRealModel"

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, (
            f"Expected 400 for unknown model, got {response.status_code}:"
            f" {response.text}"
        )

    def test_create_rag_session_invalid_task_name(
        self, client: TestClient, test_doc_id: int
    ):
        """A non-registered task_name returns 400."""
        params = _base_session_params(test_doc_id)
        params["name"] = "test_invalid_task_name"
        params["task_name"] = "NonExistentTask"

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, (
            f"Expected 400 for unknown task, got {response.status_code}:"
            f" {response.text}"
        )

    def test_create_rag_session_model_not_generative(
        self, client: TestClient, test_doc_id: int
    ):
        """A model that is not a subclass of BaseGenerativeModel returns 400.

        ``DummyClassifier`` is registered but is NOT a generative model.
        """
        params = _base_session_params(test_doc_id)
        params["name"] = "test_model_not_generative"
        params["model_name"] = "DummyClassifier"  # exists but is not generative

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, (
            f"Expected 400 for non-generative model, "
            f"got {response.status_code}: {response.text}"
        )

    # ------------------------------------------------------------------
    # Document validation
    # ------------------------------------------------------------------

    def test_create_rag_session_invalid_documents(
        self, client: TestClient, test_doc_id: int
    ):
        """Non-existent document IDs return 400 (caught by endpoint)."""
        params = _base_session_params(test_doc_id)
        params["name"] = "test_invalid_docs"
        params["parameters"]["documents"] = [99999]  # does not exist

        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 400

    def test_create_rag_session_empty_documents(
        self, client: TestClient, test_doc_id: int
    ):
        """Empty documents list is rejected with 400."""
        params = _base_session_params(test_doc_id)
        params["name"] = "test_empty_docs"
        params["parameters"]["documents"] = []

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, (
            f"Empty documents list should be rejected, "
            f"got {response.status_code}: {response.text}"
        )

    def test_create_rag_session_document_zero(
        self, client: TestClient, test_doc_id: int
    ):
        """Document ID = 0 returns 400 (caught by endpoint)."""
        params = _base_session_params(test_doc_id)
        params["name"] = "test_doc_id_zero"
        params["parameters"]["documents"] = [0]

        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 400

    def test_create_rag_session_document_negative(
        self, client: TestClient, test_doc_id: int
    ):
        """Negative document ID returns 400 (caught by endpoint)."""
        params = _base_session_params(test_doc_id)
        params["name"] = "test_doc_id_negative"
        params["parameters"]["documents"] = [-5]

        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 400

    # ------------------------------------------------------------------
    # Miscellaneous edge-cases
    # ------------------------------------------------------------------

    def test_create_rag_session_duplicate_name(
        self, client: TestClient, test_doc_id: int
    ):
        """Second creation with the same name returns 409 Conflict."""
        params = _base_session_params(test_doc_id)
        params["name"] = "test_duplicate_name"

        resp1 = client.post("/api/v1/generative-session/", json=params)
        assert resp1.status_code == 201, f"First creation failed: {resp1.text}"

        resp2 = client.post("/api/v1/generative-session/", json=params)
        assert resp2.status_code == 409, (
            f"Expected 409 for duplicate name, got {resp2.status_code}: {resp2.text}"
        )

    def test_create_rag_session_empty_name(self, client: TestClient, test_doc_id: int):
        """An empty or whitespace-only name may be treated differently by the
        schema — at minimum it should not crash."""
        params = _base_session_params(test_doc_id)
        params["name"] = ""

        response = client.post("/api/v1/generative-session/", json=params)
        # The GenerativeSessionParams schema requires name: str, so "" passes
        # Pydantic validation. The DB may or may not accept it.
        # Accept either 201 or 400/422 depending on backend validation.
        assert response.status_code in (201, 400, 422), (
            f"Unexpected status for empty name: {response.status_code}: {response.text}"
        )

    def test_create_rag_session_unknown_parameter_key(
        self, client: TestClient, test_doc_id: int
    ):
        """Extra unknown keys inside ``parameters``.

        Pydantic v2 BaseModel with default config ignores extra fields during
        ``model_validate``, so the unknown key is silently accepted (201).
        The key is also stored in the session parameters.
        """
        params = _base_session_params(test_doc_id)
        params["name"] = "test_unknown_param_key"
        params["parameters"]["unexpected_extra_key"] = "should_be_ignored"

        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 201, (
            f"Extra parameter key should be tolerated, "
            f"got {response.status_code}: {response.text}"
        )
        # The extra key may or may not be stored depending on model_validate
        # with extra='ignore'.  Just assert no crash.


# ===================================================================
# PUT endpoint: /api/v1/generative-session/{session_id}/parameters
# ===================================================================


class TestUpdateRAGSessionParams:
    """Parameter updates — partial merge, structural validation, edge-cases."""

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _create_session(client: TestClient, test_doc_id: int, name: str) -> dict:
        """Create a minimal valid session and return its JSON response."""
        params = _base_session_params(test_doc_id)
        params["name"] = name
        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 201, f"Session prereq failed: {resp.text}"
        return resp.json()

    # ------------------------------------------------------------------
    # Successful updates
    # ------------------------------------------------------------------

    def test_update_rag_session_partial(self, client: TestClient, test_doc_id: int):
        """Sends only ``generation_model`` change → 200 with merged params.

        Unchanged keys (prompt, chunking_model, …) must be preserved.
        """
        session = self._create_session(client, test_doc_id, "test_partial_update")
        session_id = session["id"]

        new_gen = {
            "component": "Llama32_1BInstruct",
            "params": {
                "max_tokens": 200,
                "temperature": 0.9,
                "frequency_penalty": 0.2,
                "context_window": 1024,
                "device": "CPU",
            },
        }
        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"generation_model": new_gen},
        )
        assert resp.status_code == 200, (
            f"Partial update failed: {resp.status_code}: {resp.text}"
        )

        data = resp.json()
        assert data["id"] == session_id
        gen = data["parameters"]["generation_model"]
        assert gen["component"] == "Llama32_1BInstruct"
        assert gen["params"]["temperature"] == 0.9
        assert gen["params"]["max_tokens"] == 200

        # Other keys must remain unchanged
        assert data["parameters"]["prompt"]["component"] == "DefaultRAGGenerationPrompt"
        assert (
            data["parameters"]["chunking_model"]["component"] == "CharacterChunkModel"
        )

    def test_update_rag_session_full_replacement(
        self, client: TestClient, test_doc_id: int
    ):
        """Replaces every RAG parameter at once → 200 with all new values."""
        session = self._create_session(client, test_doc_id, "test_full_replacement")
        session_id = session["id"]

        replacement = {
            "documents": [test_doc_id],
            "chunking_model": {
                "component": "RecursiveCharacterChunkModel",
                "params": {
                    "chunk_size": 500,
                    "chunk_overlap": 50,
                    "separators": ["\n\n", "\n", ".", " ", ""],
                },
            },
            "retriever_model": {
                "component": "TFIDFRetriever",
                "params": {
                    "TFIDFVectorizer": {
                        "component": "TFIDFVectorizerModel",
                        "params": {
                            "strip_accents": "None",
                            "lowercase": True,
                            "analyzer": "word",
                            "stop_words": [],
                            "ngram_range": [1, 1],
                            "max_df": 1.0,
                            "min_df": 0.0,
                            "max_features": 1000,
                            "norm": "l2",
                            "use_idf": True,
                            "smooth_idf": True,
                            "sublinear_tf": False,
                        },
                    },
                    "similarity_function": "cosine",
                    "top_k": 10,
                    "similarity_threshold": None,
                },
            },
            "generation_model": {
                "component": "Llama32_1BInstruct",
                "params": {
                    "max_tokens": 50,
                    "temperature": 0.5,
                    "frequency_penalty": 0.0,
                    "context_window": 512,
                    "device": "CPU",
                },
            },
            "prompt": {
                "component": "DefaultQARAGGenerationPrompt",
                "params": {"language": "en"},
            },
        }
        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json=replacement,
        )
        assert resp.status_code == 200, (
            f"Full replacement failed: {resp.status_code}: {resp.text}"
        )
        p = resp.json()["parameters"]
        assert p["prompt"]["component"] == "DefaultQARAGGenerationPrompt"
        assert p["chunking_model"]["component"] == "RecursiveCharacterChunkModel"
        assert p["retriever_model"]["component"] == "TFIDFRetriever"
        assert p["retriever_model"]["params"]["top_k"] == 10
        assert p["generation_model"]["component"] == "Llama32_1BInstruct"

    def test_update_rag_session_prompt_only(self, client: TestClient, test_doc_id: int):
        """Updates only the prompt component → 200, prompt changed, others preserved."""
        session = self._create_session(client, test_doc_id, "test_update_prompt_only")
        session_id = session["id"]

        new_prompt = {
            "component": "CustomRAGGenerationPrompt",
            "params": {"template": "Custom: {input}\nContext: {chunks}\nAnswer:"},
        }
        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"prompt": new_prompt},
        )
        assert resp.status_code == 200, resp.text
        prompt = resp.json()["parameters"]["prompt"]
        assert prompt["component"] == "CustomRAGGenerationPrompt"
        assert "{input}" in prompt["params"]["template"]
        assert "{chunks}" in prompt["params"]["template"]

    # ------------------------------------------------------------------
    # Empty / no-op updates
    # ------------------------------------------------------------------

    def test_update_rag_session_empty_body(self, client: TestClient, test_doc_id: int):
        """Empty dict ``{}`` → 200 no-op (merged params are identical to old)."""
        session = self._create_session(client, test_doc_id, "test_update_empty_body")
        session_id = session["id"]

        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={},
        )
        assert resp.status_code == 200, (
            f"Empty body should succeed, got {resp.status_code}: {resp.text}"
        )
        # All original parameters should be preserved
        assert resp.json()["parameters"]["prompt"]["component"] == (
            "DefaultRAGGenerationPrompt"
        )

    # ------------------------------------------------------------------
    # Invalid component names  (now rejected with 400)
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("component_key", "invalid_name"),
        [
            ("prompt", "NonExistentPrompt"),
            ("chunking_model", "NonExistentChunker"),
            ("retriever_model", "NonExistentRetriever"),
            ("generation_model", "NonExistentLLM"),
        ],
    )
    def test_update_rag_session_invalid_component(
        self,
        client: TestClient,
        test_doc_id: int,
        component_key: str,
        invalid_name: str,
    ):
        """Invalid component name in PUT now returns 400 (validated against
        registry)."""
        session = self._create_session(
            client, test_doc_id, f"test_update_invalid_{component_key}"
        )
        session_id = session["id"]

        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={
                component_key: {
                    "component": invalid_name,
                    "params": _dummy_params_for(component_key),
                }
            },
        )
        assert resp.status_code == 400, (
            f"Invalid component '{invalid_name}' should return 400, "
            f"got {resp.status_code}: {resp.text}"
        )

    # ------------------------------------------------------------------
    # Bad component structure
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        ("component_key", "bad_value", "idx"),
        [
            (
                "prompt",
                {"component": "CustomRAGGenerationPrompt"},
                0,
            ),  # missing 'params'
            ("prompt", {"params": {"language": "en"}}, 1),  # missing 'component'
            ("prompt", "bad_string", 2),  # wrong type
            (
                "chunking_model",
                {"component": "CharacterChunkModel"},
                0,
            ),  # missing 'params'
            ("chunking_model", [], 1),  # wrong type
            ("generation_model", None, 0),  # null
        ],
    )
    def test_update_rag_session_bad_component_structure(
        self,
        client: TestClient,
        test_doc_id: int,
        component_key: str,
        bad_value,
        idx: int,
    ):
        """Malformed component values → 400."""
        session = self._create_session(
            client, test_doc_id, f"test_update_bad_struct_{component_key}_{idx}"
        )
        session_id = session["id"]

        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={component_key: bad_value},
        )
        assert resp.status_code == 400, (
            f"Bad '{component_key}' structure should yield 400, "
            f"got {resp.status_code}: {resp.text}"
        )

    # ------------------------------------------------------------------
    # Document-related edge-cases
    # ------------------------------------------------------------------

    def test_update_rag_session_invalid_documents(
        self, client: TestClient, test_doc_id: int
    ):
        """Updating ``documents`` to non-existent IDs now returns 400."""
        session = self._create_session(client, test_doc_id, "test_update_invalid_docs")
        session_id = session["id"]

        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"documents": [99999]},
        )
        assert resp.status_code == 400, (
            f"Non-existent doc ID should return 400, "
            f"got {resp.status_code}: {resp.text}"
        )

    def test_update_rag_session_documents_empty(
        self, client: TestClient, test_doc_id: int
    ):
        """Updating documents to an empty list → 400 (empty not allowed)."""
        session = self._create_session(client, test_doc_id, "test_update_docs_empty")
        session_id = session["id"]

        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"documents": []},
        )
        assert resp.status_code == 400, (
            f"Empty documents should return 400, got {resp.status_code}: {resp.text}"
        )

    # ------------------------------------------------------------------
    # prompt_id edge cases
    # ------------------------------------------------------------------

    def test_update_rag_session_invalid_prompt_id(
        self, client: TestClient, test_doc_id: int
    ):
        """``prompt_id: 999`` (non-existent) now returns 400."""
        session = self._create_session(client, test_doc_id, "test_update_bad_prompt_id")
        session_id = session["id"]

        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"prompt_id": 999},
        )
        assert resp.status_code == 400, (
            f"Invalid prompt_id should return 400, got {resp.status_code}: {resp.text}"
        )

    def test_update_rag_session_valid_prompt_id(
        self, client: TestClient, test_doc_id: int
    ):
        """``prompt_id`` pointing to an existing prompt → prompt config resolved.

        The ``PromptService.resolve_prompt_id_to_component`` replaces the
        numeric ID with a ``{component, params}`` dict.
        """
        # Create a custom prompt via the prompt API
        create_payload = {
            "class_name": "CustomRAGGenerationPrompt",
            "name": "For prompt_id test",
            "parameters": {"template": "Context: {chunks}\nUser: {input}\nAnswer:"},
        }
        prompt_resp = client.post("/api/v1/prompt/", json=create_payload)
        assert prompt_resp.status_code == 201, (
            f"Prompt prereq failed: {prompt_resp.text}"
        )
        prompt_id = prompt_resp.json()["id"]

        session = self._create_session(
            client, test_doc_id, "test_update_valid_prompt_id"
        )
        session_id = session["id"]

        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"prompt_id": prompt_id},
        )
        assert resp.status_code == 200, (
            f"Valid prompt_id should resolve, got {resp.status_code}: {resp.text}"
        )
        prompt = resp.json()["parameters"]["prompt"]
        assert "component" in prompt
        assert prompt["component"] == "CustomRAGGenerationPrompt"

    # ------------------------------------------------------------------
    # Unknown keys
    # ------------------------------------------------------------------

    def test_update_rag_session_unknown_key(self, client: TestClient, test_doc_id: int):
        """Unknown key in PUT body is merged into parameters.

        Pydantic ``model_validate`` with default ``extra='ignore'`` tolerates
        extra keys, so the unknown key is persisted in the session.
        """
        session = self._create_session(client, test_doc_id, "test_update_unknown_key")
        session_id = session["id"]

        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"unknown_key": "some_value"},
        )
        assert resp.status_code == 200, (
            f"Unknown key should be tolerated, got {resp.status_code}: {resp.text}"
        )
        # The unknown key is stored in parameters
        assert "unknown_key" in resp.json()["parameters"]

    # ------------------------------------------------------------------
    # Non-existent session
    # ------------------------------------------------------------------

    def test_update_rag_session_nonexistent_session(self, client: TestClient):
        """PUT on a session that does not exist → 404."""
        resp = client.put(
            "/api/v1/generative-session/99999/parameters",
            json={
                "generation_model": {
                    "component": "Llama32_1BInstruct",
                    "params": {},
                }
            },
        )
        assert resp.status_code == 404, (
            f"Expected 404, got {resp.status_code}: {resp.text}"
        )

    # ------------------------------------------------------------------
    # Missing required keys after merge
    # ------------------------------------------------------------------

    def test_update_rag_session_remove_required_key(
        self, client: TestClient, test_doc_id: int
    ):
        """Overwriting a required key with something that fails structure
        validation → 400."""
        session = self._create_session(client, test_doc_id, "test_remove_required_key")
        session_id = session["id"]

        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"prompt": {}},  # empty dict — no 'component' or 'params'
        )
        assert resp.status_code == 400, (
            f"Empty prompt dict should fail validation, "
            f"got {resp.status_code}: {resp.text}"
        )


# ===================================================================
# Prompt template validation  (POST /api/v1/prompt/)
# ===================================================================


class TestPromptValidation:
    """Prompt creation validates class-name existence AND template placeholders."""

    def test_prompt_validate_template_missing_placeholders(self, client: TestClient):
        """Template lacking required placeholders ``{input}`` and ``{chunks}``
        → 400."""
        payload = {
            "class_name": "CustomRAGGenerationPrompt",
            "name": "test_template_missing_placeholders",
            "parameters": {"template": "This template has absolutely no placeholders."},
        }
        resp = client.post("/api/v1/prompt/", json=payload)
        assert resp.status_code == 400, (
            f"Expected 400 for missing required placeholders, "
            f"got {resp.status_code}: {resp.text}"
        )
        assert "placeholder" in resp.text.lower() or "template" in resp.text.lower()

    @pytest.mark.parametrize(
        ("class_name", "params", "expected_status"),
        [
            # valid: all placeholders present
            (
                "CustomRAGGenerationPrompt",
                {"template": "Context: {chunks}\nQuestion: {input}"},
                201,
            ),
            # valid: default prompt class with language and templates
            (
                "DefaultRAGGenerationPrompt",
                {"language": "en", "templates": {"en": "Q: {input}\nC: {chunks}"}},
                201,
            ),
            # valid: QA prompt with language and templates
            (
                "DefaultQARAGGenerationPrompt",
                {"language": "en", "templates": {"en": "QA: {input}\nC: {chunks}"}},
                201,
            ),
            # invalid: registered class but missing required placeholders
            (
                "CustomRAGGenerationPrompt",
                {"template": "No placeholders here"},
                400,
            ),
            # invalid: CustomRAGGenerationPrompt with only {input} but missing {chunks}
            (
                "CustomRAGGenerationPrompt",
                {"template": "Only {input} present"},
                400,
            ),
            # invalid: CustomRAGGenerationPrompt with only {chunks} but missing {input}
            (
                "CustomRAGGenerationPrompt",
                {"template": "Only {chunks} present"},
                400,
            ),
        ],
    )
    def test_prompt_validate_template_parametrized(
        self,
        client: TestClient,
        class_name: str,
        params: dict,
        expected_status: int,
    ):
        """Parametrized happy / sad paths for prompt template validation."""
        payload = {
            "class_name": class_name,
            "name": f"test_prompt_{class_name}_{expected_status}",
            "parameters": params,
        }
        resp = client.post("/api/v1/prompt/", json=payload)
        assert resp.status_code == expected_status, (
            f"Expected {expected_status} for class_name={class_name} "
            f"params={params}, got {resp.status_code}: {resp.text}"
        )

    def test_prompt_validate_invalid_class_name(self, client: TestClient):
        """Non-existent class_name → 400."""
        payload = {
            "class_name": "NonExistentPromptClass",
            "name": "test_invalid_class_name",
            "parameters": {"template": "Context: {chunks}\nQuestion: {input}"},
        }
        resp = client.post("/api/v1/prompt/", json=payload)
        assert resp.status_code == 400, (
            f"Expected 400 for invalid class_name, got {resp.status_code}: {resp.text}"
        )
        assert "not registered" in resp.text.lower()

    def test_prompt_validate_class_not_a_prompt(self, client: TestClient):
        """A registered class that is NOT a ``Prompt`` subclass → 400.

        ``CharacterChunkModel`` exists in the registry but is not a Prompt.
        """
        payload = {
            "class_name": "CharacterChunkModel",
            "name": "test_class_not_prompt",
            "parameters": {"template": "Context: {chunks}\nQuestion: {input}"},
        }
        resp = client.post("/api/v1/prompt/", json=payload)
        assert resp.status_code == 400, (
            f"Expected 400 for non-Prompt class, got {resp.status_code}: {resp.text}"
        )
        assert "prompt" in resp.text.lower()

    def test_prompt_validate_missing_required_fields(self, client: TestClient):
        """Missing ``class_name`` or ``name`` → 422 (Pydantic validation)."""
        # Missing class_name
        resp1 = client.post(
            "/api/v1/prompt/",
            json={
                "name": "no_class_name",
                "parameters": {"template": "Q: {input}\nC: {chunks}"},
            },
        )
        assert resp1.status_code == 422, (
            f"Expected 422 for missing class_name, got {resp1.status_code}"
        )

        # Missing name
        resp2 = client.post(
            "/api/v1/prompt/",
            json={
                "class_name": "CustomRAGGenerationPrompt",
                "parameters": {"template": "Q: {input}\nC: {chunks}"},
            },
        )
        assert resp2.status_code == 422, (
            f"Expected 422 for missing name, got {resp2.status_code}"
        )

    def test_prompt_validate_parameters_missing_template_key(self, client: TestClient):
        """Providing ``parameters`` dict without ``template`` or ``templates``
        → 400."""
        payload = {
            "class_name": "CustomRAGGenerationPrompt",
            "name": "test_no_template_key",
            "parameters": {"language": "en"},  # no 'template' or 'templates'
        }
        resp = client.post("/api/v1/prompt/", json=payload)
        assert resp.status_code == 400, (
            f"Expected 400 for missing template/templates key, "
            f"got {resp.status_code}: {resp.text}"
        )


# ===================================================================
# Regression: Retriever configuration bugs
# ===================================================================


class TestRetrieverConfigRegression:
    """Verify fixes for retriever configuration bugs."""

    # ------------------------------------------------------------------
    # Bug 3: DenseEmbeddingRetriever preserves its component name
    # ------------------------------------------------------------------

    def test_dense_embedding_retriever_preserves_component_name(
        self, client: TestClient, test_doc_id: int
    ):
        """Regression: creating a session with DenseEmbeddingRetriever
        must store ``component: "DenseEmbeddingRetriever"`` — NOT the
        embedding model name."""
        params = _base_session_params(test_doc_id)
        params["name"] = "test_dense_component_preserved"

        # Replace retriever with DenseEmbeddingRetriever + SentenceTransformer
        params["parameters"]["retriever_model"] = {
            "component": "DenseEmbeddingRetriever",
            "params": {
                "embedding_model": {
                    "component": "SentenceTransformerEmbedding",
                    "params": {
                        "model_name": (
                            "sentence-transformers/"
                            "paraphrase-multilingual-MiniLM-L12-v2"
                        ),
                        "overflow_strategy": "truncate",
                        "normalize": True,
                        "device": "cpu",
                    },
                },
                "similarity_metric": "cosine",
                "top_k": 10,
            },
        }

        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 201, (
            f"Expected 201, got {resp.status_code}: {resp.text}"
        )

        data = resp.json()
        stored = data["parameters"]["retriever_model"]
        assert stored["component"] == "DenseEmbeddingRetriever", (
            f"Component must be 'DenseEmbeddingRetriever', "
            f"got '{stored['component']}'. "
            f"The embedding model name must not leak to the top level."
        )

    # ------------------------------------------------------------------
    # Bug 2: Empty-component children rejected
    # ------------------------------------------------------------------

    def test_composite_retriever_rejects_empty_child_component(
        self, client: TestClient, test_doc_id: int
    ):
        """Regression: a composite retriever with an empty-component child
        must be rejected with a clear validation error."""
        params = _base_session_params(test_doc_id)
        params["name"] = "test_composite_empty_child"

        # Build a ParallelRetriever with one valid child (BM25) and one
        # child whose component name is an empty string.
        params["parameters"]["retriever_model"] = {
            "component": "ParallelRetriever",
            "params": {
                "merge_strategy": "round_robin",
                "children": [
                    {
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
                    {
                        "component": "",  # ← empty — this is the bug
                        "params": {},
                    },
                ],
            },
        }

        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 400, (
            f"Empty child component should be rejected with 400, "
            f"got {resp.status_code}: {resp.text}"
        )

        detail = resp.json()["detail"]
        assert "not registered" in detail.lower(), (
            f"Error must mention unregistered component, got: {detail}"
        )

    # ------------------------------------------------------------------
    # Bug 2B: Bare embedding model as composite child rejected
    # ------------------------------------------------------------------

    def test_bare_embedding_as_child_accepts_but_fails_at_runtime(
        self, client: TestClient, test_doc_id: int
    ):
        """Regression: a SentenceTransformerEmbedding used directly as a
        child of a composite retriever IS accepted during session creation
        (the component exists in the registry), but the runtime RAG job
        will fail with ``Unsupported retriever type``.

        The frontend fix prevents this scenario by filtering embedding
        models out of the composite child selector in RetrieverNodeConfig.
        """
        params = _base_session_params(test_doc_id)
        params["name"] = "test_bare_embedding_as_child"

        params["parameters"]["retriever_model"] = {
            "component": "ParallelRetriever",
            "params": {
                "merge_strategy": "round_robin",
                "children": [
                    {
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
                    {
                        # Bare embedding model — registered in the component
                        # registry, so session creation passes.  The runtime
                        # would fail with "Unsupported retriever type".
                        # The frontend prevents this by not offering bare
                        # embeddings as child options.
                        "component": "SentenceTransformerEmbedding",
                        "params": {
                            "model_name": (
                                "sentence-transformers/"
                                "paraphrase-multilingual-MiniLM-L12-v2"
                            ),
                            "overflow_strategy": "truncate",
                            "normalize": True,
                            "device": "cpu",
                        },
                    },
                ],
            },
        }

        resp = client.post("/api/v1/generative-session/", json=params)
        # Session creation succeeds because the component is registered;
        # the frontend fix prevents this scenario from occurring in the UI.
        assert resp.status_code == 201, (
            f"Expected 201 (component exists in registry), "
            f"got {resp.status_code}: {resp.text}"
        )

    # ------------------------------------------------------------------
    # Auto-save partial-data regression
    # ------------------------------------------------------------------

    def test_auto_save_partial_data_rejected(
        self, client: TestClient, test_doc_id: int
    ):
        """When auto-save fires with only ``embedding_model`` (simulating
        the frontend bug where store formValues is empty), the missing
        ``similarity_metric``/``top_k`` fields cause validation to fail."""
        params = _base_session_params(test_doc_id)
        params["name"] = "test_autosave_partial"
        params["parameters"]["retriever_model"] = {
            "component": "DenseEmbeddingRetriever",
            "params": {
                "embedding_model": {
                    "component": "SentenceTransformerEmbedding",
                    "params": {
                        "model_name": (
                            "sentence-transformers/"
                            "paraphrase-multilingual-MiniLM-L12-v2"
                        ),
                        "overflow_strategy": "truncate",
                        "normalize": True,
                        "device": "cpu",
                    },
                },
                # NOTE: similarity_metric and top_k missing (auto-save bug)
            },
        }
        resp = client.post("/api/v1/generative-session/", json=params)
        # Incomplete params must be rejected
        assert resp.status_code == 400, (
            f"Expected 400 for incomplete params, got {resp.status_code}: {resp.text}"
        )


# ===================================================================
# Module-level helpers
# ===================================================================


def _dummy_params_for(component_key: str) -> dict:
    """Return minimal valid ``params`` for each component type.

    Used when testing invalid component names — the structure must still
    be a valid ``{"component": str, "params": dict}``.
    """
    dummy_map = {
        "prompt": {"language": "en"},
        "chunking_model": {"chunk_size": 128, "chunk_overlap": 12},
        "retriever_model": {"top_k": 3},
        "generation_model": {
            "max_tokens": 64,
            "temperature": 0.5,
            "frequency_penalty": 0.0,
            "context_window": 256,
            "device": "CPU",
        },
    }
    return dummy_map.get(component_key, {})
