"""Error classification tests for ``llama_utils.load_llama_or_raise``.

The loader must tell three failure modes apart without loading a model:

* a HuggingFace/HTTP download failure,
* an unreadable local GGUF file,
* a genuine llama.cpp load failure (the memory-oriented diagnostics).

No real model is loaded; every loader is a stub that raises.
"""

from __future__ import annotations

import pytest

from DashAI.back.models.hugging_face import llama_utils
from DashAI.back.models.hugging_face.llama_utils import (
    build_llama_load_error,
    is_download_error,
    load_llama_or_raise,
)

_LABEL = "Test GGUF"
_PATH = "org/repo/model.gguf"


@pytest.fixture(autouse=True)
def _reset_captured_log() -> None:
    """Keep the process-wide llama.cpp log capture isolated between tests."""
    llama_utils.reset_llama_log()


def _error_class(name: str, module: str, *, base: type = OSError) -> type:
    """Create an exception class whose module root is ``module``."""
    error_cls = type(name, (base,), {})
    error_cls.__module__ = module
    return error_cls


def _loader_raising(error: Exception):
    """Return a zero-argument loader that raises ``error``."""

    def _loader():
        raise error

    return _loader


def _assert_no_memory_hints(message: str) -> None:
    """Assert the memory-oriented diagnostics are absent from ``message``."""
    assert "MiB free" not in message
    assert llama_utils._LOAD_ERROR_HINT_GPU not in message
    assert llama_utils._LOAD_ERROR_HINT_CPU not in message
    assert "Another GGUF model" not in message
    assert "may not fit in available system memory" not in message


def test_huggingface_download_error_gets_download_message() -> None:
    """A HuggingFace exception is reported as a download failure."""
    error = _error_class("RepositoryNotFoundError", "huggingface_hub.errors")(
        "repository not found"
    )

    with pytest.raises(RuntimeError) as excinfo:
        load_llama_or_raise(
            _loader_raising(error),
            model_label=_LABEL,
            model_path=_PATH,
            device="GPU 0",
            context_window=2048,
        )

    message = str(excinfo.value)
    assert "Could not download GGUF model" in message
    assert _LABEL in message
    assert _PATH in message
    assert "repository not found" in message
    assert "repository name" in message
    assert "network" in message
    _assert_no_memory_hints(message)


def test_http_module_error_gets_download_message() -> None:
    """An exception rooted in an HTTP client module is a download failure."""
    error = _error_class("ConnectError", "httpx._exceptions")("connection refused")

    with pytest.raises(RuntimeError) as excinfo:
        load_llama_or_raise(
            _loader_raising(error),
            model_label=_LABEL,
            model_path=_PATH,
            device=None,
            context_window=512,
        )

    message = str(excinfo.value)
    assert "Could not download GGUF model" in message
    assert "connection refused" in message
    _assert_no_memory_hints(message)


def test_entry_not_found_error_gets_download_message() -> None:
    """A HuggingFace ``EntryNotFoundError`` is a download failure.

    It does not necessarily subclass ``OSError``, so it used to bypass the
    wrapper entirely.
    """
    error = _error_class(
        "EntryNotFoundError", "huggingface_hub.errors", base=Exception
    )("entry not found")

    with pytest.raises(RuntimeError) as excinfo:
        load_llama_or_raise(
            _loader_raising(error),
            model_label=_LABEL,
            model_path=_PATH,
            device="GPU 0",
            context_window=2048,
        )

    message = str(excinfo.value)
    assert "Could not download GGUF model" in message
    assert "entry not found" in message
    assert "Could not read GGUF model file" not in message
    _assert_no_memory_hints(message)


