"""Tests that ControlNet models expose multi-repo download metadata."""

import pytest
from kink import di

from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin
from DashAI.back.models.hugging_face.sd15_depth_controlnet_model import (
    SD15DepthControlNetModel,
)
from DashAI.back.models.hugging_face.sd15_hed_controlnet_model import (
    SD15HEDControlNetModel,
)
from DashAI.back.models.hugging_face.sd15_openpose_controlnet_model import (
    SD15OpenPoseControlNetModel,
)
from DashAI.back.models.hugging_face.sdxl_canny_controlnet_model import (
    SDXLCannyControlNetModel,
)
from DashAI.back.models.hugging_face.stable_diffusion_v1_depth_controlnet import (
    StableDiffusionXLV1ControlNet,
)

_CLASSES = [
    SD15DepthControlNetModel,
    SD15HEDControlNetModel,
    SD15OpenPoseControlNetModel,
    SDXLCannyControlNetModel,
    StableDiffusionXLV1ControlNet,
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


@pytest.mark.parametrize("model_cls", _CLASSES)
def test_controlnet_is_downloadable(model_cls):
    assert issubclass(model_cls, HFDownloadableMixin)
    assert model_cls.REQUIRES_DOWNLOAD is True
    assert model_cls.DOWNLOAD_SIZE_BYTES is not None
    # Each ControlNet pulls several repos (base + controlnet [+ vae]).
    assert len(model_cls.hf_repos()) >= 2


# Preprocessor repos are fetched by download() (not from the Hub at run time),
# so they must be part of hf_repos() for the models that use one.
_PREPROCESSOR_REPOS = {
    SD15DepthControlNetModel: "Intel/dpt-hybrid-midas",
    SD15HEDControlNetModel: "lllyasviel/Annotators",
    SD15OpenPoseControlNetModel: "lllyasviel/Annotators",
    StableDiffusionXLV1ControlNet: "Intel/dpt-hybrid-midas",
}


@pytest.mark.parametrize(("model_cls", "repo"), _PREPROCESSOR_REPOS.items())
def test_controlnet_preprocessor_included(model_cls, repo):
    assert repo in [rid for rid, *_ in model_cls.hf_repos()]


@pytest.mark.parametrize("model_cls", _CLASSES)
def test_controlnet_metadata_flags_download(model_cls):
    meta = model_cls.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == model_cls.DOWNLOAD_SIZE_BYTES


def test_controlnet_is_downloaded_requires_all_repos(component_root):
    """is_downloaded must be True only when every repo dir is present."""
    model_cls = SD15DepthControlNetModel
    repos = [rid for rid, *_ in model_cls.hf_repos()]

    assert model_cls.is_downloaded() is False

    # Only the first repo present -> still not downloaded.
    first = component_root / model_cls.__name__ / repos[0].split("/")[-1]
    first.mkdir(parents=True)
    (first / "config.json").write_text("{}")
    assert model_cls.is_downloaded() is False

    # All repos present -> downloaded.
    for rid in repos[1:]:
        d = component_root / model_cls.__name__ / rid.split("/")[-1]
        d.mkdir(parents=True)
        (d / "config.json").write_text("{}")
    assert model_cls.is_downloaded() is True
