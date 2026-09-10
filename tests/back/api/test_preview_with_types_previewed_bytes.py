"""Verify /preview_with_types includes previewed_bytes in the response."""

import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_preview_with_types_includes_previewed_bytes(client: TestClient):
    iris_path = Path(__file__).parent / "iris.csv"
    file_size = iris_path.stat().st_size

    with open(iris_path, "rb") as fh:
        files = {"file": ("iris.csv", fh, "text/csv")}
        data = {
            "params": json.dumps(
                {
                    "dataloader_name": "CSVDataLoader",
                    "separator": ",",
                    "inference_rows": 50,
                }
            )
        }
        response = client.post(
            "/api/v1/dataset/preview_with_types", files=files, data=data
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert "previewed_bytes" in body
    assert isinstance(body["previewed_bytes"], int)
    assert body["previewed_bytes"] > 0
    assert body["previewed_bytes"] <= file_size
