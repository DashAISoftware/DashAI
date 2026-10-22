import contextlib
import ctypes
import logging
import os
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

from packaging.version import Version

logger = logging.getLogger(__name__)

try:
    import llama_cpp
except ImportError:
    llama_cpp = None


# llama_log_callback signature: void (*)(ggml_log_level level,
# const char * text, void * user_data)
_LOG_CB_T = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p)

_log_capture: list[str] = []

#: Maximum number of captured llama.cpp log lines kept in memory.
_LOG_CAPTURE_MAX_LINES = 2000

#: Maximum number of log lines included in a load error.
_LOG_TAIL_MAX_LINES = 12

#: Maximum number of characters of the captured llama.cpp log kept in errors.
_LOG_TAIL_MAX_CHARS = 800

#: Matches captured lines worth surfacing in a load error.
_LOG_SIGNAL_RE = re.compile(
    r"error|fail|free|alloc|cuda|device|invalid|out of memory",
    re.IGNORECASE,
)

#: Label used when no device was requested.
_DEFAULT_DEVICE_LABEL = "CPU"

#: Actionable troubleshooting hint appended to GPU GGUF load failures.
_LOAD_ERROR_HINT_GPU = (
    "Another GGUF model may already be occupying the GPU. Try running this "
    "model on CPU, reducing its context_window, or choosing a smaller "
    "checkpoint. If the file was just downloaded, verify the download finished."
)

#: Actionable troubleshooting hint appended to CPU GGUF load failures.
_LOAD_ERROR_HINT_CPU = (
    "The model may not fit in available system memory. Try reducing its "
    "context_window or choosing a smaller checkpoint. If the file was just "
    "downloaded, verify the download finished."
)

_LOAD_ERROR_HEADER = "Could not load GGUF model '{model_label}' from {model_path}."
_LOAD_ERROR_DEVICE = "device: {device}"
_LOAD_ERROR_CONTEXT_WINDOW = "context_window: {context_window}"
_LOAD_ERROR_ORIGINAL = "llama.cpp: {original}"
_LOAD_ERROR_LOG_HEADER = "llama.cpp log:"

#: Module roots whose exceptions mean the file could not be downloaded.
_DOWNLOAD_ERROR_MODULES = frozenset({"huggingface_hub", "requests", "urllib3", "httpx"})

#: Exception class names that indicate a download or repository failure.
_DOWNLOAD_ERROR_NAMES = frozenset(
    {
        "HfHubHTTPError",
        "LocalEntryNotFoundError",
        "RepositoryNotFoundError",
        "EntryNotFoundError",
        "ConnectionError",
    }
)

_DOWNLOAD_ERROR_HEADER = (
    "Could not download GGUF model '{model_label}' from {model_path}."
)
_DOWNLOAD_ERROR_ORIGINAL = "download: {original}"
_DOWNLOAD_ERROR_HINT = (
    "Check that the repository name and file path are correct and that the "
    "network is reachable, then retry. If the download was interrupted, remove "
    "the partial files and download it again, making sure the download finishes."
)

_FILE_ERROR_HEADER = "Could not read GGUF model file '{model_label}' from {model_path}."
_FILE_ERROR_ORIGINAL = "file: {original}"
_FILE_ERROR_HINT = (
    "The model file is missing, unreadable or incomplete. Re-download the "
    "checkpoint and try again."
)

#: Sentence used when llama.cpp reports free GPU memory.
_GPU_FREE_TEMPLATE = "llama.cpp reported {free} MiB free on {device} ({name})."

#: Matches llama.cpp lines such as
#: ``using device CUDA0 (NVIDIA GeForce RTX 4060) (...) - 0 MiB free``.
_GPU_FREE_RE = re.compile(
    r"using device\s+(\S+)\s+\(([^)]*)\)[^\n]*?-\s*(\d+)\s*MiB free"
)


def reset_llama_log() -> None:
    """Clear the captured llama.cpp log.

    Called immediately before each model load so diagnostics only describe the
    current attempt instead of reusing lines (for example a GPU free-memory
    report) captured by an earlier load.

    Returns
    -------
    None
    """
    _log_capture.clear()


