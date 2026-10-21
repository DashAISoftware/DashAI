"""Dataset flows refuse loaders whose data kind is "document"."""

import json
import uuid

import pytest

from DashAI.back.core.enums.status import DatasetStatus
from DashAI.back.dependencies.database.models import Dataset
from DashAI.back.job.base_job import JobError
from DashAI.back.job.dataset_job import DatasetJob


def test_dataset_job_refuses_a_document_loader(client, tmp_path):
    path = tmp_path / "notes.txt"
    path.write_bytes(b"Hello.")
    with client.app.container["session_factory"]() as db:
        dataset = Dataset(name=f"ds_{uuid.uuid4().hex[:8]}", file_path="")
        db.add(dataset)
        db.commit()
        dataset_id = dataset.id
    job = DatasetJob(
        kwargs={
            "dataset_id": dataset_id,
            "url": "",
            "file_path": str(path),
            "params": {"dataloader": "PlainTextDocumentDataLoader", "name": "x"},
        }
    )
    with pytest.raises(JobError, match="loads documents, not datasets"):
        job.run()
    with client.app.container["session_factory"]() as db:
        assert db.get(Dataset, dataset_id).status == DatasetStatus.ERROR


def test_preview_with_types_refuses_a_document_loader(client):
    response = client.post(
        "/api/v1/dataset/preview_with_types",
        data={"params": json.dumps({"dataloader_name": "PlainTextDocumentDataLoader"})},
        files={"file": ("notes.txt", b"Hello.", "text/plain")},
    )
    assert response.status_code == 500
    assert "loads documents, not datasets" in response.json()["detail"]
