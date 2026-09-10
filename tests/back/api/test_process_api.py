import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def session(client: TestClient):
    """Create a valid session for process tests."""
    params = {
        "model_name": "StableDiffusion2",
        "task_name": "TextToImageGenerationTask",
        "parameters": {
            "num_inference_steps": 1,
            "guidance_scale": 6.0,
            "device": "CPU",
            "negative_prompt": "",
            "seed": 42,
            "width": 256,
            "height": 256,
            "num_images_per_prompt": 1,
            "model_name": "sd2-community/stable-diffusion-2",
        },
        "name": "process_test_session",
        "description": None,
    }
    response = client.post("/api/v1/generative-session/", json=params)
    assert response.status_code == 201
    return response.json()["id"]


def test_create_process(client: TestClient, session):
    """Test creating a process for a session using form data."""
    data = {
        "session_id": session,
        "text_0": "A dog in a hat",
    }
    response = client.post(
        "/api/v1/generative-process/",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 201
    resp_data = response.json()
    assert resp_data["id"] is not None
    assert resp_data["session_id"] == session
    assert resp_data["status"] == 0


def test_create_process_invalid_session(client: TestClient):
    """Test creating a process with an invalid session id."""
    data = {
        "session_id": 4241,
        "text_0": "A cat in a hat",
    }
    response = client.post(
        "/api/v1/generative-process/",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Session with ID 4241 does not exist."


def test_get_process_by_id(client: TestClient, session):
    """Test retrieving a process by ID."""
    # First, create a process
    data = {
        "session_id": session,
        "text_0": "A dog in a hat",
    }
    create_response = client.post(
        "/api/v1/generative-process/",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert create_response.status_code == 201
    process_id = create_response.json()["id"]

    # Now, retrieve it
    response = client.get(f"/api/v1/generative-process/{process_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == process_id
    assert data["session_id"] == session


def test_get_non_existent_process(client: TestClient):
    """Test retrieving a non-existent process."""
    non_existent_id = 9999
    response = client.get(f"/api/v1/generative-process/{non_existent_id}")
    assert response.status_code == 404
    assert (
        response.json()["detail"] == "Generative process with ID 9999 does not exist."
    )


def test_get_all_processes_by_session_id(client: TestClient, session):
    """Test retrieving all processes for a session."""
    # Create two processes
    prompts = ["Prompt 1", "Prompt 2"]
    process_ids = []
    for prompt in prompts:
        data = {
            "session_id": session,
            "text_0": prompt,
        }
        resp = client.post(
            "/api/v1/generative-process/",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 201
        process_ids.append(resp.json()["id"])

    response = client.get(f"/api/v1/generative-process/session/{session}")
    assert response.status_code == 200
    data = response.json()
    returned_ids = {proc["id"] for proc in data}
    for pid in process_ids:
        assert pid in returned_ids


def test_create_process_missing_input_data(client: TestClient, session):
    """Test creating a process with missing input_data."""
    params = {
        "session_id": session,
        # "input_data" is missing
    }
    response = client.post("/api/v1/generative-process/", json=params)
    assert response.status_code == 422  # Unprocessable Entity