def recent_llama_log(
    max_lines: int = _LOG_TAIL_MAX_LINES,
    max_chars: int = _LOG_TAIL_MAX_CHARS,
) -> str:
    """Return a bounded, console-safe excerpt of the captured llama.cpp log.

    Signal lines (errors, allocation, device and memory reports) are preferred
    over ordinary informational lines. When no line matches, the most recent
    lines are used instead.

    Parameters
    ----------
    max_lines : int, optional
        Maximum number of lines to include. Default 12.
    max_chars : int, optional
        Maximum number of trailing characters to return. Default 800.

    Returns
    -------
    str
        Newline-joined, stripped and ASCII-sanitized log lines, bounded by both
        ``max_lines`` and ``max_chars``. Empty when nothing was captured or
        either bound is not positive.
    """
    if max_lines <= 0 or max_chars <= 0:
        return ""
    signal_lines = [line for line in _log_capture if _LOG_SIGNAL_RE.search(line)]
    selected = signal_lines or list(_log_capture)
    sanitized = [
        line.strip().encode("ascii", "backslashreplace").decode("ascii")
        for line in selected[-max_lines:]
    ]
    return "\n".join(sanitized)[-max_chars:]


def reported_gpu_free_memory() -> Optional[str]:
    """Return a sentence describing the last reported GPU free memory.

    Parses the most recent ``using device ... - <N> MiB free`` line emitted by
    ``llama_prepare_model_devices`` during the current model load (guaranteed
    by :func:`reset_llama_log`).

    Returns
    -------
    str or None
        A short sentence with the device and reported free memory, or ``None``
        when llama.cpp did not report a GPU free-memory line.
    """
    matches = _GPU_FREE_RE.findall("".join(_log_capture))
    if not matches:
        return None
    device, name, free = matches[-1]
    return _GPU_FREE_TEMPLATE.format(free=free, device=device, name=name)


def _iter_exception_chain(error: BaseException) -> Iterator[BaseException]:
    """Yield ``error`` and its causes/contexts, stopping on cycles.

    Parameters
    ----------
    error : BaseException
        Exception whose chain should be walked.

    Yields
    ------
    BaseException
        The exception itself followed by each ``__cause__`` or ``__context__``
        until the chain ends or a previously seen exception is reached.
    """
    seen: set[int] = set()
    current: Optional[BaseException] = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def is_download_error(error: Exception) -> bool:
    """Report whether an exception came from a download or network layer.

    HuggingFace Hub and HTTP client exceptions commonly subclass ``OSError``
    (``requests.RequestException`` does), so an ``OSError`` alone cannot tell a
    failed download apart from an unreadable local file. The module root of the
    exception class and its class names are what distinguish the two.

    The whole exception chain is inspected, because a download failure can be
    re-raised as another exception. In particular, ``HfFileSystem.ls`` converts
    ``RepositoryNotFoundError`` into a builtins ``FileNotFoundError`` and
    ``EntryNotFoundError`` does not necessarily subclass ``OSError``.

    Parameters
    ----------
    error : Exception
        Exception raised while loading a model.

    Returns
    -------
    bool
        ``True`` when the exception, or any exception in its cause/context
        chain, originates in ``huggingface_hub``, ``requests``, ``urllib3`` or
        ``httpx``, or has a known download/repository class name. A
        ``FileNotFoundError`` that wraps such an error is a download failure,
        not a local file problem.
    """
    for exc in _iter_exception_chain(error):
        module_root = (type(exc).__module__ or "").split(".", 1)[0]
        if module_root in _DOWNLOAD_ERROR_MODULES:
            return True
        class_names = {cls.__name__ for cls in type(exc).__mro__}
        if class_names & _DOWNLOAD_ERROR_NAMES:
            return True
    return False


def build_download_error(
    model_label: str,
    model_path: str,
    original: Exception,
) -> RuntimeError:
    """Build an actionable error for a failed model download.

    Download and network failures are deliberately kept apart from memory
    exhaustion: they carry no GPU free-memory report and no CPU/GPU memory
    hint, because freeing memory would not fix them.

    Parameters
    ----------
    model_label : str
        Human-readable model or component name.
    model_path : str
        GGUF file path or HuggingFace repo/filename reference being loaded.
    original : Exception
        The download/network exception.

    Returns
    -------
    RuntimeError
        Error naming the model, the reference, the original error and a hint to
        check the repository name/network and the download.
    """
    return RuntimeError(
        "\n".join(
            [
                _DOWNLOAD_ERROR_HEADER.format(
                    model_label=model_label, model_path=model_path
                ),
                _DOWNLOAD_ERROR_ORIGINAL.format(original=original),
                _DOWNLOAD_ERROR_HINT,
            ]
        )
    )


