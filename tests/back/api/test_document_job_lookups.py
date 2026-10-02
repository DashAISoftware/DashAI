"""The job queue finds and fails documents by their Huey id."""

import uuid

from DashAI.back.core.enums.status import DocumentStatus
from DashAI.back.dependencies.database.models import DataDocument
from DashAI.back.dependencies.database.utils import find_entity_by_huey_id
from DashAI.back.dependencies.job_queues.huey_job_queue import HueyJobQueue


def _create_row(client, huey_id):
    with client.app.container["session_factory"]() as db:
        row = DataDocument(
            name=f"doc_{uuid.uuid4().hex[:8]}",
            file_name="notes.txt",
            file_type="txt",
            file_hash="",
            file_path="",
            dataloader="PlainTextDocumentDataLoader",
            dataloader_params={},
            content_counts={},
            huey_id=huey_id,
            status=DocumentStatus.STARTED,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row.id, row.name


def test_find_entity_by_huey_id_reports_a_document(client):
    huey_id = f"huey-{uuid.uuid4().hex}"
    document_id, name = _create_row(client, huey_id)
    info = find_entity_by_huey_id(huey_id)
    assert info["entity_type"] == "document"
    assert info["entity_id"] == document_id
    assert info["entity_name"] == name
    assert info["status"] == DocumentStatus.STARTED


def test_mark_entity_error_marks_a_document(client):
    huey_id = f"huey-{uuid.uuid4().hex}"
    document_id, _ = _create_row(client, huey_id)
    HueyJobQueue._mark_entity_error(huey_id)
    with client.app.container["session_factory"]() as db:
        assert db.get(DataDocument, document_id).status == DocumentStatus.ERROR
