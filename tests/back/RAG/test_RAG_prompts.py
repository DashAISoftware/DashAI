"""Integration tests for prompt CRUD API and prompt usage in generative sessions.

Covers:
- Prompt CRUD operations (list, create, update)
- Prompt validation (duplicates, missing fields, invalid class names)
- Prompt usage within generative RAG sessions (default/templates, language, custom)
- Prompt cloning to sessions
"""

from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import RAGPrompt
from DashAI.back.services.RAG.prompt_service import PromptService

# ---------------------------------------------------------------------------
# helpers — matching test_rag_component_api_configs.py patterns
# ---------------------------------------------------------------------------


def _base_session_params() -> dict:
    """Return the minimal default RAG session payload."""
    return {
        "model_name": "RAGPipeline",
        "task_name": "RAGTask",
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
        "name": "Prompt Test",
        "description": None,
    }


def _post_and_get(client: TestClient, params: dict):
    """POST a session, assert 201 + metadata, then GET and return stored JSON."""
    response = client.post("/api/v1/generative-session/", json=params)
    assert response.status_code == 201, f"Session creation failed: {response.text}"
    data = response.json()
    assert data["id"] is not None
    assert data["model_name"] == "RAGPipeline"
    assert data["task_name"] == "RAGTask"
    assert data["name"] == params["name"]
    session_id = data["id"]
    get_resp = client.get(f"/api/v1/generative-session/{session_id}")
    assert get_resp.status_code == 200
    return get_resp.json()


# ===================================================================
# Prompt CRUD Operations
# ===================================================================


class TestPromptCRUD:
    """Prompt CRUD operations via the prompt API."""

    def test_list_prompts_returns_defaults(self, client: TestClient):
        """GET /api/v1/prompt/ returns the lazily-seeded default prompts."""
        response = client.get("/api/v1/prompt/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2, "Expected at least 2 default prompts in the list"

        class_names = [p["class_name"] for p in data]
        assert "DefaultRAGGenerationPrompt" in class_names, (
            "DefaultRAGGenerationPrompt not found in prompt list"
        )
        assert "DefaultQARAGGenerationPrompt" in class_names, (
            "DefaultQARAGGenerationPrompt not found in prompt list"
        )

    def test_create_custom_prompt(self, client: TestClient):
        """POST /api/v1/prompt/ creates a new CustomRAGGenerationPrompt
        and it appears in the list."""
        template = "Answer using: {chunks}\n\nQuestion: {input}"
        payload = {
            "class_name": "CustomRAGGenerationPrompt",
            "name": "Test Custom Prompt",
            "parameters": {"template": template},
        }
        response = client.post("/api/v1/prompt/", json=payload)
        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code}: {response.text}"
        )
        data = response.json()
        assert data["id"] is not None, "Created prompt should have an id"

        list_resp = client.get("/api/v1/prompt/")
        assert list_resp.status_code == 200
        prompts = list_resp.json()
        custom = [p for p in prompts if p["name"] == "Test Custom Prompt"]
        assert len(custom) == 1, "Custom prompt not found in list"
        assert custom[0]["class_name"] == "CustomRAGGenerationPrompt"
        assert custom[0]["parameters"]["template"] == template

    def test_create_duplicate_prompt_fails(self, client: TestClient):
        """Creating the same prompt twice
        (same class_name + parameters) is rejected with 409 Conflict."""
        template = "Q: {input}\nContext: {chunks}"
        payload = {
            "class_name": "CustomRAGGenerationPrompt",
            "name": "Dup Prompt 1",
            "parameters": {"template": template},
        }

        resp1 = client.post("/api/v1/prompt/", json=payload)
        assert resp1.status_code == 201, f"First creation should succeed: {resp1.text}"

        # Second creation with same class_name + parameters but different name.
        # The service catches the IntegrityError and returns 409.
        payload2 = {
            "class_name": "CustomRAGGenerationPrompt",
            "name": "Dup Prompt 2",
            "parameters": {"template": template},
        }
        resp2 = client.post("/api/v1/prompt/", json=payload2)
        assert resp2.status_code == 409, (
            f"Duplicate prompt should be rejected: {resp2.text}"
        )

    def test_create_prompt_missing_required_field(self, client: TestClient):
        """POST without class_name or without name returns 422."""
        # Without class_name
        resp1 = client.post(
            "/api/v1/prompt/",
            json={"name": "Missing Class", "parameters": {"template": "Q: {input}"}},
        )
        assert resp1.status_code == 422, (
            f"Expected 422 for missing class_name, got {resp1.status_code}"
        )

        # Without name
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

    def test_create_prompt_invalid_class_name(self, client: TestClient):
        """POST with a non-existent class_name returns 400."""
        payload = {
            "class_name": "NonExistentPrompt",
            "name": "Bad Prompt",
            "parameters": {"template": "Q: {input} - {chunks}"},
        }
        response = client.post("/api/v1/prompt/", json=payload)
        assert response.status_code == 400, (
            f"Expected 400 for invalid class_name, got"
            f" {response.status_code}: {response.text}"
        )

    def test_service_get_or_create_reuses_existing(self, client: TestClient):
        """get_or_create reuses an existing prompt with the same class+params."""
        session_factory = client.app.container["session_factory"]
        registry = client.app.container["component_registry"]
        with session_factory() as db:
            service = PromptService(db, registry)
            params = {"language": "en"}
            first = service.get_or_create(
                "DefaultRAGGenerationPrompt", "pipeline_1_X", params
            )
            second = service.get_or_create(
                "DefaultRAGGenerationPrompt", "pipeline_2_X", params
            )
            assert second.id == first.id
            assert first.class_name == "DefaultRAGGenerationPrompt"

            # Different parameters produce a distinct record.
            third = service.get_or_create(
                "DefaultRAGGenerationPrompt", "pipeline_3_X", {"language": "es"}
            )
            assert third.id != first.id

            rows = (
                db.query(RAGPrompt)
                .filter(
                    RAGPrompt.class_name == "DefaultRAGGenerationPrompt",
                    RAGPrompt.name.in_(
                        ["pipeline_1_X", "pipeline_2_X", "pipeline_3_X"]
                    ),
                )
                .all()
            )
            assert len(rows) == 2