def test_file_not_found_wrapping_repository_error_gets_download_message() -> None:
    """``HfFileSystem.ls`` can turn a repository error into ``FileNotFoundError``.

    The wrapped repository failure in the chain must win over the local-file
    classification.
    """
    cause = _error_class("RepositoryNotFoundError", "huggingface_hub.errors")(
        "repository not found"
    )
    error = FileNotFoundError("No such file or directory")
    error.__cause__ = cause

    assert is_download_error(error) is True

    with pytest.raises(RuntimeError) as excinfo:
        load_llama_or_raise(
            _loader_raising(error),
            model_label=_LABEL,
            model_path=_PATH,
            device="GPU 0",
            context_window=2048,
        )

    message = str(excinfo.value)
    assert "Could not download GGUF model" in message
    assert "Could not read GGUF model file" not in message
    assert "missing, unreadable or incomplete" not in message
    _assert_no_memory_hints(message)


def test_huggingface_value_error_gets_download_message() -> None:
    """A ``ValueError`` raised from HuggingFace is a download failure, not memory."""
    error = _error_class(
        "LocalEntryNotFoundError", "huggingface_hub.utils", base=ValueError
    )("No file found in the cache")

    with pytest.raises(RuntimeError) as excinfo:
        load_llama_or_raise(
            _loader_raising(error),
            model_label=_LABEL,
            model_path=_PATH,
            device="GPU 0",
            context_window=2048,
        )

    message = str(excinfo.value)
    assert "Could not download GGUF model" in message
    assert "No file found in the cache" in message
    _assert_no_memory_hints(message)


def test_plain_type_error_propagates_unchanged() -> None:
    """A programming error is re-raised instead of being misdiagnosed."""
    error = TypeError("programming bug")

    with pytest.raises(TypeError, match="programming bug") as excinfo:
        load_llama_or_raise(
            _loader_raising(error),
            model_label=_LABEL,
            model_path=_PATH,
            device="GPU 0",
            context_window=2048,
        )

    assert excinfo.value is error


def test_real_huggingface_exception_is_download_error() -> None:
    """A real installed huggingface_hub exception is classified as a download."""
    errors = pytest.importorskip("huggingface_hub.errors")
    error = errors.LocalEntryNotFoundError("no local entry")

    assert is_download_error(error) is True


def test_local_file_oserror_gets_file_message() -> None:
    """A plain ``OSError`` is reported as a local file problem, not a download."""
    error = FileNotFoundError("No such file or directory")

    assert is_download_error(error) is False

    with pytest.raises(RuntimeError) as excinfo:
        load_llama_or_raise(
            _loader_raising(error),
            model_label=_LABEL,
            model_path=_PATH,
            device="GPU 0",
            context_window=2048,
        )

    message = str(excinfo.value)
    assert "Could not read GGUF model file" in message
    assert _LABEL in message
    assert _PATH in message
    assert "missing, unreadable or incomplete" in message
    assert "No such file or directory" in message
    _assert_no_memory_hints(message)


def test_llama_cpp_load_failure_keeps_memory_diagnostics() -> None:
    """A llama.cpp load failure keeps the existing memory-oriented message."""
    error = RuntimeError("failed to allocate model buffer")

    def _loader():
        llama_utils._log_capture.append(
            "using device CUDA0 (NVIDIA GeForce RTX 4060) - 0 MiB free"
        )
        raise error

    with pytest.raises(RuntimeError) as excinfo:
        load_llama_or_raise(
            _loader,
            model_label=_LABEL,
            model_path=_PATH,
            device="CUDA0",
            context_window=2048,
        )

    message = str(excinfo.value)
    assert "0 MiB free on CUDA0" in message
    assert llama_utils._LOAD_ERROR_HINT_GPU in message
    assert "failed to allocate model buffer" in message
    assert "Could not load GGUF model" in message


def test_build_llama_load_error_unchanged_for_cpu() -> None:
    """The CPU memory hint is still used for non-download load failures."""
    error = ValueError("bad n_ctx")
    message = str(build_llama_load_error(_LABEL, _PATH, None, 512, error))

    assert llama_utils._LOAD_ERROR_HINT_CPU in message
    assert "0 MiB free" not in message
