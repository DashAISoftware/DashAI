"""Contract tests for the units DocumentJob is built from."""

import hashlib

import pytest
from kink import di

from DashAI.back.core.enums.status import DatafileStatus
from DashAI.back.dataloaders.classes.dashai_document import load_document
from DashAI.back.job.base_job import JobError
from DashAI.back.types.value_types import Text
from DashAI.back.units.context import ExecutionContext, UnitContractError
from DashAI.back.units.parse_document_unit import ParseDocumentUnit
from DashAI.back.units.save_document_to_path_unit import SaveDocumentToPathUnit
from DashAI.back.units.store_datafile_document_source_unit import (
    StoreDatafileDocumentSourceUnit,
)
from DashAI.back.units.store_uploaded_document_source_unit import (
    StoreUploadedDocumentSourceUnit,
)

BODY = b"First paragraph.\n\nSecond paragraph."


class _DatafileRow:
    def __init__(self, local_path, status):
        self.local_path = local_path
        self.status = status


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows

    def get(self, model, row_id):
        return self._rows.get(row_id)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class _FakeSessionFactory:
    """A class, not a lambda, so kink hands it over instead of calling it."""

    def __init__(self, rows):
        self._rows = rows

    def __call__(self):
        return _FakeSession(self._rows)


@pytest.fixture(name="registry")
def fixture_registry():
    """A registry with one document loader and one dataset loader."""
    from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
    from DashAI.back.dataloaders.classes.plain_text_document_dataloader import (
        PlainTextDocumentDataLoader,
    )
    from DashAI.back.dependencies.registry import ComponentRegistry

    registry = ComponentRegistry(
        initial_components=[PlainTextDocumentDataLoader, CSVDataLoader]
    )
    di["component_registry"] = registry
    yield registry
    del di["component_registry"]


@pytest.fixture(name="datafile_rows")
def fixture_datafile_rows():
    rows = {}
    di["session_factory"] = _FakeSessionFactory(rows)
    yield rows
    del di["session_factory"]


@pytest.fixture(name="text_file")
def fixture_text_file(tmp_path):
    path = tmp_path / "upload" / "notes.txt"
    path.parent.mkdir()
    path.write_bytes(BODY)
    return path


def _plain_text_loader(**params):
    return {"component": "PlainTextDocumentDataLoader", "params": params}


def test_uploaded_source_unit_copies_and_hashes_the_upload(text_file, tmp_path):
    ctx = ExecutionContext()

    StoreUploadedDocumentSourceUnit(
        upload_path=str(text_file),
        file_name="renamed.txt",
        path=str(tmp_path / "doc" / "source"),
    )(ctx)

    stored = tmp_path / "doc" / "source" / "renamed.txt"
    assert ctx.require("source_path") == str(stored)
    assert stored.read_bytes() == BODY
    assert ctx.require("file_hash") == hashlib.sha256(BODY).hexdigest()


def test_datafile_source_unit_copies_the_selected_file(datafile_rows, tmp_path):
    download = tmp_path / "download"
    (download / "nested").mkdir(parents=True)
    (download / "nested" / "notes.txt").write_bytes(BODY)
    (download / "other.txt").write_bytes(b"Other.")
    datafile_rows[7] = _DatafileRow(str(download), DatafileStatus.READY)
    ctx = ExecutionContext()

    StoreDatafileDocumentSourceUnit(
        datafile_id=7,
        selected_file="nested/notes.txt",
        path=str(tmp_path / "doc" / "source"),
    )(ctx)

    stored = tmp_path / "doc" / "source" / "notes.txt"
    assert ctx.require("source_path") == str(stored)
    assert stored.read_bytes() == BODY
    assert ctx.require("file_hash") == hashlib.sha256(BODY).hexdigest()
    assert (download / "nested" / "notes.txt").is_file()


def test_datafile_source_unit_takes_the_first_visible_file(datafile_rows, tmp_path):
    download = tmp_path / "download"
    (download / ".cache").mkdir(parents=True)
    (download / ".cache" / "aaa.txt").write_bytes(b"junk")
    (download / "notes.txt").write_bytes(BODY)
    datafile_rows[7] = _DatafileRow(str(download), DatafileStatus.READY)
    ctx = ExecutionContext()

    StoreDatafileDocumentSourceUnit(
        datafile_id=7, selected_file=None, path=str(tmp_path / "source")
    )(ctx)

    assert ctx.require("source_path") == str(tmp_path / "source" / "notes.txt")


def test_datafile_source_unit_rejects_an_unfinished_download(datafile_rows, tmp_path):
    datafile_rows[7] = _DatafileRow(str(tmp_path), DatafileStatus.DOWNLOADING)

    with pytest.raises(JobError) as excinfo:
        StoreDatafileDocumentSourceUnit(
            datafile_id=7, selected_file=None, path=str(tmp_path / "source")
        )(ExecutionContext())

    assert str(excinfo.value) == "Datafile 7 is not ready."
    assert not (tmp_path / "source").exists()


def test_parse_unit_parses_the_stored_source(registry, text_file):
    ctx = ExecutionContext()
    ctx.put_ref("source_path", str(text_file))

    ParseDocumentUnit(dataloader=_plain_text_loader(split_paragraphs=True))(ctx)

    assert ctx.require("document")[Text] == [
        "First paragraph.",
        "Second paragraph.",
    ]


def test_parse_unit_needs_a_stored_source(registry):
    with pytest.raises(UnitContractError):
        ParseDocumentUnit(dataloader=_plain_text_loader())(ExecutionContext())


@pytest.mark.parametrize(
    ("component", "message"),
    [
        ("MissingLoader", "Document loader 'MissingLoader' is not registered."),
        ("CSVDataLoader", "loads datasets, not documents"),
    ],
)
def test_parse_unit_validates_the_loader_without_a_source(registry, component, message):
    unit = ParseDocumentUnit(dataloader={"component": component, "params": {}})

    with pytest.raises(JobError, match=message):
        unit.validate(ExecutionContext())


def test_save_unit_writes_the_document(registry, text_file, tmp_path):
    ctx = ExecutionContext()
    ctx.put_ref("source_path", str(text_file))
    ParseDocumentUnit(dataloader=_plain_text_loader(split_paragraphs=True))(ctx)

    SaveDocumentToPathUnit(path=str(tmp_path / "document"))(ctx)

    assert load_document(str(tmp_path / "document"))[Text] == [
        "First paragraph.",
        "Second paragraph.",
    ]


def test_save_unit_keeps_the_original_error(tmp_path):
    ctx = ExecutionContext()
    ctx.put("document", object())

    with pytest.raises(JobError, match="Can not save document to path"):
        SaveDocumentToPathUnit(path=str(tmp_path / "document"))(ctx)
