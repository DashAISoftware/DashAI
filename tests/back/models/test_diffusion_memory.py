"""Tests for diffusers pipeline placement and the shared schema fields."""

import gc
import weakref
from unittest import mock

import pytest
import torch

from DashAI.back.job.generative_job import _release_frames
from DashAI.back.models.hugging_face import diffusion_memory
from DashAI.back.models.hugging_face.diffusion_memory import place_pipeline
from DashAI.back.models.hugging_face.pixart_sigma_model import PixArtSigmaSchema
from DashAI.back.models.hugging_face.sd15_depth_controlnet_model import (
    SD15DepthControlNetSchema,
)
from DashAI.back.models.hugging_face.sd15_hed_controlnet_model import (
    SD15HEDControlNetSchema,
)
from DashAI.back.models.hugging_face.sd15_openpose_controlnet_model import (
    SD15OpenPoseControlNetSchema,
)
from DashAI.back.models.hugging_face.sdxl_canny_controlnet_model import (
    SDXLCannyControlNetSchema,
)
from DashAI.back.models.hugging_face.sdxl_turbo_model import SDXLTurboSchema
from DashAI.back.models.hugging_face.stable_diffusion_v1_depth_controlnet import (
    StableDiffusionXLV1ControlNetSchema,
)
from DashAI.back.models.hugging_face.stable_diffusion_v2_model import (
    StableDiffusionSchema as StableDiffusionV2Schema,
)
from DashAI.back.models.hugging_face.stable_diffusion_v3_model import (
    StableDiffusionSchema as StableDiffusionV3Schema,
)
from DashAI.back.models.hugging_face.stable_diffusion_xl_model import (
    StableDiffusionXLSchema,
)
from DashAI.back.models.hugging_face.tongyi_z_image_model import TongyiZImageSchema

GB = 1024**3

DIFFUSION_SCHEMAS = [
    PixArtSigmaSchema,
    SD15DepthControlNetSchema,
    SD15HEDControlNetSchema,
    SD15OpenPoseControlNetSchema,
    SDXLCannyControlNetSchema,
    SDXLTurboSchema,
    StableDiffusionXLV1ControlNetSchema,
    StableDiffusionV2Schema,
    StableDiffusionV3Schema,
    StableDiffusionXLSchema,
    TongyiZImageSchema,
]
TEXT_TO_IMAGE_SCHEMAS = [
    PixArtSigmaSchema,
    SDXLTurboSchema,
    StableDiffusionV2Schema,
    StableDiffusionV3Schema,
    StableDiffusionXLSchema,
    TongyiZImageSchema,
]


class _FakePipeline:
    """Stands in for a diffusers pipeline with components of given sizes."""

    def __init__(self, *component_bytes):
        # A float32 parameter of n/4 elements takes n bytes.
        self.components = {
            f"c{i}": torch.nn.Linear(1, n // 4, bias=False)
            for i, n in enumerate(component_bytes)
        }
        self.components["scheduler"] = object()
        self.to = mock.Mock(return_value=self)
        self.enable_model_cpu_offload = mock.Mock()
        self.enable_sequential_cpu_offload = mock.Mock()


def _placed_with(pipeline, free_bytes, mode="auto", device="cuda:0"):
    with mock.patch("torch.cuda.mem_get_info", return_value=(free_bytes, 12 * GB)):
        return place_pipeline(pipeline, device, mode)


@pytest.mark.parametrize(
    ("free_gb", "expected"),
    [
        # 1 KB of weights: everything fits.
        (12, "full"),
        # No room even for the largest component plus headroom.
        (1, "sequential"),
    ],
)
def test_auto_picks_by_free_vram(free_gb, expected):
    pipeline = _FakePipeline(1024)
    _placed_with(pipeline, free_gb * GB)
    calls = {
        "full": pipeline.to,
        "model": pipeline.enable_model_cpu_offload,
        "sequential": pipeline.enable_sequential_cpu_offload,
    }
    for mode, call in calls.items():
        assert call.called == (mode == expected), mode


def test_auto_offloads_by_component_when_only_the_largest_fits():
    pipeline = _FakePipeline(1024, 1024)
    with (
        mock.patch.object(diffusion_memory, "_HEADROOM_BYTES", 0),
        mock.patch.object(diffusion_memory, "_HEADROOM_FACTOR", 1.0),
    ):
        # 2048 bytes in total, 1024 in the largest component.
        _placed_with(pipeline, 1500)
    pipeline.enable_model_cpu_offload.assert_called_once_with(gpu_id=0)
    pipeline.to.assert_not_called()


@pytest.mark.parametrize(
    ("mode", "attribute"),
    [
        ("model", "enable_model_cpu_offload"),
        ("sequential", "enable_sequential_cpu_offload"),
    ],
)
def test_explicit_offload_mode_uses_the_device_index(mode, attribute):
    pipeline = _FakePipeline(1024)
    _placed_with(pipeline, 12 * GB, mode=mode, device="cuda:1")
    getattr(pipeline, attribute).assert_called_once_with(gpu_id=1)
    pipeline.to.assert_not_called()


def test_explicit_full_mode_ignores_free_vram():
    pipeline = _FakePipeline(1024)
    _placed_with(pipeline, 0, mode="full")
    pipeline.to.assert_called_once_with("cuda:0")


def test_cpu_ignores_the_mode():
    pipeline = _FakePipeline(1024)
    place_pipeline(pipeline, "cpu", "sequential")
    pipeline.to.assert_called_once_with("cpu")
    pipeline.enable_sequential_cpu_offload.assert_not_called()


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError, match="gpu_memory_mode"):
        _placed_with(_FakePipeline(1024), 12 * GB, mode="half")


@pytest.mark.parametrize("schema", DIFFUSION_SCHEMAS, ids=lambda s: s.__name__)
def test_gpu_memory_mode_is_optional_and_defaults_to_auto(schema):
    json_schema = schema.model_json_schema()
    assert "gpu_memory_mode" not in json_schema["required"]
    assert json_schema["properties"]["gpu_memory_mode"]["default"] == "auto"


@pytest.mark.parametrize("schema", TEXT_TO_IMAGE_SCHEMAS, ids=lambda s: s.__name__)
def test_negative_prompt_is_optional(schema):
    assert "negative_prompt" not in schema.model_json_schema()["required"]


def test_release_frames_frees_what_the_traceback_pinned():
    class Weights:
        pass

    refs = []

    def load(weights):
        raise RuntimeError("CUDA out of memory")

    def run():
        weights = Weights()
        refs.append(weakref.ref(weights))
        try:
            load(weights)
        except RuntimeError as e:
            raise ValueError("load failed") from e

    try:
        run()
    except ValueError as error:
        failure = error
    gc.collect()
    assert refs[0]() is not None, "the traceback frames should pin the weights"

    _release_frames(failure)
    gc.collect()
    assert refs[0]() is None
    # The traceback still says where it happened.
    assert failure.__cause__.__traceback__.tb_lineno > 0
