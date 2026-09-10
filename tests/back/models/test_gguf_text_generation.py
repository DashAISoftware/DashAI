"""Tests for the per-checkpoint GGUF text-generation components."""

import pathlib

import pytest
from kink import di

from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin
from DashAI.back.initial_components import get_initial_components
from DashAI.back.models.hugging_face.llama_model import (
    Llama31_8BInstruct,
    Llama32_1BInstruct,
    Llama32_3BInstruct,
)
from DashAI.back.models.hugging_face.mistral_model import (
    Mistral7BInstructV03,
    MistralNemoInstruct2407,
)
from DashAI.back.models.hugging_face.mixtral_model import (
    Mixtral8x7BInstructQ2K,
    Mixtral8x7BInstructQ4KM,
)
from DashAI.back.models.hugging_face.qwen_model import (
    Qwen25_05BInstruct,
    Qwen25_15BInstruct,
)
from DashAI.back.models.hugging_face.smol_lm_model import (
    SmolLM2_17BInstruct,
    SmolLM2_360MInstruct,
)

ALL_CHECKPOINTS = [
    Qwen25_05BInstruct,
    Qwen25_15BInstruct,
    SmolLM2_360MInstruct,
    SmolLM2_17BInstruct,
    Llama31_8BInstruct,
    Llama32_1BInstruct,
    Llama32_3BInstruct,
    Mistral7BInstructV03,
    MistralNemoInstruct2407,
    Mixtral8x7BInstructQ4KM,
    Mixtral8x7BInstructQ2K,
]


@pytest.fixture
def component_root(tmp_path):
    sentinel = object()
    old = di["config"] if "config" in di else sentinel  # noqa: SIM401
    di["config"] = {"COMPONENT_PATH": str(tmp_path)}
    yield pathlib.Path(tmp_path)
    if old is sentinel:
        del di["config"]
    else:
        di["config"] = old


@pytest.mark.parametrize("cls", ALL_CHECKPOINTS)
def test_checkpoint_is_downloadable(cls):
    assert issubclass(cls, HFDownloadableMixin)
    assert cls.REQUIRES_DOWNLOAD is True
    assert cls.DOWNLOAD_SIZE_BYTES is not None
    assert cls.REPO_ID
    assert cls.GGUF_PATTERN


@pytest.mark.parametrize("cls", ALL_CHECKPOINTS)
def test_hf_repos_single_file_entry(cls):
    assert cls.hf_repos() == [(cls.REPO_ID, "model", [cls.GGUF_PATTERN])]


@pytest.mark.parametrize("cls", ALL_CHECKPOINTS)
def test_metadata_flags_download(cls):
    meta = cls.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == cls.DOWNLOAD_SIZE_BYTES


def test_is_downloaded_reflects_component_dir(component_root):
    cls = Qwen25_05BInstruct
    assert cls.is_downloaded() is False

    repo_dir = component_root / cls.__name__ / cls.REPO_ID.split("/")[-1]
    repo_dir.mkdir(parents=True)
    (repo_dir / "model-q8_0.gguf").write_text("weights")
    assert cls.is_downloaded() is True


def test_new_classes_registered_old_ones_gone():
    registered = {c.__name__ for c in get_initial_components()}
    for cls in ALL_CHECKPOINTS:
        assert cls.__name__ in registered
    for old in {
        "QwenModel",
        "SmolLMModel",
        "LlamaModel",
        "MistralModel",
        "MixtralModel",
    }:
        assert old not in registered
