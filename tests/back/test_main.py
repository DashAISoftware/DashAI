from fastapi.testclient import TestClient

from DashAI.back.server import create_app


def test_app_docs():
    client = TestClient(create_app())

    response = client.get("/app/")
    assert response.status_code == 200
