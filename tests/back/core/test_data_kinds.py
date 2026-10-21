import pytest

from DashAI.back.core.data_kinds import (
    DATA_KINDS,
    DATASET,
    DOCUMENT,
    component_data_kinds,
    normalize_data_kinds,
    supports_data_kind,
)


class _NoMetadata:
    """A component class that declares no metadata at all."""


class _NoneMetadata:
    """A component class whose metadata is None."""

    metadata = None


class _DocumentOnly:
    """A component class that runs on documents only."""

    metadata = {"data_kinds": ["document"]}


def test_absent_kinds_default_to_datasets_only():
    assert normalize_data_kinds(None) == ["dataset"]


def test_an_empty_list_defaults_to_datasets_only():
    assert normalize_data_kinds([]) == ["dataset"]


def test_a_single_string_is_one_kind_not_its_characters():
    assert normalize_data_kinds("document") == ["document"]


def test_duplicates_are_dropped_and_order_is_kept():
    assert normalize_data_kinds(["document", "dataset", "document"]) == [
        "document",
        "dataset",
    ]


def test_an_unknown_kind_is_refused():
    with pytest.raises(ValueError, match="tabular"):
        normalize_data_kinds(["dataset", "tabular"])


def test_the_constants_match_the_data_classes():
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
    from DashAI.back.dataloaders.classes.dashai_document import DashAIDocument

    assert DATASET == DashAIDataset.DATA_KIND
    assert DOCUMENT == DashAIDocument.DATA_KIND
    assert DATA_KINDS == (DATASET, DOCUMENT)


def test_a_component_without_metadata_is_datasets_only():
    assert component_data_kinds(_NoMetadata) == ["dataset"]
    assert component_data_kinds(_NoneMetadata) == ["dataset"]


def test_supports_data_kind_reads_the_class_metadata():
    assert supports_data_kind(_DocumentOnly, "document")
    assert not supports_data_kind(_DocumentOnly, "dataset")
    assert supports_data_kind(_NoMetadata, "dataset")