def build_file_error(
    model_label: str,
    model_path: str,
    original: Exception,
) -> RuntimeError:
    """Build an actionable error for an unreadable local model file.

    Parameters
    ----------
    model_label : str
        Human-readable model or component name.
    model_path : str
        Local GGUF file path that could not be read.
    original : Exception
        The ``OSError`` raised while reading the file.

    Returns
    -------
    RuntimeError
        Error naming the model and path and stating that the file is missing,
        unreadable or incomplete. No memory hint is included.
    """
    return RuntimeError(
        "\n".join(
            [
                _FILE_ERROR_HEADER.format(
                    model_label=model_label, model_path=model_path
                ),
                _FILE_ERROR_ORIGINAL.format(original=original),
                _FILE_ERROR_HINT,
            ]
        )
    )


def build_llama_load_error(
    model_label: str,
    model_path: str,
    device: Optional[str],
    context_window: int,
    original: Exception,
) -> RuntimeError:
    """Build an actionable error for a failed GGUF model load.

    GPU loads report any captured free-memory line and suggest freeing the GPU,
    while CPU loads report a system-memory hint and never surface GPU data.

    Parameters
    ----------
    model_label : str
        Human-readable model or component name.
    model_path : str
        GGUF file path or HuggingFace repo/filename reference being loaded.
    device : str or None
        Device label requested from the schema; ``None`` means CPU.
    context_window : int
        Requested context window (``n_ctx``) for the failed load.
    original : Exception
        The exception raised by llama.cpp / llama-cpp-python.

    Returns
    -------
    RuntimeError
        Error carrying the model, device, context window, the device-specific
        troubleshooting hint, and the sanitized log excerpt.
    """
    is_gpu = device is not None and device != _DEFAULT_DEVICE_LABEL
    lines = [
        _LOAD_ERROR_HEADER.format(model_label=model_label, model_path=model_path),
        _LOAD_ERROR_DEVICE.format(device=device or _DEFAULT_DEVICE_LABEL),
        _LOAD_ERROR_CONTEXT_WINDOW.format(context_window=context_window),
    ]
    if is_gpu:
        gpu_free = reported_gpu_free_memory()
        if gpu_free:
            lines.append(gpu_free)
        lines.append(_LOAD_ERROR_HINT_GPU)
    else:
        lines.append(_LOAD_ERROR_HINT_CPU)
    lines.append(_LOAD_ERROR_ORIGINAL.format(original=original))
    log_tail = recent_llama_log()
    if log_tail:
        lines.append(_LOAD_ERROR_LOG_HEADER)
        lines.append(log_tail)
    return RuntimeError("\n".join(lines))


def load_llama_or_raise(
    loader: Callable[[], Any],
    *,
    model_label: str,
    model_path: str,
    device: Optional[str],
    context_window: int,
) -> Any:
    """Load a llama.cpp model, converting load failures into RuntimeError.

    The captured log is reset immediately before invoking ``loader`` so the
    diagnostics of one attempt never leak into another. Failures are classified
    before a message is built: download/network errors and unreadable local
    files get their own file-oriented message, and only genuine llama.cpp load
    failures are reported with the memory hints. Unexpected exceptions
    (programming errors, missing imports) propagate unchanged so they are not
    misdiagnosed as GPU exhaustion.

    Parameters
    ----------
    loader : Callable[[], Any]
        Zero-argument callable performing the actual llama.cpp load.
    model_label : str
        Human-readable model or component name.
    model_path : str
        GGUF file path or HuggingFace repo/filename reference being loaded.
    device : str or None
        Device label requested from the schema; ``None`` means CPU.
    context_window : int
        Requested context window (``n_ctx``) for the load.

    Returns
    -------
    Any
        Whatever ``loader`` returns on success.

    Raises
    ------
    RuntimeError
        If ``loader`` raises a download/network error, an ``OSError``, a
        ``ValueError`` or a ``RuntimeError``. Download/network errors and local
        file errors get a file-oriented message; other load failures get the
        memory-oriented diagnostics. Any other exception (programming errors)
        propagates unchanged. The original exception is chained as
        ``__cause__``.
    """
    reset_llama_log()
    try:
        return loader()
    except Exception as err:
        if is_download_error(err):
            raise build_download_error(
                model_label=model_label,
                model_path=model_path,
                original=err,
            ) from err
        if isinstance(err, OSError):
            raise build_file_error(
                model_label=model_label,
                model_path=model_path,
                original=err,
            ) from err
        if isinstance(err, (ValueError, RuntimeError)):
            raise build_llama_load_error(
                model_label=model_label,
                model_path=model_path,
                device=device,
                context_window=context_window,
                original=err,
            ) from err
        raise


