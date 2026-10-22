"""Tests for the per-checkpoint GGUF text-generation components."""

import pathlib
import sys
from types import SimpleNamespace

import pytest
from kink import di

from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin
from DashAI.back.initial_components import get_initial_components
from DashAI.back.models.hugging_face import llama_utils
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
from DashAI.back.models.hugging_face.phi_4_mini_instruct_model import (
    Phi4MiniInstructModel,
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


@pytest.fixture(autouse=True)
def _isolate_llama_log():
    """Keep the module-level llama.cpp log capture isolated per test."""
    saved = list(llama_utils._log_capture)
    llama_utils.reset_llama_log()
    yield
    llama_utils._log_capture[:] = saved


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


def _fake_checkpoint(component_root, cls):
    """Create a fake downloaded GGUF file for ``cls`` under ``component_root``."""
    repo_dir = component_root / cls.__name__ / cls.REPO_ID.split("/")[-1]
    repo_dir.mkdir(parents=True)
    gguf_path = repo_dir / "model-Q4_K_M.gguf"
    gguf_path.write_text("weights")
    return gguf_path


def test_partial_download_is_not_downloaded_and_error_is_actionable(component_root):
    """A repo dir with only non-checkpoint files is not a completed download."""
    cls = Llama32_1BInstruct
    repo_dir = component_root / cls.__name__ / cls.REPO_ID.split("/")[-1]
    repo_dir.mkdir(parents=True)
    (repo_dir / "README.md").write_text("readme")
    (repo_dir / ".cache").mkdir()
    (repo_dir / "model-Q4_K_M.gguf.incomplete").write_text("partial")

    assert cls.is_downloaded() is False

    with pytest.raises(RuntimeError) as exc_info:
        cls._local_gguf_path()

    message = str(exc_info.value)
    assert cls.__name__ in message
    assert cls.REPO_ID in message
    assert cls.GGUF_PATTERN in message
    assert "missing or incomplete" in message
    assert "re-download" in message


def test_matching_gguf_is_downloaded_and_path_resolves(component_root):
    """A file matching GGUF_PATTERN makes the component downloaded."""
    cls = Llama32_1BInstruct
    gguf_path = _fake_checkpoint(component_root, cls)

    assert cls.is_downloaded() is True
    assert cls._local_gguf_path() == gguf_path


class _FakeLlama:
    """Minimal llama.cpp backend exposing the close lifecycle hook."""

    def __init__(self):
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


class _RaisingCloseLlama(_FakeLlama):
    """Backend whose close fails after recording the call."""

    def close(self) -> None:
        self.close_calls += 1
        raise RuntimeError("inner llama close exploded")


def _wrapper_with_backend(cls, backend):
    """Build a model instance around ``backend`` without loading llama.cpp."""
    wrapper = cls.__new__(cls)
    wrapper.model = backend
    return wrapper


@pytest.mark.parametrize("cls", [Llama32_1BInstruct, Phi4MiniInstructModel])
def test_close_calls_backend_close_and_is_idempotent(cls):
    backend = _FakeLlama()
    wrapper = _wrapper_with_backend(cls, backend)

    wrapper.close()

    assert backend.close_calls == 1
    assert wrapper.model is None

    wrapper.close()
    assert backend.close_calls == 1


@pytest.mark.parametrize("cls", [Llama32_1BInstruct, Phi4MiniInstructModel])
def test_close_suppresses_backend_failure_and_drops_reference(cls):
    backend = _RaisingCloseLlama()
    wrapper = _wrapper_with_backend(cls, backend)

    wrapper.close()  # must not propagate the inner failure

    assert backend.close_calls == 1
    assert wrapper.model is None


def test_init_wraps_llama_load_failure_for_cpu(component_root, monkeypatch):
    cls = Llama32_1BInstruct
    gguf_path = _fake_checkpoint(component_root, cls)
    original = ValueError("Failed to load model from file: fake.gguf")

    # Simulate a stale GPU free-memory line left behind by an earlier load; the
    # per-load reset must keep it out of this CPU failure report.
    llama_utils._log_capture[:] = [
        "llama_prepare_model_devices: using device CUDA0 (Fake GPU) "
        "(0000:01:00.0) - 0 MiB free\n",
    ]

    def _raise_load_error(*args, **kwargs):
        raise original

    monkeypatch.setitem(
        sys.modules, "llama_cpp", SimpleNamespace(Llama=_raise_load_error)
    )

    with pytest.raises(RuntimeError) as exc_info:
        cls(
            device="CPU",
            context_window=512,
            max_tokens=10,
            temperature=0.7,
            frequency_penalty=0.1,
        )

    message = str(exc_info.value)
    assert cls.__name__ in message
    assert "device: CPU" in message
    assert str(gguf_path) in message
    assert "context_window: 512" in message
    assert "llama.cpp: Failed to load model from file: fake.gguf" in message
    assert "system memory" in message
    assert "MiB free" not in message
    assert exc_info.value.__cause__ is original


def test_build_load_error_reports_gpu_memory_and_ascii_safe_log():
    llama_utils._log_capture[:] = [
        "llama_prepare_model_devices: using device CUDA0 (Fake GPU) "
        "(0000:01:00.0) - 0 MiB free\n",
        "llama_model_load: error loading model: invalid vector subscript\n",
        "print_info: LF token = 198 '\u010a'\n",
    ]

    original = ValueError("llama.cpp failed to load the model")
    error = llama_utils.build_llama_load_error(
        model_label="TestModel",
        model_path="model.gguf",
        device="GPU 0",
        context_window=512,
        original=original,
    )
    message = str(error)

    assert "llama.cpp reported 0 MiB free on CUDA0 (Fake GPU)." in message
    assert "Another GGUF model may already be occupying the GPU" in message
    assert "invalid vector subscript" in message
    assert "llama.cpp: llama.cpp failed to load the model" in message
    assert message.isascii()
    assert "\u010a" not in message


@pytest.mark.parametrize("device", ["CPU", None])
def test_build_load_error_cpu_does_not_report_stale_gpu_memory(device):
    llama_utils._log_capture[:] = [
        "llama_prepare_model_devices: using device CUDA0 (Fake GPU) "
        "(0000:01:00.0) - 0 MiB free\n",
    ]

    error = llama_utils.build_llama_load_error(
        model_label="TestModel",
        model_path="model.gguf",
        device=device,
        context_window=512,
        original=MemoryError("allocation failed"),
    )
    message = str(error)

    assert "device: CPU" in message
    assert "system memory" in message
    assert "llama.cpp reported" not in message
    assert "Another GGUF model may already be occupying the GPU" not in message


def test_load_llama_or_raise_resets_capture_before_loading():
    llama_utils._log_capture[:] = ["stale line\n"]
    seen = {}

    def _loader():
        seen["capture"] = list(llama_utils._log_capture)
        return "loaded"

    result = llama_utils.load_llama_or_raise(
        _loader,
        model_label="TestModel",
        model_path="model.gguf",
        device="CPU",
        context_window=512,
    )

    assert result == "loaded"
    assert seen["capture"] == []


def test_load_llama_or_raise_propagates_unexpected_exception():
    def _raise_type_error():
        raise TypeError("unexpected programming error")

    with pytest.raises(TypeError, match="unexpected programming error"):
        llama_utils.load_llama_or_raise(
            _raise_type_error,
            model_label="TestModel",
            model_path="model.gguf",
            device="CPU",
            context_window=512,
        )


def test_phi4_init_wraps_from_pretrained_failure(monkeypatch):
    original = RuntimeError("Repository not found")

    class _FakeLlama:
        @classmethod
        def from_pretrained(cls, **kwargs):
            assert kwargs["repo_id"] == "unsloth/Phi-4-mini-instruct-GGUF"
            raise original

    monkeypatch.setitem(sys.modules, "llama_cpp", SimpleNamespace(Llama=_FakeLlama))

    with pytest.raises(RuntimeError) as exc_info:
        Phi4MiniInstructModel(
            model_name="unsloth/Phi-4-mini-instruct-GGUF",
            quantization="Phi-4-mini-instruct.Q8_0.gguf",
            device="CPU",
            context_window=256,
            max_tokens=10,
            temperature=0.7,
            frequency_penalty=0.1,
        )

    message = str(exc_info.value)
    assert "Phi4MiniInstructModel" in message
    assert "unsloth/Phi-4-mini-instruct-GGUF" in message
    assert "Phi-4-mini-instruct.Q8_0.gguf" in message
    assert "llama.cpp: Repository not found" in message
    assert exc_info.value.__cause__ is original


def test_reset_llama_log_clears_capture():
    llama_utils._log_capture[:] = ["first line\n", "second line\n"]

    llama_utils.reset_llama_log()

    assert llama_utils._log_capture == []


def test_log_capture_is_bounded():
    for index in range(llama_utils._LOG_CAPTURE_MAX_LINES + 50):
        llama_utils._capturing_log_cb(0, f"line {index}\n".encode(), None)

    assert len(llama_utils._log_capture) == llama_utils._LOG_CAPTURE_MAX_LINES
    assert llama_utils._log_capture[-1] == (
        f"line {llama_utils._LOG_CAPTURE_MAX_LINES + 49}\n"
    )


def test_recent_llama_log_sanitizes_non_ascii_signal_lines():
    llama_utils._log_capture[:] = [
        "device error: print_info: LF token = 198 '\u010a'\n",
    ]

    tail = llama_utils.recent_llama_log()

    assert tail.isascii()
    assert "\\u010a" in tail
    assert llama_utils.recent_llama_log(max_lines=0) == ""
    assert llama_utils.recent_llama_log(max_chars=0) == ""


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
