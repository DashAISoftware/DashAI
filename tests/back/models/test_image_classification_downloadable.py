"""Tests that torchvision image classifiers expose download metadata."""

import pytest
from kink import di

from DashAI.back.dependencies.downloads.downloadable import TorchvisionDownloadMixin
from DashAI.back.models.efficientnet_b0_image_classifier import (
    EfficientNetB0ImageClassifier,
)
from DashAI.back.models.resnet18_image_classifier import ResNet18ImageClassifier
from DashAI.back.models.resnet50_image_classifier import ResNet50ImageClassifier

_CASES = [
    ResNet18ImageClassifier,
    ResNet50ImageClassifier,
    EfficientNetB0ImageClassifier,
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


@pytest.mark.parametrize("model_cls", _CASES)
def test_image_classifier_is_downloadable(model_cls):
    assert issubclass(model_cls, TorchvisionDownloadMixin)
    assert model_cls.REQUIRES_DOWNLOAD is True
    assert model_cls.DOWNLOAD_SIZE_BYTES is not None


@pytest.mark.parametrize("model_cls", _CASES)
def test_image_classifier_metadata_flags_download(model_cls):
    meta = model_cls.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == model_cls.DOWNLOAD_SIZE_BYTES


@pytest.mark.parametrize("model_cls", _CASES)
def test_is_downloaded_uses_checkpoints_dir(model_cls, component_root):
    assert model_cls.is_downloaded() is False

    ckpt = component_root / model_cls.__name__ / "checkpoints"
    ckpt.mkdir(parents=True)
    (ckpt / "weights.pth").write_bytes(b"w")
    assert model_cls.is_downloaded() is True
