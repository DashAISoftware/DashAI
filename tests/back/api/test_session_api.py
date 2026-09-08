from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import (
    GenerativeSession,
    GenerativeSessionParameterHistory,
)


def _mark_download_required_components_present(app) -> None:
    """Create each download-required component's repo folder so the download
    gate (reconciled against the filesystem) treats it as available without
    fetching weights.

    Every GGUF text-generation checkpoint (Llama32_1BInstruct, Qwen25_15BInstruct,
    etc.) requires a download, so session creation would otherwise be rejected
    with HTTP 409. Following the pattern in ``tests/back/api/conftest.py``, an
    empty file inside ``<COMPONENT_PATH>/<ClassName>/<repo-leaf>`` is enough for
    ``HFDownloadableMixin.is_downloaded`` to report the component as present.
    """
    registry = app.container["component_registry"]
    components_root = Path(app.container["config"]["COMPONENT_PATH"])

    for component_dict in registry.get_components_by_types():
        component_class = component_dict["class"]
        if not getattr(component_class, "REQUIRES_DOWNLOAD", False):
            continue
        try:
            repos = component_class.hf_repos()
        except Exception:
            continue
        for repo_id, *_ in repos:
            repo_dir = (
                components_root / component_class.__name__ / repo_id.split("/")[-1]
            )
            repo_dir.mkdir(parents=True, exist_ok=True)
            (repo_dir / "config.json").write_text("{}", encoding="utf-8")


@pytest.fixture(scope="module", autouse=True)
def mark_downloads_present(client: TestClient) -> None:
    """Mark all download-required components as present before tests run."""
    _mark_download_required_components_present(client.app)


@pytest.fixture(scope="module", name="response_1")
def create_session_1(client: TestClient):
    """Create testing session 1 using job system."""
    params = {
        "model_name": "StableDiffusion2",
        "task_name": "TextToImageGenerationTask",
        "parameters": {
            "num_inference_steps": 1,
            "model_name": "sd2-community/stable-diffusion-2",
            "guidance_scale": 6.0,
            "device": "CPU",
            "negative_prompt": "",
            "seed": 42,
            "width": 256,
            "height": 256,
            "num_images_per_prompt": 1,
        },
        "name": "session_1",
        "description": None,
    }

    response = client.post(
        "/api/v1/generative-session/",
        json=params,
    )

    return response


@pytest.fixture(scope="module", name="response_2")
def create_session_2(client: TestClient):
    """Create testing session 2 using job system."""
    params = {
        "model_name": "SomeModel",
        "task_name": "ImageGenerationTask",
        "parameters": {
            "num_inference_steps": 1,
        },
        "name": "session_2",
        "description": None,
    }

    response = client.post(
        "/api/v1/generative-session/",
        json=params,
    )

    return response


@pytest.fixture(scope="module", name="response_3")
def create_session_3(client: TestClient):
    """Create testing session 3 using a non-download-required model."""
    params = {
        "model_name": "StableDiffusion2",
        "task_name": "TextToImageGenerationTask",
        "parameters": {
            "num_inference_steps": 1,
            "model_name": "sd2-community/stable-diffusion-2",
            "guidance_scale": 6.0,
            "device": "CPU",
            "negative_prompt": "",
            "seed": 42,
            "width": 256,
            "height": 256,
            "num_images_per_prompt": 1,
        },
        "name": "session_3",
        "description": None,
    }

    response = client.post(
        "/api/v1/generative-session/",
        json=params,
    )

    return response


@pytest.fixture(scope="module", name="response_4")
def create_session_4(client: TestClient):
    """Create testing session 4 with an invalid task (valid model)."""
    params = {
        "model_name": "StableDiffusion2",
        "task_name": "SomeTask",
        "parameters": {
            "num_inference_steps": 1,
            "model_name": "sd2-community/stable-diffusion-2",
            "guidance_scale": 6.0,
            "device": "CPU",
            "negative_prompt": "",
            "seed": 42,
            "width": 256,
            "height": 256,
            "num_images_per_prompt": 1,
        },
        "name": "session_4",
        "description": None,
    }

    response = client.post(
        "/api/v1/generative-session/",
        json=params,
    )

    return response


def test_create_session(response_1):
    """Test creating a session."""
    assert response_1.status_code == 201, "Session creation failed"
    data = response_1.json()
    assert data["id"] is not None, "Session ID is missing"
    assert data["name"] == "session_1", "Session name does not match"
    assert data["model_name"] == "StableDiffusion2", "Model name does not match"
    assert data["task_name"] == "TextToImageGenerationTask", "Task name does not match"


def test_create_session_with_invalid_model(response_2):
    """Test creating a session with an invalid model."""
    assert response_2.status_code == 400
    assert response_2.json()["detail"] == "Model SomeModel is not registered."


def test_get_session_by_id(client: TestClient, response_1):
    """Test retrieving a session by ID."""
    session_id = response_1.json()["id"]
    response = client.get(f"/api/v1/generative-session/{session_id}")

    assert response.status_code == 200, "Failed to retrieve session by ID"
    data = response.json()
    assert data["id"] == session_id, "Retrieved session ID does not match"
    assert data["name"] == "session_1", "Session name does not match"
    assert data["model_name"] == "StableDiffusion2", "Model name does not match"
    assert data["task_name"] == "TextToImageGenerationTask", "Task name does not match"


