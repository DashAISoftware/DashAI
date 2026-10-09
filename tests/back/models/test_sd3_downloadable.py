"""Tests that Stable Diffusion 3 per-checkpoint models expose download metadata."""

import pytest

from DashAI.back.dependencies.downloads.downloadable import HFPretrainedDownloadMixin
from DashAI.back.models.hugging_face.stable_diffusion_v3_model import (
    StableDiffusion3Medium,
    StableDiffusion35Large,
    StableDiffusion35LargeTurbo,
    StableDiffusion35Medium,
)

_CASES = [
    (StableDiffusion3Medium, "stabilityai/stable-diffusion-3-medium-diffusers"),
    (StableDiffusion35Medium, "stabilityai/stable-diffusion-3.5-medium"),
    (StableDiffusion35Large, "stabilityai/stable-diffusion-3.5-large"),
    (StableDiffusion35LargeTurbo, "stabilityai/stable-diffusion-3.5-large-turbo"),
]


@pytest.mark.parametrize(("model_cls", "repo_id"), _CASES)
def test_sd3_is_downloadable(model_cls, repo_id):
    assert issubclass(model_cls, HFPretrainedDownloadMixin)
    assert model_cls.REQUIRES_DOWNLOAD is True
    assert model_cls.DOWNLOAD_SIZE_BYTES is not None
    assert model_cls.hf_repos() == [(repo_id, "model")]


@pytest.mark.parametrize(("model_cls", "repo_id"), _CASES)
def test_sd3_metadata_flags_download(model_cls, repo_id):
    meta = model_cls.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == model_cls.DOWNLOAD_SIZE_BYTES
