from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset


def test_delete_notebook(client: TestClient, dataset_1: Dataset) -> None:
    response = client.post(
        "/api/v1/notebook/",
        json={"name": "delete_me", "dataset_id": dataset_1.id},
    )
    assert response.status_code == 201, response.text
    notebook_id = response.json()["id"]

    response = client.delete(f"/api/v1/notebook/{notebook_id}")
    assert response.status_code == 204, response.text

    response = client.get(f"/api/v1/notebook/{notebook_id}")
    assert response.status_code == 404, response.text

    response = client.delete("/api/v1/notebook/10000")
    assert response.status_code == 404, response.text


def test_bulk_delete_notebooks(client: TestClient, dataset_1: Dataset) -> None:
    created_ids = []
    for name in ["bulk_delete_notebook_1", "bulk_delete_notebook_2"]:
        response = client.post(
            "/api/v1/notebook/",
            json={"name": name, "dataset_id": dataset_1.id},
        )
        assert response.status_code == 201, response.text
        created_ids.append(response.json()["id"])

    # A non-existent id mixed in should be skipped rather than failing the batch.
    response = client.request(
        "DELETE",
        "/api/v1/notebook/",
        json={"ids": [*created_ids, 999999]},
    )
    assert response.status_code == 204, response.text

    for notebook_id in created_ids:
        response = client.get(f"/api/v1/notebook/{notebook_id}")
        assert response.status_code == 404, response.text
