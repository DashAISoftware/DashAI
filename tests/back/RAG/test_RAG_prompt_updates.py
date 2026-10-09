from DashAI.back.dependencies.database.models import GenerativeSession


def _get_prompt_list(client):
    response = client.get("/api/v1/prompt/")
    assert response.status_code == 200
    return response.json()


def _create_rag_session(session_factory, prompt_id: int, name: str):
    params = {
        "documents": [],
        "chunking_model": {
            "component": "CharacterChunkModel",
            "params": {
                "chunk_size": 8,
                "chunk_overlap": 2,
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
                "top_k": 1,
                "similarity_threshold": None,
            },
        },
        "generation_model": {
            "component": "Qwen25_15BInstruct",
            "params": {
                "max_tokens": 32,
                "temperature": 0.2,
                "frequency_penalty": 0.0,
                "context_window": 128,
                "device": "CPU",
            },
        },
        "prompt_id": prompt_id,
    }

    with session_factory() as db:
        session = GenerativeSession(
            model_name="RAGPipeline",
            task_name="RAGTask",
            parameters=params,
            name=name,
            description=None,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session.id


def test_session_prompt_is_edited_through_its_own_parameters(client):
    """A session's prompt is part of its parameters, edited in place.

    There used to be a PATCH on the prompt itself, but ``rag_prompt`` rows are
    deduplicated by a hash of their parameters, so one row is shared by every
    session that landed on the same template: editing it rewrote the other
    sessions' prompt too.
    """
    prompts = _get_prompt_list(client)
    session_factory = client.app.container["session_factory"]
    session_id = _create_rag_session(
        session_factory, prompts[0]["id"], "rag-prompt-edit"
    )

    response = client.put(
        f"/api/v1/generative-session/{session_id}/parameters",
        json={
            "prompt": {
                "component": "CustomRAGGenerationPrompt",
                "params": {
                    "template": "Answer using {chunks}. Question: {input}",
                    "language": "en",
                },
            }
        },
    )

    assert response.status_code == 200, response.text
    prompt = response.json()["parameters"]["prompt"]
    assert prompt["component"] == "CustomRAGGenerationPrompt"
    assert prompt["params"]["template"].startswith("Answer using {chunks}")


def test_editing_one_session_prompt_leaves_another_alone(client):
    """Two sessions starting from the same template stay independent."""
    prompts = _get_prompt_list(client)
    session_factory = client.app.container["session_factory"]
    first = _create_rag_session(session_factory, prompts[0]["id"], "rag-prompt-a")
    second = _create_rag_session(session_factory, prompts[0]["id"], "rag-prompt-b")

    shared = {
        "component": "CustomRAGGenerationPrompt",
        "params": {"template": "Shared: {chunks} {input}", "language": "en"},
    }
    for session_id in (first, second):
        response = client.put(
            f"/api/v1/generative-session/{session_id}/parameters",
            json={"prompt": shared},
        )
        assert response.status_code == 200, response.text

    edited = {
        "component": "CustomRAGGenerationPrompt",
        "params": {"template": "Only mine: {chunks} {input}", "language": "en"},
    }
    response = client.put(
        f"/api/v1/generative-session/{first}/parameters", json={"prompt": edited}
    )
    assert response.status_code == 200, response.text

    untouched = client.get(f"/api/v1/generative-session/{second}").json()
    assert untouched["parameters"]["prompt"]["params"]["template"] == (
        "Shared: {chunks} {input}"
    )


def test_prompt_id_is_resolved_into_the_session(client):
    """``prompt_id`` still works, and is copied rather than referenced.

    The id is a convenience for picking a registered template; what the
    session stores is the resolved component and its params, so nothing later
    depends on the shared row.
    """
    prompts = _get_prompt_list(client)
    base_prompt = prompts[1]
    session_factory = client.app.container["session_factory"]
    session_id = _create_rag_session(
        session_factory, base_prompt["id"], "rag-prompt-resolve"
    )

    response = client.put(
        f"/api/v1/generative-session/{session_id}/parameters",
        json={"prompt_id": base_prompt["id"]},
    )

    assert response.status_code == 200, response.text
    parameters = response.json()["parameters"]
    # The id is resolved into a component ref the session owns outright.
    assert parameters["prompt"]["component"] == base_prompt["class_name"]
    assert "params" in parameters["prompt"]
