"""Tests that SDXL / SDXL-Turbo models expose download metadata."""

import pytest

from DashAI.back.dependencies.downloads.downloadable import HFPretrainedDownloadMixin
from DashAI.back.models.hugging_face.sdxl_turbo_model import SDXLTurboModel
from DashAI.back.models.hugging_face.stable_diffusion_xl_model import (
    RealVisXLV4,
    StableDiffusionXL,
)

_CASES = [
    (StableDiffusionXL, "stabilityai/stable-diffusion-xl-base-1.0"),
    (RealVisXLV4, "SG161222/RealVisXL_V4.0"),
    (SDXLTurboModel, "stabilityai/sdxl-turbo"),
]


@pytest.mark.parametrize(("model_cls", "repo_id"), _CASES)
def test_sdxl_is_downloadable(model_cls, repo_id):
    assert issubclass(model_cls, HFPretrainedDownloadMixin)
    assert model_cls.REQUIRES_DOWNLOAD is True
    assert model_cls.DOWNLOAD_SIZE_BYTES is not None
    assert model_cls.hf_repos() == [(repo_id, "model")]


@pytest.mark.parametrize(("model_cls", "repo_id"), _CASES)
def test_sdxl_metadata_flags_download(model_cls, repo_id):
    meta = model_cls.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == model_cls.DOWNLOAD_SIZE_BYTES
