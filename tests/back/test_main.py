from fastapi.testclient import TestClient

from DashAI.back.app import create_app


def test_app_front():
    client = TestClient(create_app())

    response = client.get("/app/")
    assert response.status_code == 200
