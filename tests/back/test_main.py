from fastapi.testclient import TestClient

from DashAI.back.core.app import app

client = TestClient(app)


def test_app_docs():
    response = client.get("/app/")
    assert response.status_code == 200
