"""GPU placement for diffusers pipelines.

Every diffusion model used to call ``pipeline.to(device)``, which needs the
whole pipeline to fit in VRAM at once. Several shipped checkpoints do not fit
on a 12 GB card (PixArt-Sigma's T5-XXL encoder alone is ~9.5 GB in fp16), and
a failed ``.to()`` leaves the partial copy stranded in the persistent job
worker. ``place_pipeline`` picks how much of the pipeline lives on the GPU, and
``GpuMemoryModeField`` lets the user override that choice.
"""

import logging
from typing import Any, Literal

from DashAI.back.core.schema_fields import enum_field, schema_field
from DashAI.back.core.utils import MultilingualString

log = logging.getLogger(__name__)

GpuMemoryMode = Literal["auto", "full", "model", "sequential"]
GPU_MEMORY_MODES: list[str] = ["auto", "full", "model", "sequential"]

# Room left for activations, the CUDA context and the allocator's slack on top
# of the weights themselves. Activations grow with resolution and batch size,
# so this errs on the side of offloading.
_HEADROOM_BYTES = 2 * 1024**3
_HEADROOM_FACTOR = 1.1

GpuMemoryModeField = schema_field(
    enum_field(enum=GPU_MEMORY_MODES),
    placeholder="auto",
    description=MultilingualString(
        en=(
            "How much of the model is kept on the GPU. 'auto' measures free "
            "VRAM when the model loads and picks the fastest option that fits. "
            "'full' keeps everything on the GPU (fastest, most VRAM). 'model' "
            "moves one component (text encoder, denoiser, VAE) to the GPU at a "
            "time. 'sequential' streams the weights layer by layer: slowest, "
            "but runs large models on small GPUs. Ignored on CPU."
        ),
        es=(
            "Cuánto del modelo se mantiene en la GPU. 'auto' mide la VRAM libre "
            "al cargar el modelo y elige la opción más rápida que cabe. 'full' "
            "deja todo en la GPU (lo más rápido, usa más VRAM). 'model' sube a "
            "la GPU un componente a la vez (codificador de texto, denoiser, "
            "VAE). 'sequential' sube los pesos capa por capa: lo más lento, "
            "pero permite modelos grandes en GPUs pequeñas. Se ignora en CPU."
        ),
        pt=(
            "Quanto do modelo é mantido na GPU. 'auto' mede a VRAM livre ao "
            "carregar o modelo e escolhe a opção mais rápida que cabe. 'full' "
            "mantém tudo na GPU (mais rápido, usa mais VRAM). 'model' envia "
            "um componente por vez para a GPU (codificador de texto, denoiser, "
            "VAE). 'sequential' transmite os pesos camada por camada: mais "
            "lento, mas roda modelos grandes em GPUs pequenas. Ignorado na CPU."
        ),
        de=(
            "Wie viel des Modells auf der GPU bleibt. 'auto' misst beim Laden "
            "den freien VRAM und wählt die schnellste Option, die passt. "
            "'full' hält alles auf der GPU (am schnellsten, meister VRAM). "
            "'model' lädt jeweils eine Komponente (Text-Encoder, Denoiser, "
            "VAE) auf die GPU. 'sequential' überträgt die Gewichte Schicht für "
            "Schicht: am langsamsten, aber große Modelle laufen auch auf "
            "kleinen GPUs. Wird auf der CPU ignoriert."
        ),
        zh=(
            "模型保留在 GPU 上的程度。'auto' 在加载模型时测量可用显存，"
            "并选择可容纳的最快方案。'full' 全部保留在 GPU 上（最快，显存占用最多）。"
            "'model' 每次仅将一个组件（文本编码器、去噪器、VAE）移至 GPU。"
            "'sequential' 逐层传输权重：最慢，但可在小显存 GPU 上运行大模型。"
            "在 CPU 上忽略此项。"
        ),
    ),
    alias=MultilingualString(
        en="GPU memory mode",
        es="Modo de memoria GPU",
        pt="Modo de memória da GPU",
        de="GPU-Speichermodus",
        zh="GPU 显存模式",
    ),
)


def _module_bytes(module: Any) -> int:
    """Return the bytes taken by a module's parameters and buffers."""
    tensors = list(module.parameters()) + list(module.buffers())
    return sum(t.numel() * t.element_size() for t in tensors)


def _choose_mode(pipeline: Any, gpu_id: int) -> str:
    """Pick the fastest placement whose weights fit in the free VRAM.

    Parameters
    ----------
    pipeline : diffusers.DiffusionPipeline
        The pipeline, still on the CPU.
    gpu_id : int
        Index of the target CUDA device.

    Returns
    -------
    str
        ``"full"``, ``"model"`` or ``"sequential"``.
    """
    import torch

    sizes = [
        _module_bytes(component)
        for component in pipeline.components.values()
        if isinstance(component, torch.nn.Module)
    ]
    free, _ = torch.cuda.mem_get_info(gpu_id)

    def fits(n_bytes: int) -> bool:
        return n_bytes * _HEADROOM_FACTOR + _HEADROOM_BYTES <= free

    if fits(sum(sizes)):
        mode = "full"
    elif fits(max(sizes, default=0)):
        mode = "model"
    else:
        mode = "sequential"
    log.info(
        "gpu_memory_mode=auto chose %r: pipeline %.1f GB, largest component "
        "%.1f GB, free VRAM %.1f GB",
        mode,
        sum(sizes) / 1e9,
        max(sizes, default=0) / 1e9,
        free / 1e9,
    )
    return mode


def place_pipeline(pipeline: Any, device: str, mode: str = "auto") -> Any:
    """Move a diffusers pipeline to ``device`` according to ``mode``.

    Parameters
    ----------
    pipeline : diffusers.DiffusionPipeline
        A freshly loaded pipeline, still on the CPU. Pass sub-models such as a
        ControlNet or a replacement VAE through ``from_pretrained`` rather than
        moving them yourself, so they are placed together with the rest.
    device : str
        ``"cpu"`` or ``"cuda:<index>"``.
    mode : str
        One of ``GPU_MEMORY_MODES``. Ignored on the CPU.

    Returns
    -------
    diffusers.DiffusionPipeline
        The same pipeline. Call it as usual: with offloading enabled, diffusers
        moves each piece to the GPU when it runs.
    """
    if not device.startswith("cuda"):
        return pipeline.to(device)

    gpu_id = int(device.split(":")[1]) if ":" in device else 0
    if mode == "auto":
        mode = _choose_mode(pipeline, gpu_id)

    if mode == "full":
        return pipeline.to(device)
    if mode == "model":
        pipeline.enable_model_cpu_offload(gpu_id=gpu_id)
        return pipeline
    if mode == "sequential":
        pipeline.enable_sequential_cpu_offload(gpu_id=gpu_id)
        return pipeline
    raise ValueError(
        f"Unknown gpu_memory_mode {mode!r}; expected one of {GPU_MEMORY_MODES}."
    )
