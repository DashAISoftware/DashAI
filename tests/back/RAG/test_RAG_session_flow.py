"""Integration tests for RAG session parameter state transitions, prompt_id lifecycle,
and workflow edge cases.

Tests verify the OBSERVABLE BEHAVIOR of the API as a state machine — not internal
implementation details.  The API endpoints tested are:

  POST   /api/v1/generative-session/              → create session (201)
  GET    /api/v1/generative-session/{id}           → read session (200)
  PUT    /api/v1/generative-session/{id}/parameters → update params (200)
  DELETE /api/v1/generative-session/{id}           → delete session (204)
  GET    /api/v1/generative-session/{id}/parameters-history → history (200)
  POST   /api/v1/prompt/                           → create prompt (201)

Coverage
--------
- Parameter state transitions (PUT merge, rollback, accumulation)
- Prompt ID resolution and replacement across session lifecycle
- Session lifecycle (create → delete → not-found)
- Cross-component parameter validation (type, range, cross-field)
- Parameter change history tracking
"""

import pytest
from fastapi.testclient import TestClient

from tests.back.RAG.conftest import _create_test_document

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def test_doc_id(client: TestClient) -> int:
    """Module-scoped test document ID shared across all flow tests."""
    return _create_test_document(client, suffix="_rag_session_flow")


def _base_session_params(test_doc_id: int) -> dict:
    """Return the minimal valid RAG session payload."""
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
        "name": "Flow Test",
        "description": None,
    }


def _create_session(client: TestClient, test_doc_id: int, name: str) -> dict:
    """Create a minimal valid RAG session and return its JSON response."""
    params = _base_session_params(test_doc_id)
    params["name"] = name
    resp = client.post("/api/v1/generative-session/", json=params)
    assert resp.status_code == 201, f"Session prereq failed: {resp.text}"
    return resp.json()


def _create_prompt(client: TestClient, template: str, name: str) -> int:
    """Create a CustomRAGGenerationPrompt and return its ID."""
    payload = {
        "class_name": "CustomRAGGenerationPrompt",
        "name": name,
        "parameters": {"template": template},
    }
    resp = client.post("/api/v1/prompt/", json=payload)
    assert resp.status_code == 201, f"Prompt creation failed: {resp.text}"
    return resp.json()["id"]


# ===================================================================
# Parameter State Transitions
# ===================================================================


