import json
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from DashAI.back.app import create_app

DATA_DIR = Path(__file__).parent


@pytest.fixture
def client(tmp_path: Path):
    app = create_app(local_path=tmp_path, logging_level="ERROR", enable_seeding=False)

    @asynccontextmanager
    async def nolifespan(_app):
        yield

    app.router.lifespan_context = nolifespan

    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize(
    ("file", "sep", "expected_max_rows", "expected_columns"),
    [
        (
            "iris.csv",
            ",",
            150,
            {
                "SepalLengthCm",
                "SepalWidthCm",
                "PetalLengthCm",
                "PetalWidthCm",
                "Species",
            },
        ),
        (
            "datos_comas_100.csv",
            ";",
            100,
            {"ID", "Producto", "Precio", "Descuento"},
        ),
        (
            "ds_3.csv",
            ";",
            100,
            {"ID", "Producto", "Precio", "Descuento"},
        ),
    ],
    ids=[
        "iris_csv",
        "datos_comas_100_csv",
        "ds_3_csv",
    ],
)
def test_load_preview_csv(client, file, sep, expected_max_rows, expected_columns):
    path = DATA_DIR / file
    if not path.exists():
        pytest.skip(f"File {file} not found in {DATA_DIR}, skipping test.")

    with path.open("rb") as f:
        files = {"file": (file, f, "text/csv")}
        data = {
            "params": json.dumps({"separator": sep, "dataloader_name": "CSVDataLoader"})
        }
        resp = client.post("/api/v1/dataset/preview_with_types", data=data, files=files)

    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert isinstance(payload.get("schema"), dict)
    assert isinstance(payload.get("sample"), list)
    sample_len = len(payload.get("sample"))
    assert sample_len <= expected_max_rows
    assert sample_len > 0
    assert set(payload.get("schema").keys()) == expected_columns
    assert set(payload.get("sample")[0].keys()) == expected_columns


@pytest.mark.parametrize(
    ("file", "datakey", "expected_columns"),
    [
        ("random_text.json", "text_data", {"text", "class"}),
        (
            "iris.json",
            "data",
            {"feature_0", "feature_1", "feature_2", "feature_3", "class"},
        ),
    ],
    ids=[
        "random_text_json",
        "irisDataset_json",
    ],
)
def test_load_preview_json(client, file, datakey, expected_columns):
    path = DATA_DIR / file
    if not path.exists():
        pytest.skip(f"File {file} not found in {DATA_DIR}, skipping test.")

    with path.open("rb") as f:
        files = {"file": (file, f, "application/json")}
        data = {
            "params": json.dumps(
                {"data_key": datakey, "dataloader_name": "JSONDataLoader"}
            )
        }
        resp = client.post("/api/v1/dataset/preview_with_types", data=data, files=files)

    assert resp.status_code == 200, resp.text
    payload = resp.json()

    assert isinstance(payload.get("schema"), dict)
    assert isinstance(payload.get("sample"), list)

    sample_len = len(payload.get("sample"))
    assert sample_len <= 100
    assert sample_len > 0
    assert set(payload.get("schema").keys()) == expected_columns
    assert set(payload.get("sample")[0].keys()) == expected_columns


def test_schema_change(client: TestClient):
    path = DATA_DIR / "iris.csv"
    if not path.exists():
        pytest.skip(f"File iris.csv not found in {DATA_DIR}, skipping test.")

    with path.open("rb") as f:
        files = {"file": ("iris.csv", f, "text/csv")}
        data = {
            "params": json.dumps({"separator": ",", "dataloader_name": "CSVDataLoader"})
        }
        resp = client.post("/api/v1/dataset/preview_with_types", data=data, files=files)

    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert set(payload.get("schema").keys()) == {
        "SepalLengthCm",
        "SepalWidthCm",
        "PetalLengthCm",
        "PetalWidthCm",
        "Species",
    }

    modified_schema = payload["schema"].copy()
    modified_schema["Species"] = {"type": "Categorical", "dtype": "string"}

    create_ds_resp = client.post(
        "/api/v1/dataset/",
        json={"name": "iris_testing_schema"},
    )
    assert create_ds_resp.status_code == 201, create_ds_resp.text
    dataset_id = create_ds_resp.json()["id"]

    f = path.open("rb")
    try:
        files = {"file": ("iris.csv", f, "text/csv")}
        kwargs = {
            "dataset_id": dataset_id,
            "name": "iris_testing_schema",
            "url": "",
            "file_path": str(path),
            "params": {
                "dataloader": "CSVDataLoader",
                "name": "iris_testing_schema",
                "separator": ",",
                "schema": modified_schema,
            },
        }
        form_data = {"job_type": "DatasetJob", "kwargs": json.dumps(kwargs)}
        create_resp = client.post(
            "/api/v1/job/",
            data=form_data,
            files=files,
            headers={"filename": "iris.csv"},
        )
        assert create_resp.status_code == 201, create_resp.text
    finally:
        f.close()

    from DashAI.back.job.dataset_job import DatasetJob

    job = DatasetJob(**kwargs)
    job.run()

    types_resp = client.get(f"/api/v1/dataset/{dataset_id}/types/")
    assert types_resp.status_code == 200, types_resp.text
    types = types_resp.json()

    assert types["Species"]["type"] == "Categorical"
    for col in ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]:
        assert types[col]["type"] == "Float"
        assert types[col]["dtype"] in {"float16", "float32", "float64"}
