"""Tests that text classification transformers expose download metadata."""

import pytest
from kink import di

from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin
from DashAI.back.models.hugging_face.distilbert_transformer import DistilBertTransformer


@pytest.fixture
def component_root(tmp_path):
    """Inject a temporary COMPONENT_PATH into the kink DI container."""
    sentinel = object()
    old = di["config"] if "config" in di else sentinel  # noqa: SIM401
    di["config"] = {"COMPONENT_PATH": str(tmp_path)}
    yield tmp_path
    if old is sentinel:
        del di["config"]
    else:
        di["config"] = old


def test_text_classification_is_downloadable():
    assert issubclass(DistilBertTransformer, HFDownloadableMixin)
    assert DistilBertTransformer.REQUIRES_DOWNLOAD is True
    assert DistilBertTransformer.DOWNLOAD_SIZE_BYTES is not None


def test_hf_repos_derived_from_model_name():
    assert DistilBertTransformer.hf_repos() == [("distilbert-base-uncased", "model")]


def test_metadata_flags_download():
    meta = DistilBertTransformer.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == DistilBertTransformer.DOWNLOAD_SIZE_BYTES


def test_is_downloaded_uses_component_dir(component_root):
    assert DistilBertTransformer.is_downloaded() is False

    repo_dir = component_root / "DistilBertTransformer" / "distilbert-base-uncased"
    repo_dir.mkdir(parents=True)
    (repo_dir / "config.json").write_text("{}")
    assert DistilBertTransformer.is_downloaded() is True
