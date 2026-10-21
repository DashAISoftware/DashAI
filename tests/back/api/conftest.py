import json
import shutil
import time
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from DashAI.back.app import create_app
from DashAI.back.dependencies.database.models import Dataset
from DashAI.back.dependencies.job_queues.huey_job_queue import HueyJobQueue
from DashAI.back.job.dataset_job import DatasetJob


def remove_dir_with_retry(directory, max_attempts=5, sleep_seconds=1):
    for attempt in range(max_attempts):
        try:
            shutil.rmtree(directory)
            print(f"Successfully removed directory: {directory}")
            break
        except PermissionError as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            time.sleep(sleep_seconds)
    else:
        print(f"Failed to remove directory after {max_attempts} attempts.")


@pytest.fixture(scope="module", autouse=True)
def client(test_path: Path):
    app = create_app(
        local_path=test_path,
        logging_level="ERROR",
        enable_seeding=False,
    )

    job_queue = app.container._services.get("job_queue")
    if job_queue and isinstance(job_queue, HueyJobQueue):
        job_queue.set_test_mode(True)

    test_client = TestClient(app)
    yield test_client

    if job_queue and isinstance(job_queue, HueyJobQueue):
        job_queue.set_test_mode(False)

    app.container._services["engine"].dispose()
    remove_dir_with_retry(app.container._services["config"]["LOCAL_PATH"])


@pytest.fixture(scope="module", autouse=True)
def _mark_stable_diffusion2_downloaded(client):
    """Make ``StableDiffusion2`` appear downloaded for session/run tests.

    All generative models now require a download, so the download gate would
    reject session/run creation. Creating the component's repo folder lets the
    filesystem-reconciled gate treat it as available without fetching weights.
    """
    config = client.app.container._services["config"]
    repo_dir = (
        Path(config["COMPONENT_PATH"]) / "StableDiffusion2" / "stable-diffusion-2"
    )
    repo_dir.mkdir(parents=True, exist_ok=True)
    (repo_dir / "config.json").write_text("{}", encoding="utf-8")
    return


@pytest.fixture(name="dataset_1", scope="module")
def create_dataset_1(client) -> Dataset:
    """Create testing dataset 1 using job system."""
    abs_file_path = Path(__file__).parent / "iris.csv"

    container = client.app.container
    session_factory = container["session_factory"]

    IRIS_SCHEMA = {
        "SepalLengthCm": {"type": "Float", "dtype": "float64"},
        "SepalWidthCm": {"type": "Float", "dtype": "float64"},
        "PetalLengthCm": {"type": "Float", "dtype": "float64"},
        "PetalWidthCm": {"type": "Float", "dtype": "float64"},
        "Species": {"type": "Categorical", "dtype": "string"},
    }

    with session_factory() as db:
        iris_dataset_entry = Dataset(
            name="test_csv_1",
            file_path="",
        )
        db.add(iris_dataset_entry)
        db.commit()
        db.refresh(iris_dataset_entry)

        # run dataset_job directly to be sure the dataset is ready when the test starts
        kwargs = {
            "dataset_id": iris_dataset_entry.id,
            "url": "",
            "params": {
                "dataloader": "CSVDataLoader",
                "separator": ",",
                "name": iris_dataset_entry.name,
                "schema": IRIS_SCHEMA,
            },
            "file_path": abs_file_path,
        }
        job = DatasetJob(job_type="DatasetJob", kwargs=kwargs, db=db)
        job.run()

        db.refresh(iris_dataset_entry)
    return iris_dataset_entry


@pytest.fixture(name="upload_document")
def fixture_upload_document(client):
    """Return a helper that creates a document and runs its DocumentJob.

    The test client puts the job queue in immediate mode, so the job has run
    when the upload request returns.

    Parameters
    ----------
    client : fastapi.testclient.TestClient
        The module scoped API client.

    Returns
    -------
    Callable[..., dict]
        ``upload(content, file_name, dataloader, dataloader_params, name)``
        returning the document as ``GET /api/v1/documents/{id}`` serves it.
    """

    def _upload(
        content: bytes,
        file_name: str = "notes.txt",
        dataloader: str = "PlainTextDocumentDataLoader",
        dataloader_params: dict = None,
        name: str = None,
    ) -> dict:
        created = client.post(
            "/api/v1/documents/",
            json={
                "name": name or f"doc_{uuid.uuid4().hex[:8]}",
                "file_name": file_name,
                "dataloader": dataloader,
                "dataloader_params": dataloader_params or {},
            },
        )
        assert created.status_code == 201, created.text
        document_id = created.json()["id"]
        enqueued = client.post(
            "/api/v1/job/",
            data={
                "job_type": "DocumentJob",
                "kwargs": json.dumps({"document_id": document_id}),
            },
            files={"file": (file_name, content, "application/octet-stream")},
            headers={"filename": file_name},
        )
        assert enqueued.status_code == 201, enqueued.text
        fetched = client.get(f"/api/v1/documents/{document_id}")
        assert fetched.status_code == 200, fetched.text
        return fetched.json()

    return _upload
