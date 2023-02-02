from fastapi.testclient import TestClient

from DashAI.back.main import app

client = TestClient(app)


def test_app_docs():
    response = client.get("/docs")
    assert response.status_code == 200