import os

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import DatasetStatus
from DashAI.back.dependencies.database.models import Dataset


@pytest.fixture(scope="module")
def dataset_not_started(client) -> Dataset:
    """Create testing dataset 2 using job system."""
    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        iris_dataset_entry = Dataset(
            name="test_csv_2",
            file_path="",
        )
        db.add(iris_dataset_entry)
        db.commit()
        db.refresh(iris_dataset_entry)

    return iris_dataset_entry


@pytest.mark.dependency
def test_create_dataset(client: TestClient) -> None:
    response = client.post("/api/v1/dataset/", json={"name": "test_csv"})

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "test_csv"

    response = client.get(f"/api/v1/dataset/{data['id']}")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "test_csv"
    assert data["status"] == DatasetStatus.NOT_STARTED.value
    assert data["id"] is not None
    assert data["file_path"] == ""


@pytest.mark.dependency(depends=["test_create_dataset"])
def test_get_all_datasets(client: TestClient, dataset_1: Dataset) -> None:
    response = client.get("/api/v1/dataset/")
    assert response.status_code == 200, response.text
    data = response.json()

    assert len(data) == 2, "There should be 2 datasets in the DB"

    dataset_names = [dataset["name"] for dataset in data]
    assert "test_csv" in dataset_names
    assert "test_csv_1" in dataset_names


