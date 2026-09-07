"""Tests for KaggleDatasetSource."""

import json
import os
import sys
import types
from contextlib import contextmanager
from unittest.mock import MagicMock

from DashAI.back.dataset_sources.base_dataset_source import SearchPage
from DashAI.back.dataset_sources.kaggle_dataset_source import KaggleDatasetSource


@contextmanager
def fake_kaggle(api):
    """Install a stub ``kaggle`` module whose ``api`` attribute is ``api``."""
    saved = {name: sys.modules.get(name) for name in ("kaggle",)}
    mod = types.ModuleType("kaggle")
    mod.api = api
    sys.modules["kaggle"] = mod
    try:
        yield
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def _make_source():
    source = KaggleDatasetSource()
    source.get_credential = MagicMock(return_value=MagicMock())
    return source


def _dataset(ref, title="Title", description="", tags=None, total_bytes=100):
    item = MagicMock()
    item.ref = ref
    item.title = title
    item.description = description
    item.subtitle = ""
    item.tags = tags if tags is not None else []
    item.total_bytes = total_bytes
    return item


def test_kaggle_source_has_correct_type_and_credentials():
    assert KaggleDatasetSource.TYPE == "DatasetSource"
    assert KaggleDatasetSource.OPTIONAL_CREDENTIALS == ["KaggleCredential"]


def test_search_returns_dataset_entries():
    api = MagicMock()
    response = MagicMock()
    response.datasets = [
        _dataset(
            "uciml/iris",
            title="Iris Species",
            description="",
            tags=[{"name": "biology"}, {"name": "tabular"}],
            total_bytes=15347,
        )
    ]
    response.next_page_token = ""
    api.dataset_list_with_response.return_value = response

    with fake_kaggle(api):
        source = _make_source()
        page = source.search("iris", limit=5)

    api.dataset_list_with_response.assert_called_once_with(
        search="iris", page_token=None, page_size=5, sort_by="hottest"
    )
    assert isinstance(page, SearchPage)
    assert len(page.entries) == 1
    entry = page.entries[0]
    assert entry.id == "uciml/iris"
    assert entry.name == "Iris Species"
    assert entry.tags == ["biology", "tabular"]
    assert entry.size_bytes == 15347
    assert entry.url == "https://www.kaggle.com/datasets/uciml/iris"
    assert entry.source == "KaggleDatasetSource"
    assert page.next_cursor is None


def test_search_passes_cursor_and_exposes_next_cursor():
    api = MagicMock()
    response = MagicMock()
    response.datasets = [_dataset("owner/repo")]
    response.next_page_token = "tok123"
    api.dataset_list_with_response.return_value = response

    with fake_kaggle(api):
        source = _make_source()
        page = source.search("q", limit=20, cursor="prevtok")

    api.dataset_list_with_response.assert_called_once_with(
        search="q", page_token="prevtok", page_size=20, sort_by="hottest"
    )
    assert page.next_cursor == "tok123"


def test_search_uses_slug_as_name_when_title_missing():
    api = MagicMock()
    response = MagicMock()
    response.datasets = [_dataset("uciml/iris", title="")]
    response.next_page_token = ""
    api.dataset_list_with_response.return_value = response

    with fake_kaggle(api):
        source = _make_source()
        page = source.search("iris")

    assert page.entries[0].name == "iris"


def test_search_error_returns_empty_page():
    api = MagicMock()
    api.dataset_list_with_response.side_effect = Exception("boom")

    with fake_kaggle(api):
        source = _make_source()
        page = source.search("anything")

    assert page.entries == []
    assert page.next_cursor is None


def test_get_info_returns_enriched_entry():
    api = MagicMock()

    def _write_metadata(dataset, path):
        os.makedirs(path, exist_ok=True)
        meta_path = os.path.join(path, "dataset-metadata.json")
        with open(meta_path, "w") as f:
            json.dump(
                {
                    "info": {
                        "title": "Iris Species",
                        "description": "The classic iris dataset.",
                        "keywords": ["biology"],
                    }
                },
                f,
            )
        return meta_path

    api.dataset_metadata.side_effect = _write_metadata
    files_response = MagicMock()
    file_a = MagicMock()
    file_a.name = "Iris.csv"
    file_a.total_bytes = 5107
    file_b = MagicMock()
    file_b.name = "database.sqlite"
    file_b.total_bytes = 10240
    files_response.files = [file_a, file_b]
    api.dataset_list_files.return_value = files_response

    with fake_kaggle(api):
        source = _make_source()
        entry = source.get_info("uciml/iris")

    assert entry is not None
    assert entry.id == "uciml/iris"
    assert entry.name == "Iris Species"
    assert entry.description == "The classic iris dataset."
    assert entry.tags == ["biology"]
    assert entry.size_bytes == 15347
    assert entry.url == "https://www.kaggle.com/datasets/uciml/iris"
    assert entry.source == "KaggleDatasetSource"


def test_get_info_returns_none_on_error():
    api = MagicMock()
    api.dataset_metadata.side_effect = Exception("not found")

    with fake_kaggle(api):
        source = _make_source()
        entry = source.get_info("owner/repo")

    assert entry is None


def test_download_dataset_returns_path(tmp_path):
    api = MagicMock()
    api.dataset_download_files.return_value = None

    with fake_kaggle(api):
        source = _make_source()
        out = source.download_dataset("uciml/iris", str(tmp_path))

    assert out == str(tmp_path)
    kwargs = api.dataset_download_files.call_args.kwargs
    assert kwargs["path"] == str(tmp_path)
    assert kwargs["force"] is True
    assert kwargs["unzip"] is True
    api.dataset_download_files.assert_called_once_with("uciml/iris", **kwargs)
    source.get_credential.return_value.apply.assert_called_once()