class TestParameterStateTransitions:
    """PUT /.../parameters modifies stored state — verify merge semantics,
    rollback on error, and that the API surface is consistent."""

    def test_update_preserves_unmentioned_params(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """PUT with only ``generation_model`` → all other parameters
        preserved; only ``generation_model`` reflects the new values."""
        session = _create_session(client, test_doc_id, "flow_preserve_unmentioned")
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
        assert resp.status_code == 200, resp.text
        params = resp.json()["parameters"]

        # generation_model changed
        assert params["generation_model"]["params"]["temperature"] == 0.9
        assert params["generation_model"]["params"]["max_tokens"] == 200

        # All other top-level params preserved
        assert params["prompt"]["component"] == "DefaultRAGGenerationPrompt"
        assert params["chunking_model"]["component"] == "CharacterChunkModel"
        assert params["chunking_model"]["params"]["chunk_size"] == 400
        assert params["retriever_model"]["component"] == "BM25Retriever"
        assert params["documents"] == [test_doc_id]

        # Verify persistence via GET (the response from PUT is the same shape)
        get_resp = client.get(f"/api/v1/generative-session/{session_id}")
        assert get_resp.status_code == 200
        get_params = get_resp.json()["parameters"]
        assert get_params["generation_model"]["params"]["temperature"] == 0.9
        assert get_params["prompt"]["component"] == "DefaultRAGGenerationPrompt"

    def test_update_clears_old_retriever_when_changed(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """PUT to replace the retriever from BM25 → TFIDF results in
        the observable state showing the new retriever."""
        session = _create_session(client, test_doc_id, "flow_retriever_change")
        session_id = session["id"]

        new_retriever = {
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
            },
        }
        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"retriever_model": new_retriever},
        )
        assert resp.status_code == 200, resp.text
        retriever = resp.json()["parameters"]["retriever_model"]
        assert retriever["component"] == "TFIDFRetriever"
        assert retriever["params"]["top_k"] == 10

    def test_update_rollback_on_error(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """PUT with a structurally invalid component dict returns 400 and
        the session's stored parameters remain unchanged (no partial update).

        .. note::

           The strict recursive validation contract requires every
           ``{component, params}`` dict to carry both keys — sub-component
           field values (e.g. ``temperature`` type) are validated against
           their own schema during PUT as well.
        """
        session = _create_session(client, test_doc_id, "flow_rollback")
        session_id = session["id"]
        original_gen = dict(session["parameters"]["generation_model"])

        # Missing ``params`` key — structure validation requires both
        # ``component`` and ``params`` → 400.
        bad_gen = {
            "component": "Llama32_1BInstruct",
            # missing "params"
        }
        resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"generation_model": bad_gen},
        )
        assert resp.status_code == 400, (
            f"Missing 'params' key should yield 400, "
            f"got {resp.status_code}: {resp.text}"
        )

        # GET session → original parameters unchanged
        get_resp = client.get(f"/api/v1/generative-session/{session_id}")
        assert get_resp.status_code == 200
        stored_gen = get_resp.json()["parameters"]["generation_model"]
        assert stored_gen == original_gen, (
            "Generation model must be unchanged after a failed PUT"
        )

    def test_update_invalid_then_valid(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """A failed PUT (400) does not corrupt the session — a subsequent
        valid PUT succeeds with the correct final state."""
        session = _create_session(client, test_doc_id, "flow_invalid_then_valid")
        session_id = session["id"]

        # ---- invalid PUT: malformed component structure ----
        # Sending ``{"component": "CustomRAGGenerationPrompt"}`` without
        # the required ``params`` key fails structure validation → 400.
        bad_payload = {
            "component": "CustomRAGGenerationPrompt",
        }
        resp_bad = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"prompt": bad_payload},
        )
        assert resp_bad.status_code == 400, (
            f"Expected 400 for malformed component, "
            f"got {resp_bad.status_code}: {resp_bad.text}"
        )

        # ---- valid PUT: change generation_model ----
        new_gen = {
            "component": "Llama32_1BInstruct",
            "params": {
                "max_tokens": 150,
                "temperature": 0.5,
                "frequency_penalty": 0.0,
                "context_window": 1024,
                "device": "CPU",
            },
        }
        resp_good = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"generation_model": new_gen},
        )
        assert resp_good.status_code == 200, resp_good.text
        gen = resp_good.json()["parameters"]["generation_model"]
        assert gen["params"]["max_tokens"] == 150
        assert gen["params"]["temperature"] == 0.5

        # Other original params still intact
        prompt = resp_good.json()["parameters"]["prompt"]
        assert prompt["component"] == "DefaultRAGGenerationPrompt"


# ===================================================================
# Prompt ID Lifecycle
# ===================================================================


