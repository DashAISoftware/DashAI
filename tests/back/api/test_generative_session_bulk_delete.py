from fastapi.testclient import TestClient

SESSION_PARAMS = {
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
    "description": None,
}


def test_delete_generative_session(client: TestClient) -> None:
    response = client.post(
        "/api/v1/generative-session/",
        json={**SESSION_PARAMS, "name": "delete_me"},
    )
    assert response.status_code == 201, response.text
    session_id = response.json()["id"]

    response = client.delete(f"/api/v1/generative-session/{session_id}")
    assert response.status_code == 204, response.text

    response = client.get(f"/api/v1/generative-session/{session_id}")
    assert response.status_code == 404, response.text


def test_bulk_delete_generative_sessions(client: TestClient) -> None:
    created_ids = []
    for name in ["bulk_delete_gen_session_1", "bulk_delete_gen_session_2"]:
        response = client.post(
            "/api/v1/generative-session/",
            json={**SESSION_PARAMS, "name": name},
        )
        assert response.status_code == 201, response.text
        created_ids.append(response.json()["id"])

    # A non-existent id mixed in should be skipped rather than failing the batch.
    response = client.request(
        "DELETE",
        "/api/v1/generative-session/",
        json={"ids": [*created_ids, 999999]},
    )
    assert response.status_code == 204, response.text

    for session_id in created_ids:
        response = client.get(f"/api/v1/generative-session/{session_id}")
        assert response.status_code == 404, response.text
