from DashAI.back.core.config import task_registry

from fastapi.testclient import TestClient

def test_get_all_tasks(client: TestClient):
    task_names = task_registry.registry.keys()
    response = client.get("/api/v1/task/")
    assert response.status_code == 200, response.text
    data = response.json()
    for task_name, task_data in data.items():
        assert task_name in task_names
        assert task_data["class"] in task_names
        assert task_name == task_data["class"]