class TestPromptIDLifecycle:
    """``prompt_id`` resolution and replacement across the session lifecycle.

    .. note::

       The POST endpoint does **not** resolve ``prompt_id`` — it stores the
       raw ID as-is in the parameters dict.  Resolution happens only during
       PUT via :meth:`PromptService.resolve_prompt_id_to_component`, which
       converts the numeric ID into a ``{component, params}`` dict and
       removes the ``prompt_id`` key.
    """

    def test_prompt_id_replaced_by_prompt_in_params(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """When both ``prompt`` and ``prompt_id`` are stored in session
        parameters (e.g. after prompt cloning), a PUT with an empty body
        triggers resolution: ``prompt_id`` is converted to a ``prompt``
        config and the raw ID key is removed."""
        # ---- create a custom prompt ----
        template = "Context: {chunks}\nUser: {input}\nAnswer:"
        prompt_id = _create_prompt(client, template, "flow_resolve_initial")

        # ---- create a session that includes BOTH prompt and prompt_id ----
        params = _base_session_params(test_doc_id)
        params["name"] = "flow_prompt_id_resolve"
        params["parameters"]["prompt_id"] = prompt_id
        # prompt key is already present from _base_session_params

        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 201, resp.text
        session_id = resp.json()["id"]

        # ---- GET before PUT: prompt_id resolved on CREATE ----
        get_resp = client.get(f"/api/v1/generative-session/{session_id}")
        assert get_resp.status_code == 200
        stored = get_resp.json()["parameters"]
        # CREATE resolves prompt_id → prompt, so prompt_id is removed
        assert "prompt_id" not in stored, "CREATE should resolve prompt_id to prompt"
        assert stored["prompt"]["component"] == "CustomRAGGenerationPrompt"

        # ---- PUT with prompt_id triggers resolution ----
        put_resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"prompt_id": prompt_id},
        )
        assert put_resp.status_code == 200, put_resp.text
        updated = put_resp.json()["parameters"]

        # prompt_id resolved → replaced by prompt config
        assert "prompt_id" not in updated, "PUT must remove prompt_id after resolution"
        assert updated["prompt"]["component"] == "CustomRAGGenerationPrompt"
        assert updated["prompt"]["params"]["template"] == template

        # Verify persistence via GET
        get_resp2 = client.get(f"/api/v1/generative-session/{session_id}")
        assert get_resp2.status_code == 200
        stored2 = get_resp2.json()["parameters"]
        assert "prompt_id" not in stored2
        assert stored2["prompt"]["params"]["template"] == template

    def test_update_prompt_id_resolves(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """PUT with a new ``prompt_id`` switches the session to a different
        prompt.  The stored ``prompt`` config reflects the new prompt's
        component and params."""
        # ---- create two prompts ----
        template_a = "A: {chunks}\nQ: {input}"
        prompt_a_id = _create_prompt(client, template_a, "flow_prompt_switch_a")

        template_b = "System: {chunks}\nUser: {input}\nAnswer:"
        prompt_b_id = _create_prompt(client, template_b, "flow_prompt_switch_b")

        # ---- session with both default prompt AND prompt_a_id ----
        params = _base_session_params(test_doc_id)
        params["name"] = "flow_prompt_id_switch"
        params["parameters"]["prompt_id"] = prompt_a_id

        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 201, resp.text
        session_id = resp.json()["id"]

        # ---- PUT with new prompt_id → resolve to prompt_b ----
        put_resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"prompt_id": prompt_b_id},
        )
        assert put_resp.status_code == 200, put_resp.text
        updated = put_resp.json()["parameters"]

        assert "prompt_id" not in updated, "prompt_id must be resolved and removed"
        assert updated["prompt"]["component"] == "CustomRAGGenerationPrompt"
        assert updated["prompt"]["params"]["template"] == template_b

        # Verify persistence via GET
        get_resp = client.get(f"/api/v1/generative-session/{session_id}")
        assert get_resp.status_code == 200
        stored = get_resp.json()["parameters"]
        assert stored["prompt"]["params"]["template"] == template_b


# ===================================================================
# Session Lifecycle
# ===================================================================


class TestSessionLifecycle:
    """Create → read → delete → not-found lifecycle."""

    def test_create_then_delete_rag_session(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """A valid RAG session can be created (201), then deleted (204).
        Subsequent GET returns 404."""
        params = _base_session_params(test_doc_id)
        params["name"] = "flow_create_delete"
        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 201, resp.text
        session_id = resp.json()["id"]

        # DELETE → 204
        del_resp = client.delete(f"/api/v1/generative-session/{session_id}")
        assert del_resp.status_code == 204, (
            f"Expected 204, got {del_resp.status_code}: {del_resp.text}"
        )

        # GET after delete → 404
        get_resp = client.get(f"/api/v1/generative-session/{session_id}")
        assert get_resp.status_code == 404, (
            f"Expected 404 after delete, got {get_resp.status_code}"
        )

    def test_delete_nonexistent_session_bug(
        self,
        client: TestClient,
    ):
        """DELETE on a session ID that never existed returns 404 (bug fixed)."""
        resp = client.delete("/api/v1/generative-session/99999")
        # Bug fixed: now returns 404
        assert resp.status_code == 404, (
            f"Expected 404, got {resp.status_code}: {resp.text}"
        )

    def test_multiple_updates_accumulate(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """Sequential PUTs for different parameters (A → B → C) all
        accumulate in the final session state."""
        session = _create_session(client, test_doc_id, "flow_multiple_updates")
        session_id = session["id"]

        # ---- PUT A: change generation_model ----
        gen_a = {
            "component": "Llama32_1BInstruct",
            "params": {
                "max_tokens": 50,
                "temperature": 0.3,
                "frequency_penalty": 0.0,
                "context_window": 512,
                "device": "CPU",
            },
        }
        resp_a = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"generation_model": gen_a},
        )
        assert resp_a.status_code == 200, resp_a.text

        # ---- PUT B: change chunking_model ----
        chunk_b = {
            "component": "RecursiveCharacterChunkModel",
            "params": {
                "chunk_size": 500,
                "chunk_overlap": 50,
                "separators": ["\n\n", "\n", ".", " ", ""],
            },
        }
        resp_b = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"chunking_model": chunk_b},
        )
        assert resp_b.status_code == 200, resp_b.text

        # ---- PUT C: change prompt ----
        prompt_c = {
            "component": "DefaultQARAGGenerationPrompt",
            "params": {"language": "en"},
        }
        resp_c = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"prompt": prompt_c},
        )
        assert resp_c.status_code == 200, resp_c.text

        # ---- verify final state via GET ----
        get_resp = client.get(f"/api/v1/generative-session/{session_id}")
        assert get_resp.status_code == 200
        p = get_resp.json()["parameters"]

        # All three changes present
        assert p["generation_model"]["params"]["max_tokens"] == 50
        assert p["generation_model"]["params"]["temperature"] == 0.3
        assert p["chunking_model"]["component"] == "RecursiveCharacterChunkModel"
        assert p["chunking_model"]["params"]["chunk_size"] == 500
        assert p["prompt"]["component"] == "DefaultQARAGGenerationPrompt"

        # Unchanged params still present
        assert p["retriever_model"]["component"] == "BM25Retriever"
        assert p["documents"] == [test_doc_id]


