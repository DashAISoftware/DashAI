"""Tests that translation transformers expose download metadata."""

import pytest
from kink import di

from DashAI.back.dependencies.downloads.downloadable import (
    HFPretrainedDownloadMixin,
)
from DashAI.back.models.hugging_face.m2m100_transformer import M2M100Transformer
from DashAI.back.models.hugging_face.nllb_transformer import NllbTransformer
from DashAI.back.models.hugging_face.t5_small_transformer import T5SmallTransformer

_CASES = [
    (M2M100Transformer, "facebook/m2m100_418M"),
    (NllbTransformer, "facebook/nllb-200-distilled-600M"),
    (T5SmallTransformer, "t5-small"),
]


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


@pytest.mark.parametrize(("model_cls", "repo_id"), _CASES)
def test_translation_is_downloadable(model_cls, repo_id):
    assert issubclass(model_cls, HFPretrainedDownloadMixin)
    assert model_cls.REQUIRES_DOWNLOAD is True
    assert model_cls.DOWNLOAD_SIZE_BYTES is not None
    assert model_cls.hf_repos() == [(repo_id, "model")]


@pytest.mark.parametrize(("model_cls", "repo_id"), _CASES)
def test_translation_metadata_flags_download(model_cls, repo_id):
    meta = model_cls.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == model_cls.DOWNLOAD_SIZE_BYTES


@pytest.mark.parametrize(("model_cls", "repo_id"), _CASES)
def test_translation_is_downloaded_uses_component_dir(
    model_cls, repo_id, component_root
):
    assert model_cls.is_downloaded() is False

    leaf = repo_id.split("/")[-1]
    repo_dir = component_root / model_cls.__name__ / leaf
    repo_dir.mkdir(parents=True)
    (repo_dir / "config.json").write_text("{}")
    assert model_cls.is_downloaded() is True
