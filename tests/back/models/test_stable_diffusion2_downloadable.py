"""Tests that Stable Diffusion 2 per-checkpoint models expose download metadata."""

import pytest
from kink import di

from DashAI.back.dependencies.downloads.downloadable import HFPretrainedDownloadMixin
from DashAI.back.models.hugging_face.stable_diffusion_v2_model import (
    StableDiffusion2,
    StableDiffusion2_512,
    StableDiffusion21,
    StableDiffusion21_512,
)

_CASES = [
    (StableDiffusion2, "sd2-community/stable-diffusion-2"),
    (StableDiffusion2_512, "sd2-community/stable-diffusion-2-base"),
    (StableDiffusion21, "sd2-community/stable-diffusion-2-1"),
    (StableDiffusion21_512, "sd2-community/stable-diffusion-2-1-base"),
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
def test_sd2_is_downloadable(model_cls, repo_id):
    assert issubclass(model_cls, HFPretrainedDownloadMixin)
    assert model_cls.REQUIRES_DOWNLOAD is True
    assert model_cls.DOWNLOAD_SIZE_BYTES is not None
    assert model_cls.hf_repos() == [(repo_id, "model")]


@pytest.mark.parametrize(("model_cls", "repo_id"), _CASES)
def test_sd2_metadata_flags_download(model_cls, repo_id):
    meta = model_cls.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == model_cls.DOWNLOAD_SIZE_BYTES


@pytest.mark.parametrize(("model_cls", "repo_id"), _CASES)
def test_sd2_is_downloaded_uses_component_dir(model_cls, repo_id, component_root):
    assert model_cls.is_downloaded() is False

    leaf = repo_id.split("/")[-1]
    repo_dir = component_root / model_cls.__name__ / leaf
    repo_dir.mkdir(parents=True)
    (repo_dir / "config.json").write_text("{}")
    assert model_cls.is_downloaded() is True
