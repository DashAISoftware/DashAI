from fastapi.testclient import TestClient


def test_post_plugin(client: TestClient):
    response = client.post("/api/v1/plugin/")
    assert response.status_code == 501, response.text


def test_get_all_plugins(client: TestClient):
    response = client.get("/api/v1/plugin/")
    assert response.status_code == 501, response.text


def test_get_unexistant_plugin(client: TestClient):
    response = client.get("/api/v1/plugin/31415")
    assert response.status_code == 501, response.text


def test_patch_plugin(client: TestClient):
    response = client.patch("/api/v1/plugin/1")
    assert response.status_code == 501, response.text


def test_delete_plugin(client: TestClient):
    response = client.delete("/api/v1/plugin/1")
    assert response.status_code == 501, response.text
