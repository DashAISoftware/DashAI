from fastapi.testclient import TestClient
from DashAI.api.api_v1.api import app

client = TestClient(app)


def test_app_docs():
    response = client.get("/api/docs")
    assert response.status_code == 200