# ===================================================================
# Prompt Session Integration
# ===================================================================


class TestPromptSessionIntegration:
    """Prompt usage within generative RAG sessions."""

    def test_session_with_default_prompt_en(self, client: TestClient):
        """Session creation with DefaultRAGGenerationPrompt
        (language=en) stores prompt correctly."""
        params = _base_session_params()
        params["name"] = "Session EN Prompt"
        stored = _post_and_get(client, params)
        prompt = stored["parameters"]["prompt"]
        assert prompt["component"] == "DefaultRAGGenerationPrompt", (
            "Prompt component mismatch"
        )
        assert prompt["params"]["language"] == "en", "Language should be en"

    def test_session_with_default_prompt_es(self, client: TestClient):
        """Session creation with DefaultRAGGenerationPrompt
        (language=es) stores prompt correctly."""
        params = _base_session_params()
        params["name"] = "Session ES Prompt"
        params["parameters"]["prompt"] = {
            "component": "DefaultRAGGenerationPrompt",
            "params": {"language": "es"},
        }
        stored = _post_and_get(client, params)
        prompt = stored["parameters"]["prompt"]
        assert prompt["component"] == "DefaultRAGGenerationPrompt"
        assert prompt["params"]["language"] == "es", "Language should be es"

    def test_session_with_qna_prompt(self, client: TestClient):
        """Session creation with DefaultQARAGGenerationPrompt
        (language=en) stores prompt correctly."""
        params = _base_session_params()
        params["name"] = "Session QnA Prompt"
        params["parameters"]["prompt"] = {
            "component": "DefaultQARAGGenerationPrompt",
            "params": {"language": "en"},
        }
        stored = _post_and_get(client, params)
        prompt = stored["parameters"]["prompt"]
        assert prompt["component"] == "DefaultQARAGGenerationPrompt", (
            "Prompt component should be DefaultQARAGGenerationPrompt"
        )
        assert prompt["params"]["language"] == "en"

    def test_session_with_custom_prompt_template(self, client: TestClient):
        """Session creation with CustomRAGGenerationPrompt
        stores the custom template correctly."""
        template_text = "Answer the question based on: {chunks}\n\nQuestion: {input}"
        params = _base_session_params()
        params["name"] = "Session Custom Prompt"
        params["parameters"]["prompt"] = {
            "component": "CustomRAGGenerationPrompt",
            "params": {"template": template_text},
        }
        stored = _post_and_get(client, params)
        prompt = stored["parameters"]["prompt"]
        assert prompt["component"] == "CustomRAGGenerationPrompt"
        assert prompt["params"]["template"] == template_text, (
            "Custom template should be stored exactly as provided"
        )

    def test_session_rejects_invalid_prompt_class(self, client: TestClient):
        """Session creation rejects unknown prompt component names with 400."""
        params = _base_session_params()
        params["name"] = "Session Invalid Prompt"
        params["parameters"]["prompt"] = {
            "component": "NonExistentPrompt",
            "params": {"language": "en"},
        }
        response = client.post("/api/v1/generative-session/", json=params)
        assert response.status_code == 400, (
            f"Unknown component should be rejected, got {response.status_code}"
        )