def test_dataset_has_row_column_fields(client: TestClient, dataset_1: Dataset) -> None:
    response = client.get(f"/api/v1/dataset/{dataset_1.id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "total_rows" in data
    assert "total_columns" in data


def test_dataset_job_writes_counts(client: TestClient, dataset_1: Dataset) -> None:
    response = client.get(f"/api/v1/dataset/{dataset_1.id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total_rows"] == 150
    assert data["total_columns"] == 5


def test_get_dataset(client: TestClient, dataset_1: Dataset) -> None:
    response = client.get(f"/api/v1/dataset/{dataset_1.id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == dataset_1.name
    assert data["id"] == dataset_1.id
    assert data["status"] == DatasetStatus.FINISHED.value
    expected_path_str = os.path.normpath(str(dataset_1.file_path))
    actual_path_str = os.path.normpath(data["file_path"])
    assert actual_path_str == expected_path_str


def test_get_unexistant_dataset(client: TestClient) -> None:
    response = client.get("/api/v1/dataset/31415")
    assert response.status_code == 404, response.text
    assert response.text == '{"detail":"Dataset not found"}'


def test_get_types(
    client: TestClient, dataset_1: Dataset, dataset_not_started: Dataset
) -> None:
    response = client.get(f"/api/v1/dataset/{dataset_1.id}/types")
    data = response.json()
    assert data == {
        "SepalLengthCm": {"type": "Float", "dtype": "float64"},
        "SepalWidthCm": {"type": "Float", "dtype": "float64"},
        "PetalLengthCm": {"type": "Float", "dtype": "float64"},
        "PetalWidthCm": {"type": "Float", "dtype": "float64"},
        "Species": {
            "type": "Categorical",
            "dtype": "string",
            "encoder": "one_hot",
            "categories": ["Iris-setosa", "Iris-versicolor", "Iris-virginica"],
            "num_categories": 3,
            "converted": False,
        },
    }

    response = client.get(f"/api/v1/dataset/{dataset_not_started.id}/types")
    assert response.status_code == 422, response.text
    assert response.text == '{"detail":"Dataset is not in finished state"}'


def test_modify_dataset_name(client: TestClient, dataset_1: Dataset) -> None:
    response = client.patch(
        f"/api/v1/dataset/{dataset_1.id}",
        json={"name": "test_modify_name"},
    )
    assert response.status_code == 200, response.text
    response = client.get(f"/api/v1/dataset/{dataset_1.id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "test_modify_name"


@pytest.mark.dependency(depends=["test_get_types"])
def test_update_column_encoder_ok(client: TestClient, dataset_1: Dataset) -> None:
    """Change a categorical column's encoder."""
    response = client.patch(
        f"/api/v1/dataset/{dataset_1.id}/columns/Species/encoder",
        json={"encoder": "label"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["Species"]["encoder"] == "label"

    # Verify persisted
    response = client.get(f"/api/v1/dataset/{dataset_1.id}/types")
    assert response.json()["Species"]["encoder"] == "label"

    # Reset back to one_hot for downstream tests
    client.patch(
        f"/api/v1/dataset/{dataset_1.id}/columns/Species/encoder",
        json={"encoder": "one_hot"},
    )


@pytest.mark.dependency(depends=["test_get_types"])
def test_update_column_encoder_non_categorical(
    client: TestClient, dataset_1: Dataset
) -> None:
    """Updating encoder on a non-categorical column returns 422."""
    response = client.patch(
        f"/api/v1/dataset/{dataset_1.id}/columns/SepalLengthCm/encoder",
        json={"encoder": "label"},
    )
    assert response.status_code == 422, response.text


@pytest.mark.dependency(depends=["test_get_types"])
def test_update_column_encoder_invalid_value(
    client: TestClient, dataset_1: Dataset
) -> None:
    """Invalid encoder value returns 422."""
    response = client.patch(
        f"/api/v1/dataset/{dataset_1.id}/columns/Species/encoder",
        json={"encoder": "bogus_encoder"},
    )
    assert response.status_code == 422, response.text


@pytest.mark.dependency(depends=["test_get_types"])
def test_update_column_encoder_column_not_found(
    client: TestClient, dataset_1: Dataset
) -> None:
    """Unknown column name returns 404."""
    response = client.patch(
        f"/api/v1/dataset/{dataset_1.id}/columns/nonexistent_col/encoder",
        json={"encoder": "label"},
    )
    assert response.status_code == 404, response.text


@pytest.mark.dependency(depends=["test_get_types"])
def test_update_column_encoder_dataset_not_started(
    client: TestClient, dataset_not_started: Dataset
) -> None:
    """Dataset not in FINISHED state returns 422."""
    response = client.patch(
        f"/api/v1/dataset/{dataset_not_started.id}/columns/col/encoder",
        json={"encoder": "label"},
    )
    assert response.status_code == 422, response.text


def test_backfill_populates_null_counts(client: TestClient, dataset_1: Dataset) -> None:
    container = client.app.container
    session_factory = container["session_factory"]

    with session_factory() as db:
        ds = db.get(Dataset, dataset_1.id)
        ds.total_rows = None
        ds.total_columns = None
        db.commit()

    from DashAI.back.dependencies.database.backfill import backfill_dataset_counts

    backfill_dataset_counts(session_factory)

    with session_factory() as db:
        ds = db.get(Dataset, dataset_1.id)
        assert ds.total_rows == 150
        assert ds.total_columns == 5


def test_delete_dataset(client: TestClient, dataset_1: Dataset) -> None:
    response = client.delete(f"/api/v1/dataset/{dataset_1.id}")
    assert response.status_code == 204, response.text

    response = client.delete("/api/v1/dataset/10000")
    assert response.status_code == 404, response.text


def test_bulk_delete_datasets(client: TestClient) -> None:
    created_ids = []
    for name in ["bulk_delete_1", "bulk_delete_2"]:
        response = client.post("/api/v1/dataset/", json={"name": name})
        assert response.status_code == 201, response.text
        created_ids.append(response.json()["id"])

    # A non-existent id mixed in should be skipped rather than failing the batch.
    response = client.request(
        "DELETE",
        "/api/v1/dataset/",
        json={"ids": [*created_ids, 999999]},
    )
    assert response.status_code == 204, response.text

    for dataset_id in created_ids:
        response = client.get(f"/api/v1/dataset/{dataset_id}")
        assert response.status_code == 404, response.text
