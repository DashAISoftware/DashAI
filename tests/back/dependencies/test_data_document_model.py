import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from DashAI.back.core.enums.status import DocumentStatus
from DashAI.back.dependencies.database.models import Base, DataDocument, Folder


@pytest.fixture
def db():
    engine = sa.create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _document(**overrides):
    values = {"name": "report", "file_name": "report.pdf", "file_type": "pdf"}
    values.update(overrides)
    return DataDocument(**values)


def test_defaults(db):
    document = _document()
    db.add(document)
    db.commit()

    assert document.status == DocumentStatus.NOT_STARTED
    assert document.file_path == ""
    assert document.created is not None
    assert document.folder_id is None


def test_status_transitions(db):
    document = _document()
    db.add(document)
    db.commit()

    document.set_status_as_delivered()
    assert document.status == DocumentStatus.DELIVERED
    document.set_status_as_started()
    assert document.status == DocumentStatus.STARTED
    document.set_status_as_finished()
    assert document.status == DocumentStatus.FINISHED
    document.set_status_as_error()
    assert document.status == DocumentStatus.ERROR


def test_name_is_unique(db):
    db.add(_document())
    db.commit()
    db.add(_document(file_name="other.pdf"))

    with pytest.raises(IntegrityError):
        db.commit()


def test_json_fields_round_trip(db):
    document = _document(
        dataloader="PypdfDocumentDataLoader",
        dataloader_params={"extract_images": True},
        content_counts={"Text": 3, "Image": 1},
        total_pages=3,
    )
    db.add(document)
    db.commit()
    db.expire_all()

    stored = db.get(DataDocument, document.id)
    assert stored.dataloader_params == {"extract_images": True}
    assert stored.content_counts == {"Text": 3, "Image": 1}


def test_folder_relationship(db):
    folder = Folder(name="papers")
    document = _document(folder=folder)
    db.add(document)
    db.commit()

    assert folder.data_documents == [document]
    assert document.folder_id == folder.id