@_LOG_CB_T
def _capturing_log_cb(level, msg, user_data):
    if not msg:
        return
    try:
        text = msg.decode("utf-8", errors="ignore")
    except Exception:
        return
    _log_capture.append(text)
    if len(_log_capture) > _LOG_CAPTURE_MAX_LINES:
        del _log_capture[:-_LOG_CAPTURE_MAX_LINES]
    logger.debug("llama: %s", text.rstrip("\n"))


def _lib_dir() -> Path:
    return Path(os.path.dirname(llama_cpp.__file__)) / "lib"


@lru_cache(maxsize=1)
def _load_llama_lib():
    """Load llama.dll and install our own log callback so CUDA init output
    can be captured in _log_capture instead of printed to the real stderr."""
    if llama_cpp is None:
        return None
    lib = llama_cpp.llama_cpp.load_shared_library("llama", _lib_dir())
    if hasattr(lib, "llama_log_set"):
        try:
            lib.llama_log_set.argtypes = [_LOG_CB_T, ctypes.c_void_p]
            lib.llama_log_set.restype = None
            lib.llama_log_set(_capturing_log_cb, None)
        except Exception as e:
            logger.debug("llama_log_set failed: %s", e)
    return lib


@lru_cache(maxsize=1)
def _all_ggml_libs() -> tuple:
    """Load every shared lib in llama_cpp/lib/ so backend symbols are reachable."""
    if llama_cpp is None:
        return ()
    if sys.platform.startswith("win"):
        patterns = ("*.dll",)
    elif sys.platform == "darwin":
        patterns = ("*.dylib",)
    else:
        patterns = ("*.so", "*.so.*")

    base = _lib_dir()
    if not base.is_dir():
        return ()

    libs = []
    seen = set()
    for pat in patterns:
        for f in base.glob(pat):
            if f.name in seen:
                continue
            seen.add(f.name)
            try:
                libs.append(ctypes.CDLL(str(f)))
            except OSError as e:
                logger.debug("skip lib %s: %s", f.name, e)
    return tuple(libs)


def _find_symbol(libs, name):
    for lib in libs:
        if hasattr(lib, name):
            return lib
    return None


def _parse_compute_caps(log: str) -> dict[int, str]:
    """Extract `Device N: ..., compute capability X.Y` from captured log."""
    pattern = r"Device\s*(\d+):\s*[^,]+,\s*compute capability\s*([\d.]+)"
    return {int(m.group(1)): m.group(2) for m in re.finditer(pattern, log)}


def _enum_via_cuda_api(libs, caps: dict[int, str]) -> list[str]:
    lib = _find_symbol(libs, "ggml_backend_cuda_get_device_count")
    if lib is None or not hasattr(lib, "ggml_backend_cuda_get_device_description"):
        return []

    lib.ggml_backend_cuda_get_device_count.restype = ctypes.c_int
    lib.ggml_backend_cuda_get_device_description.restype = None
    lib.ggml_backend_cuda_get_device_description.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_size_t,
    ]

    count = lib.ggml_backend_cuda_get_device_count()
    devices = []
    for i in range(count):
        buf = ctypes.create_string_buffer(256)
        lib.ggml_backend_cuda_get_device_description(i, buf, 256)
        name = buf.value.decode("utf-8", errors="ignore").strip() or "CUDA device"
        cap = caps.get(i)
        if cap:
            devices.append(f"GPU {i}: {name} - Compute Capability {cap}")
        else:
            devices.append(f"GPU {i}: {name}")
    return devices