def test_get_non_existent_session(client: TestClient):
    """Test retrieving a non-existent session."""
    non_existent_id = 9999
    response = client.get(f"/api/v1/generative-session/{non_existent_id}")

    assert response.status_code == 404, "Expected 404 for non-existent session"
    assert response.json()["detail"] == "Generative session 9999 does not exist in DB."


def test_get_all_sessions(
    client: TestClient,
    response_1,
    response_3,
):
    """Test retrieving all sessions."""
    response = client.get("/api/v1/generative-session/")

    assert response.status_code == 200, "Failed to retrieve all sessions"
    data = response.json()

    assert len(data) == 2, "Expected 2 sessions"

    session_ids = {session["id"] for session in data}
    assert response_1.json()["id"] in session_ids, "Session 1 not found in all sessions"
    assert response_3.json()["id"] in session_ids, "Session 3 not found in all sessions"


def test_update_generative_session_params_merges_and_logs_history(client: TestClient):
    """Test updating RAG parameters through the dedicated endpoint."""
    from DashAI.back.dependencies.database.models import Document, RAGExtractor

    session_factory = client.app.container["session_factory"]

    # Create documents in DB
    with session_factory() as db:
        doc_ids = []
        for i in range(2):
            extractor = RAGExtractor(component_name="PlainTextExtractor", params={})
            db.add(extractor)
            db.flush()
            d = Document(
                file_name=f"test_doc_{i}.txt",
                file_type="txt",
                file_path=f"/tmp/test_doc_{i}.txt",
                file_hash=f"hash_doc_{i}_update",
                extractor_id=extractor.id,
            )
            db.add(d)
            db.commit()
            db.refresh(d)
            doc_ids.append(d.id)

    # Create a prompt first so prompt_id resolution works.
    prompt_payload = {
        "class_name": "DefaultRAGGenerationPrompt",
        "name": "Test Prompt",
        "parameters": {
            "templates": {"en": "Q: {input}\nContext: {chunks}"},
            "language": "en",
        },
    }
    prompt_resp = client.post("/api/v1/prompt/", json=prompt_payload)
    assert prompt_resp.status_code == 201
    prompt_id = prompt_resp.json()["id"]

    # Create session via POST to trigger prompt_id resolution
    create_payload = {
        "model_name": "RAGPipeline",
        "task_name": "RAGTask",
        "name": "rag-session-update-test",
        "parameters": {
            "documents": doc_ids,
            "chunking_model": {
                "component": "CharacterChunkModel",
                "params": {"chunk_size": 256, "chunk_overlap": 40},
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
                    "top_k": 5,
                },
            },
            "generation_model": {
                "component": "Qwen25_15BInstruct",
                "params": {
                    "max_tokens": 128,
                    "temperature": 0.7,
                    "frequency_penalty": 0.1,
                    "context_window": 512,
                    "device": "CPU",
                },
            },
            "prompt_id": prompt_id,
        },
    }
    create_resp = client.post("/api/v1/generative-session/", json=create_payload)
    assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
    session_id = create_resp.json()["id"]

    generation_update = {
        "component": "Qwen25_15BInstruct",
        "params": {
            "max_tokens": 256,
            "temperature": 0.2,
            "frequency_penalty": 0.1,
            "context_window": 512,
            "device": "CPU",
        },
    }
    response = client.put(
        f"/api/v1/generative-session/{session_id}/parameters",
        json={
            "generation_model": generation_update,
        },
    )

    assert response.status_code == 200, f"Failed to update: {response.text}"
    data = response.json()
    assert data["id"] == session_id
    assert data["parameters"]["documents"] == [1, 2]
    assert data["parameters"]["chunking_model"] == {
        "component": "CharacterChunkModel",
        "params": {"chunk_size": 256, "chunk_overlap": 40},
    }
    assert data["parameters"]["generation_model"] == generation_update
    # prompt_id was resolved on CREATE → prompt present, prompt_id gone
    assert "prompt_id" not in data["parameters"]
    assert "prompt" in data["parameters"]

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        updated_session = db.get(GenerativeSession, session_id)
        assert updated_session is not None
        assert updated_session.parameters["documents"] == [1, 2]
        assert updated_session.parameters["generation_model"] == generation_update
        assert "prompt_id" not in updated_session.parameters
        assert "prompt" in updated_session.parameters

        history_entries = (
            db.query(GenerativeSessionParameterHistory)
            .filter(GenerativeSessionParameterHistory.session_id == session_id)
            .order_by(GenerativeSessionParameterHistory.modified_at.asc())
            .all()
        )
        # One entry from CREATE, one from UPDATE
        assert len(history_entries) == 2
        assert "prompt_id" not in history_entries[1].parameters
        assert "prompt" in history_entries[1].parameters


def test_create_session_with_invalid_task(response_4):
    """Test creating a session with an invalid task."""
    assert response_4.status_code == 400
    assert response_4.json()["detail"] == "Task SomeTask is not registered."
