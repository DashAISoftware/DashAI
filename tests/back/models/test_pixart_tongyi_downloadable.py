"""Tests that PixArt-Sigma / Tongyi Z-Image models expose download metadata."""

import pytest

from DashAI.back.dependencies.downloads.downloadable import HFPretrainedDownloadMixin
from DashAI.back.models.hugging_face.pixart_sigma_model import PixArtSigma
from DashAI.back.models.hugging_face.tongyi_z_image_model import (
    TongyiZImage,
    TongyiZImageTurbo,
)

# Single-repo checkpoints: hf_repos() is exactly one (repo_id, "model").
_SINGLE_REPO_CASES = [
    (TongyiZImage, "Tongyi-MAI/Z-Image"),
    (TongyiZImageTurbo, "Tongyi-MAI/Z-Image-Turbo"),
]

_ALL = [PixArtSigma, TongyiZImage, TongyiZImageTurbo]


@pytest.mark.parametrize(("model_cls", "repo_id"), _SINGLE_REPO_CASES)
def test_single_repo_is_downloadable(model_cls, repo_id):
    assert issubclass(model_cls, HFPretrainedDownloadMixin)
    assert model_cls.REQUIRES_DOWNLOAD is True
    assert model_cls.DOWNLOAD_SIZE_BYTES is not None
    assert model_cls.hf_repos() == [(repo_id, "model")]


def test_pixart_sigma_downloads_both_checkpoints():
    """PixArt-Sigma downloads the 1024 pipeline and the 512 transformer."""
    assert issubclass(PixArtSigma, HFPretrainedDownloadMixin)
    assert PixArtSigma.REQUIRES_DOWNLOAD is True
    assert PixArtSigma.DOWNLOAD_SIZE_BYTES is not None
    repos = [repo_id for repo_id, *_ in PixArtSigma.hf_repos()]
    assert "PixArt-alpha/PixArt-Sigma-XL-2-1024-MS" in repos
    assert "PixArt-alpha/PixArt-Sigma-XL-2-512-MS" in repos


@pytest.mark.parametrize("model_cls", _ALL)
def test_metadata_flags_download(model_cls):
    meta = model_cls.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == model_cls.DOWNLOAD_SIZE_BYTES
