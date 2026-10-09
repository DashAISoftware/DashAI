import os
from pathlib import Path

import torch

from DashAI.back.models.hugging_face.llama_utils import (
    get_llama_gpu_devices_formatted,
    is_gpu_available_for_llama_cpp,
)


def resolve_temp_checkpoint_dir(temp_checkpoint_dir: str) -> Path:
    """Resolve a transformer's temp checkpoint dir to an absolute, writable path.

    Historically ``TEMP_CHECKPOINT_DIR`` was a path relative to the repository
    root (e.g. ``DashAI/back/user_models/temp_checkpoints_*``). That only works
    in development mode, where the current working directory is the repo root.
    In a packaged executable (PyInstaller/AppImage) the working directory is the
    read-only install location, so creating the directory fails with a
    permission/not-found error.

    To work in both cases we anchor the checkpoints under the DashAI local data
    directory (``DASHAI_LOCAL_PATH`` env var, falling back to ``~/.DashAI``) and
    keep only the final segment of the configured path as the folder name.

    Parameters
    ----------
    temp_checkpoint_dir : str
        The configured (possibly relative) checkpoint directory.

    Returns
    -------
    Path
        An absolute path under the DashAI local data directory.
    """
    local_path = os.environ.get("DASHAI_LOCAL_PATH")
    base = Path(local_path).expanduser() if local_path else Path.home() / ".DashAI"
    folder_name = Path(temp_checkpoint_dir).name or "temp_checkpoints"
    return base / "user_models" / folder_name


DEVICE_ENUM: list[str] = ["CPU"]
DEVICE_PLACEHOLDER: str = "CPU"
DEVICE_TO_IDX: dict[str, int] = {"CPU": -1}
GPU_OR_CPU: list[str] = ["CPU"]
GPU_OR_CPU_PLACEHOLDER: str = "CPU"

if torch.cuda.is_available():
    GPU_OR_CPU.insert(0, "GPU")
    GPU_OR_CPU_PLACEHOLDER = "GPU"
    cuda_devices = []
    for i in range(torch.cuda.device_count()):
        cuda_devices.append(
            f"GPU {i}: {torch.cuda.get_device_name(i)} - "
            f"Compute Capability {torch.cuda.get_device_capability(i)[0]}."
            f"{torch.cuda.get_device_capability(i)[1]}"
        )
    DEVICE_ENUM = cuda_devices + ["CPU"]
    DEVICE_PLACEHOLDER = DEVICE_ENUM[0]
    DEVICE_TO_IDX.update({name: i for i, name in enumerate(cuda_devices)})

LLAMA_DEVICE_ENUM: list[str] = ["CPU"]
LLAMA_DEVICE_PLACEHOLDER: str = "CPU"
LLAMA_DEVICE_TO_IDX: dict[str, int] = {"CPU": -1}
if is_gpu_available_for_llama_cpp():
    cuda_devices = get_llama_gpu_devices_formatted()
    LLAMA_DEVICE_ENUM = cuda_devices + ["CPU"]
    LLAMA_DEVICE_PLACEHOLDER = LLAMA_DEVICE_ENUM[0]
    LLAMA_DEVICE_TO_IDX.update({name: i for i, name in enumerate(cuda_devices)})