def _enum_via_ggml_dev_api(libs, caps: dict[int, str]) -> list[str]:
    lib = _find_symbol(libs, "ggml_backend_dev_count")
    required = (
        "ggml_backend_dev_get",
        "ggml_backend_dev_type",
        "ggml_backend_dev_description",
        "ggml_backend_dev_name",
    )
    if lib is None or not all(hasattr(lib, s) for s in required):
        return []

    lib.ggml_backend_dev_count.restype = ctypes.c_size_t
    lib.ggml_backend_dev_get.restype = ctypes.c_void_p
    lib.ggml_backend_dev_get.argtypes = [ctypes.c_size_t]
    lib.ggml_backend_dev_type.restype = ctypes.c_int
    lib.ggml_backend_dev_type.argtypes = [ctypes.c_void_p]
    lib.ggml_backend_dev_description.restype = ctypes.c_char_p
    lib.ggml_backend_dev_description.argtypes = [ctypes.c_void_p]
    lib.ggml_backend_dev_name.restype = ctypes.c_char_p
    lib.ggml_backend_dev_name.argtypes = [ctypes.c_void_p]

    # GGML_BACKEND_DEVICE_TYPE_CPU = 0, GPU = 1, ACCEL = 2
    count = lib.ggml_backend_dev_count()
    devices = []
    gpu_idx = 0
    for i in range(count):
        dev = lib.ggml_backend_dev_get(i)
        if not dev:
            continue
        if lib.ggml_backend_dev_type(dev) == 0:
            continue
        desc = lib.ggml_backend_dev_description(dev) or lib.ggml_backend_dev_name(dev)
        name = desc.decode("utf-8", errors="ignore").strip() if desc else "GPU"
        cap = caps.get(gpu_idx)
        if cap:
            devices.append(f"GPU {gpu_idx}: {name} - Compute Capability {cap}")
        else:
            devices.append(f"GPU {gpu_idx}: {name}")
        gpu_idx += 1
    return devices


@lru_cache(maxsize=1)
def get_llama_gpu_devices_formatted() -> list[str]:
    """GPU device strings visible to llama_cpp (not torch).
    Example: ["GPU 0: NVIDIA GeForce RTX 5080 - Compute Capability 12.0"]
    """
    if llama_cpp is None:
        return []

    try:
        _load_llama_lib()  # installs log callback
        libs = _all_ggml_libs()
        if not libs:
            return []

        # Trigger CUDA init so compute-capability line lands in _log_capture
        cuda_lib = _find_symbol(libs, "ggml_backend_cuda_get_device_count")
        if cuda_lib is not None:
            cuda_lib.ggml_backend_cuda_get_device_count.restype = ctypes.c_int
            with contextlib.suppress(Exception):
                cuda_lib.ggml_backend_cuda_get_device_count()

        caps = _parse_compute_caps("".join(_log_capture))
        devices = _enum_via_cuda_api(libs, caps)
        if devices:
            return devices
        return _enum_via_ggml_dev_api(libs, caps)
    except Exception as e:
        logger.warning("Error enumerating llama GPUs: %s", e)
        return []


def is_gpu_available_for_llama_cpp() -> bool:
    """Check whether the installed llama-cpp-python was compiled with GPU support.

    Dispatches to a version-specific helper based on the ``llama_cpp`` package
    version, because the internal API changed between 0.2.x and 0.3.x.

    Returns
    -------
    bool
        ``True`` if GPU offloading is available; ``False`` if ``llama-cpp-python``
        is not installed or if the check raises an unexpected exception.
    """
    if llama_cpp is None:
        return False
    try:
        if Version(llama_cpp.__version__) > Version("0.3.0"):
            return __is_gpu_available_for_llama_cpp_v03()
        else:
            return __is_gpu_available_for_llama_cpp_v02()
    except Exception as e:
        logger.warning(
            "Error checking GPU availability for llama_cpp. Will use CPU only.\n"
            f"Details: {e}"
        )
        return False


def __is_gpu_available_for_llama_cpp_v03() -> bool:
    """Check GPU availability using the llama.cpp v0.3 shared-library API.

    Loads the ``llama`` shared library from the llama_cpp package directory and
    calls ``llama_supports_gpu_offload`` to determine whether the build was
    compiled with GPU support.

    Returns
    -------
    bool
        ``True`` if ``llama_supports_gpu_offload()`` returns a truthy value,
        ``False`` otherwise.
    """
    lib = _load_llama_lib()
    return bool(lib.llama_supports_gpu_offload())


def __is_gpu_available_for_llama_cpp_v02() -> bool:
    """Check GPU availability using the llama.cpp v0.2 shared-library API.

    Loads the ``llama`` shared library via the legacy ``_load_shared_library``
    helper and inspects it for the ``ggml_init_cublas`` symbol, which is only
    present in CUDA-enabled builds.

    Returns
    -------
    bool
        ``True`` if the ``ggml_init_cublas`` attribute is found in the loaded
        library, ``False`` otherwise.
    """
    lib = llama_cpp.llama_cpp._load_shared_library("llama")
    return hasattr(lib, "ggml_init_cublas")