# ===================================================================
# Cross-Component Validation (Edge Cases)
# ===================================================================


class TestCrossComponentValidation:
    """Parameter validation within nested component schemas.

    .. important::

       Since the strict recursive validation contract, every ``{component,
       params}`` (including nested sub-components such as
       ``BM25VectorizerModel`` inside ``BM25Retriever``) is validated against
       its own schema **at creation time**.  Invalid sub-component field
       types or ranges are therefore **rejected** (400) during session
       creation, instead of being deferred to pipeline runtime.
    """

    # ------------------------------------------------------------------
    # Structure validation  (what RAGPipelineSchema actually checks)
    # ------------------------------------------------------------------

    def test_component_missing_params_key(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """Component dict without ``params`` key fails structure
        validation → 400."""
        params = _base_session_params(test_doc_id)
        params["name"] = "flow_missing_params"
        params["parameters"]["generation_model"] = {
            "component": "Llama32_1BInstruct",
            # missing "params"
        }
        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 400, (
            f"Missing 'params' key should yield 400, "
            f"got {resp.status_code}: {resp.text}"
        )

    def test_component_missing_component_key(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """Component dict without ``component`` key fails structure
        validation → 400."""
        params = _base_session_params(test_doc_id)
        params["name"] = "flow_missing_component"
        params["parameters"]["prompt"] = {
            "params": {"language": "en"},
            # missing "component"
        }
        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 400, (
            f"Missing 'component' key should yield 400, "
            f"got {resp.status_code}: {resp.text}"
        )

    def test_component_wrong_type(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """Component value that is not a dict fails structure
        validation → 400."""
        params = _base_session_params(test_doc_id)
        params["name"] = "flow_wrong_component_type"
        params["parameters"]["chunking_model"] = "not_a_dict"
        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 400, (
            f"Non-dict component should yield 400, got {resp.status_code}: {resp.text}"
        )

    # ------------------------------------------------------------------
    # Sub-component validation is STRICT at creation time
    # ------------------------------------------------------------------

    def test_subcomponent_temperature_string_rejected(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """``temperature: "not-a-number"`` is REJECTED (400) at session
        creation — sub-component field types are validated recursively
        against ``LlamaSchema.temperature`` (``float_field(ge=0.0, le=1.0)``)
        at create/update time, not deferred to pipeline runtime.
        """
        params = _base_session_params(test_doc_id)
        params["name"] = "flow_temp_string_rejected"
        params["parameters"]["generation_model"]["params"]["temperature"] = (
            "not-a-number"
        )

        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 400, (
            f"String temperature should be rejected (strict validation), "
            f"got {resp.status_code}: {resp.text}"
        )

    def test_subcomponent_negative_chunk_size_rejected(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """``chunk_size: -1`` is REJECTED (400) at session creation —
        ``CharacterChunkModelSchema.chunk_size`` uses ``int_field(gt=1)``
        and sub-component validation now propagates into nested schemas.
        """
        params = _base_session_params(test_doc_id)
        params["name"] = "flow_neg_chunk_rejected"
        params["parameters"]["chunking_model"]["params"]["chunk_size"] = -1

        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 400, (
            f"Negative chunk_size should be rejected (strict validation), "
            f"got {resp.status_code}: {resp.text}"
        )

    def test_subcomponent_overlap_equals_size_rejected(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """``chunk_overlap == chunk_size`` is REJECTED (400) at session
        creation — the cross-field validator in
        ``CharacterChunkModelSchema`` now runs at create/update time.
        """
        params = _base_session_params(test_doc_id)
        params["name"] = "flow_overlap_eq_rejected"
        params["parameters"]["chunking_model"]["params"]["chunk_size"] = 100
        params["parameters"]["chunking_model"]["params"]["chunk_overlap"] = 100

        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 400, (
            f"chunk_overlap == chunk_size should be rejected "
            f"(strict validation), got {resp.status_code}: {resp.text}"
        )

    def test_subcomponent_temperature_out_of_range_rejected(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """``temperature=2.5`` is REJECTED (400) at session creation —
        ``LlamaSchema.temperature`` has ``float_field(ge=0.0, le=1.0)`` and
        this constraint is now enforced at create/update time.
        """
        params = _base_session_params(test_doc_id)
        params["name"] = "flow_temp_range_rejected"
        params["parameters"]["generation_model"]["params"]["temperature"] = 2.5

        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 400, (
            f"temperature=2.5 should be rejected (strict validation), "
            f"got {resp.status_code}: {resp.text}"
        )


# ===================================================================
# History Tracking
# ===================================================================


class TestHistoryTracking:
    """Parameter change history via
    ``GET /api/v1/generative-session/{id}/parameters-history``."""

    def test_parameter_update_logs_history(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """A PUT that changes parameters creates a history entry retrievable
        via the parameters-history endpoint."""
        session = _create_session(client, test_doc_id, "flow_history_basic")
        session_id = session["id"]

        # PUT a change
        new_gen = {
            "component": "Llama32_1BInstruct",
            "params": {
                "max_tokens": 75,
                "temperature": 0.5,
                "frequency_penalty": 0.0,
                "context_window": 512,
                "device": "CPU",
            },
        }
        put_resp = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"generation_model": new_gen},
        )
        assert put_resp.status_code == 200, put_resp.text

        # Check history
        hist_resp = client.get(
            f"/api/v1/generative-session/{session_id}/parameters-history"
        )
        assert hist_resp.status_code == 200
        history = hist_resp.json()
        assert len(history) >= 1, "Expected at least one history entry"

        # The latest entry should contain the updated parameters
        latest = history[-1]
        assert latest["session_id"] == session_id
        assert "parameters" in latest
        assert "modified_at" in latest

        gen = latest["parameters"]["generation_model"]
        assert gen["params"]["max_tokens"] == 75

    def test_history_contains_initial_state(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """Session creation also logs an initial history entry with the
        original parameters."""
        params = _base_session_params(test_doc_id)
        params["name"] = "flow_history_initial"
        resp = client.post("/api/v1/generative-session/", json=params)
        assert resp.status_code == 201, resp.text
        session_id = resp.json()["id"]

        hist_resp = client.get(
            f"/api/v1/generative-session/{session_id}/parameters-history"
        )
        assert hist_resp.status_code == 200
        history = hist_resp.json()
        assert len(history) >= 1, "Expected at least the initial state in history"

        # The first entry should match the creation parameters
        first = history[0]
        assert first["session_id"] == session_id
        prompt = first["parameters"]["prompt"]
        assert prompt["component"] == "DefaultRAGGenerationPrompt"

    def test_multiple_updates_create_multiple_history_entries(
        self,
        client: TestClient,
        test_doc_id: int,
    ):
        """Three sequential PUTs produce distinct history entries,
        each capturing the parameter state at that point in time."""
        session = _create_session(client, test_doc_id, "flow_history_multiple")
        session_id = session["id"]

        # Three updates with different temperatures
        for temp in [0.1, 0.5, 0.9]:
            new_gen = {
                "component": "Llama32_1BInstruct",
                "params": {
                    "max_tokens": 100,
                    "temperature": temp,
                    "frequency_penalty": 0.0,
                    "context_window": 512,
                    "device": "CPU",
                },
            }
            put_resp = client.put(
                f"/api/v1/generative-session/{session_id}/parameters",
                json={"generation_model": new_gen},
            )
            assert put_resp.status_code == 200, put_resp.text

        hist_resp = client.get(
            f"/api/v1/generative-session/{session_id}/parameters-history"
        )
        assert hist_resp.status_code == 200
        history = hist_resp.json()

        # 1 initial creation entry + 3 update entries = at least 4
        assert len(history) >= 4, (
            f"Expected ≥4 history entries (1 initial + 3 updates), got {len(history)}"
        )

        # The last entry should have temperature 0.9
        assert (
            history[-1]["parameters"]["generation_model"]["params"]["temperature"]
            == 0.9
        )
