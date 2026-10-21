"""Data kind contract of BaseDataLoader and DocumentDataLoader."""

import pytest

from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dataloaders.classes.dataloader import (
    BaseDataLoader,
    DataKindMismatchError,
    require_data_kind,
)
from DashAI.back.dataloaders.classes.document_dataloader import DocumentDataLoader
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry


class _TxtLoader(DocumentDataLoader):
    """Minimal document loader for the contract tests."""

    SUPPORTED_EXTENSIONS = frozenset({".txt"})


def test_dataset_loaders_declare_the_dataset_kind():
    assert BaseDataLoader.DATA_KIND == "dataset"
    assert CSVDataLoader.get_metadata()["data_kinds"] == ["dataset"]
    with pytest.raises(NotImplementedError):
        CSVDataLoader().load_document("any.csv", {})


def test_document_loaders_declare_the_document_kind():
    metadata = _TxtLoader.get_metadata()
    assert metadata["data_kinds"] == ["document"]
    assert metadata["supported_extensions"] == [".txt"]
    assert metadata["category"].en == "Document Extractor"
    with pytest.raises(NotImplementedError, match="load_document"):
        _TxtLoader().load_data("a.txt", "tmp", {})


def test_tags_are_the_supported_file_formats():
    """The card and the details panel label a loader by the formats it reads,
    so the tags come from the same extensions that drive the file picker."""
    assert _TxtLoader.get_metadata()["tags"] == ["TXT"]
    assert CSVDataLoader.get_metadata()["tags"] == ["CSV", "ZIP"]
    assert BaseDataLoader.get_metadata()["tags"] == []


def test_document_loaders_stay_in_the_dataloader_type():
    registry = ComponentRegistry(initial_components=[CSVDataLoader, _TxtLoader])
    assert set(registry.registry["DataLoader"]) == {"CSVDataLoader", "_TxtLoader"}


def test_require_data_kind():
    require_data_kind(CSVDataLoader, "dataset")
    require_data_kind(_TxtLoader, "document")
    with pytest.raises(DataKindMismatchError, match="loads documents, not datasets"):
        require_data_kind(_TxtLoader, "dataset")
    with pytest.raises(DataKindMismatchError, match="loads datasets, not documents"):
        require_data_kind(CSVDataLoader, "document")


def test_document_loader_helpers(tmp_path):
    loader = _TxtLoader()
    assert _TxtLoader.supports_file("NOTES.TXT")
    assert not _TxtLoader.supports_file("notes.pdf")
    assert loader.build_metadata(str(tmp_path / "a.TXT"), {"x": 1}, None) == {
        "file_name": "a.TXT",
        "file_type": "txt",
        "n_pages": None,
        "dataloader": "_TxtLoader",
        "dataloader_params": {"x": 1},
    }
