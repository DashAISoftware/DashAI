"""Tests for BaseDatasetSource and DatasetEntry."""

from unittest.mock import MagicMock, patch

import pytest

from DashAI.back.dataset_sources.base_dataset_source import (
    BaseDatasetSource,
    DatasetEntry,
    SearchPage,
)
from DashAI.back.dataset_sources.huggingface_dataset_source import (
    HuggingFaceDatasetSource,
)
from DashAI.back.dataset_sources.openml_dataset_source import OpenMLDatasetSource


class ConcreteSource(BaseDatasetSource):
    DISPLAY_NAME = "Test Source"
    DESCRIPTION = "A test source"

    def search(self, query, limit=20, cursor=None, **filters):
        return SearchPage(
            entries=[
                DatasetEntry(
                    id="test/dataset",
                    name="Test Dataset",
                    description="A test dataset",
                    tags=["tabular"],
                    size_bytes=1024,
                    url="https://example.com/test",
                    source="ConcreteSource",
                )
            ],
            next_cursor=None,
        )

    def download_dataset(self, dataset_id, temp_path):
        return "/tmp/file.csv"


def test_dataset_entry_fields():
    entry = DatasetEntry(
        id="owner/name",
        name="My Dataset",
        description="desc",
        tags=["nlp"],
        size_bytes=2048,
        url="https://example.com",
        source="HuggingFaceDatasetSource",
    )
    assert entry.id == "owner/name"
    assert entry.name == "My Dataset"
    assert entry.tags == ["nlp"]
    assert entry.source == "HuggingFaceDatasetSource"


def test_dataset_entry_optional_fields():
    entry = DatasetEntry(
        id="x",
        name="x",
        description="",
        tags=[],
        size_bytes=None,
        url="",
        source="",
    )
    assert entry.size_bytes is None


def test_concrete_source_has_type():
    assert ConcreteSource.TYPE == "DatasetSource"


def test_concrete_source_search_returns_entries():
    source = ConcreteSource()
    page = source.search("test")
    assert isinstance(page, SearchPage)
    assert len(page.entries) == 1
    assert isinstance(page.entries[0], DatasetEntry)
    assert page.entries[0].id == "test/dataset"
    assert page.next_cursor is None


def test_concrete_source_download_dataset_returns_path():
    source = ConcreteSource()
    path = source.download_dataset("test/dataset", "/tmp")
    assert path == "/tmp/file.csv"


def test_incomplete_subclass_cannot_be_instantiated():
    from abc import ABC

    class Incomplete(BaseDatasetSource, ABC):
        pass

    with pytest.raises(TypeError):
        Incomplete()


def test_hf_source_has_correct_type():
    assert HuggingFaceDatasetSource.TYPE == "DatasetSource"


def _hf_item(item_id, description="", tags=None):
    item = MagicMock()
    item.id = item_id
    item.description = description
    item.tags = list(tags or [])
    return item


def test_hf_search_returns_dataset_entries():
    item = _hf_item(
        "stanfordnlp/imdb",
        description="IMDB movie review sentiment",
        tags=["text-classification"],
    )

    with patch("huggingface_hub.HfApi") as MockApi:
        MockApi.return_value.list_datasets.return_value = iter([item])
        source = HuggingFaceDatasetSource()
        page = source.search("imdb", limit=5)

    assert isinstance(page, SearchPage)
    assert len(page.entries) == 1
    assert page.entries[0].id == "stanfordnlp/imdb"
    assert page.entries[0].source == "HuggingFaceDatasetSource"
    assert page.entries[0].url == "https://huggingface.co/datasets/stanfordnlp/imdb"
    assert page.entries[0].size_bytes is None
    assert page.next_cursor is None


def test_hf_get_info_returns_size_bytes():
    mock_item = MagicMock()
    mock_item.description = "IMDB movie review sentiment"
    mock_item.tags = ["text-classification"]
    mock_item.used_storage = 83455823

    with patch("huggingface_hub.HfApi") as MockApi:
        MockApi.return_value.dataset_info.return_value = mock_item
        source = HuggingFaceDatasetSource()
        entry = source.get_info("stanfordnlp/imdb")

    assert entry is not None
    assert entry.id == "stanfordnlp/imdb"
    assert entry.size_bytes == 83455823


def test_hf_get_info_returns_none_on_error():
    with patch("huggingface_hub.HfApi") as MockApi:
        MockApi.return_value.dataset_info.side_effect = Exception("not found")
        source = HuggingFaceDatasetSource()
        entry = source.get_info("owner/repo")

    assert entry is None


def test_hf_get_info_size_none_when_used_storage_absent():
    mock_item = MagicMock()
    mock_item.description = ""
    mock_item.tags = []
    mock_item.used_storage = None

    with patch("huggingface_hub.HfApi") as MockApi:
        MockApi.return_value.dataset_info.return_value = mock_item
        source = HuggingFaceDatasetSource()
        entry = source.get_info("owner/repo")

    assert entry is not None
    assert entry.size_bytes is None


def test_hf_search_uses_cursor_as_offset():
    """cursor encodes a numeric offset; results past the offset are returned."""
    items = [_hf_item(f"owner/repo{i}") for i in range(8)]

    with patch("huggingface_hub.HfApi") as MockApi:
        MockApi.return_value.list_datasets.return_value = iter(items)
        source = HuggingFaceDatasetSource()
        page = source.search("repo", limit=3, cursor="2")

    assert [e.id for e in page.entries] == [
        "owner/repo2",
        "owner/repo3",
        "owner/repo4",
    ]
    assert page.next_cursor == "5"


def test_hf_search_next_cursor_none_when_partial_page():
    item = _hf_item("owner/repo")

    with patch("huggingface_hub.HfApi") as MockApi:
        MockApi.return_value.list_datasets.return_value = iter([item])
        source = HuggingFaceDatasetSource()
        page = source.search("repo", limit=5)

    assert page.entries[0].size_bytes is None
    assert page.next_cursor is None


def test_hf_search_handles_api_error():
    with patch("huggingface_hub.HfApi") as MockApi:
        MockApi.return_value.list_datasets.side_effect = Exception("boom")
        source = HuggingFaceDatasetSource()
        page = source.search("anything")

    assert page.entries == []
    assert page.next_cursor is None


def test_openml_source_has_correct_type():
    assert OpenMLDatasetSource.TYPE == "DatasetSource"


def _openml_list_result(rows):
    result = MagicMock()
    result.to_dict.return_value = rows
    return result


def test_openml_search_returns_dataset_entries():
    list_result = _openml_list_result([{"did": 61, "name": "iris"}])

    with (
        patch(
            "DashAI.back.dataset_sources.openml_dataset_source.openml.datasets.list_datasets",
            return_value=list_result,
        ),
        patch(
            "DashAI.back.dataset_sources.openml_dataset_source._fetch_dataset_meta",
            return_value=("Iris flower dataset.", ("study_14", "uci")),
        ),
    ):
        source = OpenMLDatasetSource()
        page = source.search("iris", limit=5)

    assert isinstance(page, SearchPage)
    assert len(page.entries) == 1
    assert page.entries[0].id == "61"
    assert page.entries[0].name == "iris"
    assert page.entries[0].size_bytes is None
    assert page.entries[0].description == "Iris flower dataset."
    assert page.entries[0].tags == ["study_14", "uci"]
    assert page.entries[0].source == "OpenMLDatasetSource"
    assert page.entries[0].url == "https://www.openml.org/d/61"
    assert page.next_cursor is None


def test_openml_search_empty_query_omits_data_name():
    """Empty query must not be passed as data_name filter."""
    list_result = _openml_list_result([])

    with patch(
        "DashAI.back.dataset_sources.openml_dataset_source.openml.datasets.list_datasets",
        return_value=list_result,
    ) as mock_list:
        source = OpenMLDatasetSource()
        source.search("", limit=20)

    kwargs = mock_list.call_args.kwargs
    assert "data_name" not in kwargs


def test_openml_search_uses_cursor_for_pagination():
    """cursor encodes numeric offset passed to list_datasets."""
    list_result = _openml_list_result([])

    with patch(
        "DashAI.back.dataset_sources.openml_dataset_source.openml.datasets.list_datasets",
        return_value=list_result,
    ) as mock_list:
        source = OpenMLDatasetSource()
        source.search("iris", limit=10, cursor="20")

    kwargs = mock_list.call_args.kwargs
    assert kwargs["offset"] == 20
    assert kwargs["size"] == 11  # limit+1 sentinel pattern


def test_openml_search_next_cursor_set_when_full_page():
    """next_cursor is non-null when limit+1 rows are returned (sentinel pattern)."""
    rows = [{"did": i, "name": f"ds{i}"} for i in range(6)]  # limit+1 sentinel
    list_result = _openml_list_result(rows)

    with (
        patch(
            "DashAI.back.dataset_sources.openml_dataset_source.openml.datasets.list_datasets",
            return_value=list_result,
        ),
        patch(
            "DashAI.back.dataset_sources.openml_dataset_source._fetch_dataset_meta",
            return_value=("", ()),
        ),
    ):
        source = OpenMLDatasetSource()
        page = source.search("x", limit=5)

    assert page.next_cursor == "5"
    assert len(page.entries) == 5  # sentinel trimmed


def test_openml_search_next_cursor_none_when_partial_page():
    """next_cursor is null when fewer results than limit are returned."""
    list_result = _openml_list_result([{"did": 1, "name": "only"}])

    with (
        patch(
            "DashAI.back.dataset_sources.openml_dataset_source.openml.datasets.list_datasets",
            return_value=list_result,
        ),
        patch(
            "DashAI.back.dataset_sources.openml_dataset_source._fetch_dataset_meta",
            return_value=("", ()),
        ),
    ):
        source = OpenMLDatasetSource()
        page = source.search("x", limit=5)

    assert page.next_cursor is None


def test_openml_search_handles_api_error():
    with patch(
        "DashAI.back.dataset_sources.openml_dataset_source.openml.datasets.list_datasets",
        side_effect=Exception("boom"),
    ):
        source = OpenMLDatasetSource()
        page = source.search("iris")

    assert page.entries == []
    assert page.next_cursor is None


def test_openml_download_dataset_returns_file(tmp_path):
    mock_dataset = MagicMock()
    mock_dataset.url = "https://openml.org/data/v1/download/22044555/iris.arff"

    arff_content = b"@relation iris\n@data\n5.1,Iris-setosa\n"
    file_response = MagicMock()
    file_response.status_code = 200
    file_response.content = arff_content
    file_response.raise_for_status = MagicMock()

    with (
        patch(
            "DashAI.back.dataset_sources.openml_dataset_source.openml.datasets.get_dataset",
            return_value=mock_dataset,
        ),
        patch(
            "DashAI.back.dataset_sources.openml_dataset_source.httpx.get",
            return_value=file_response,
        ),
    ):
        source = OpenMLDatasetSource()
        out_path = source.download_dataset("61", str(tmp_path))

    assert out_path.endswith(".arff")
    with open(out_path, "rb") as fh:
        assert b"@relation iris" in fh.read()
