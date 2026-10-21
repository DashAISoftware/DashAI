"""Shared pieces of tools that run one downloadable pretrained model."""

from typing import Any, Iterator, List, Optional, Sequence

from DashAI.back.core.schema_fields import enum_field, schema_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import HFPretrainedDownloadMixin
from DashAI.back.models.utils import DEVICE_ENUM, DEVICE_PLACEHOLDER, DEVICE_TO_IDX


def device_field() -> Any:
    """Return the schema field that picks the device a model runs on.

    Returns
    -------
    Any
        A ``device`` field over the available GPUs and the CPU.
    """
    return schema_field(
        enum_field(DEVICE_ENUM),
        DEVICE_PLACEHOLDER,
        description=MultilingualString(
            en="Device the model runs on. A GPU is much faster than the CPU.",
            es="Dispositivo en el que corre el modelo. Una GPU es mucho más "
            "rápida que la CPU.",
            pt="Dispositivo em que o modelo roda. Uma GPU é muito mais rápida "
            "que a CPU.",
            de="Gerät, auf dem das Modell läuft. Eine GPU ist viel schneller "
            "als die CPU.",
            zh="运行模型的设备。GPU 比 CPU 快得多。",
        ),
        alias=MultilingualString(
            en="Device",
            es="Dispositivo",
            pt="Dispositivo",
            de="Gerät",
            zh="设备",
        ),
    )


def torch_device(label: Optional[str]) -> str:
    """Turn a device label of :func:`device_field` into a torch device.

    Parameters
    ----------
    label : str, optional
        A label such as ``"CPU"`` or ``"GPU 0: ..."``; None means CPU.

    Returns
    -------
    str
        ``"cuda:<index>"`` or ``"cpu"``.
    """
    index = DEVICE_TO_IDX.get(label or "CPU", -1)
    return f"cuda:{index}" if index >= 0 else "cpu"


def batches(values: Sequence[Any], size: int) -> Iterator[List[Any]]:
    """Yield consecutive slices of at most ``size`` values.

    Parameters
    ----------
    values : Sequence[Any]
        The values to slice.
    size : int
        The largest slice.

    Yields
    ------
    List[Any]
        The next slice.
    """
    for start in range(0, len(values), size):
        yield list(values[start : start + size])


def open_image(value: Any) -> Any:
    """Decode a stored image value into an RGB PIL image.

    Parameters
    ----------
    value : dict or DashAIImage
        A ``{"bytes", "path"}`` value or an object with ``bytes``.

    Returns
    -------
    PIL.Image.Image
        The image in RGB mode.
    """
    import io

    from PIL import Image

    data = value["bytes"] if isinstance(value, dict) else value.bytes
    return Image.open(io.BytesIO(data)).convert("RGB")


class PretrainedTool(HFPretrainedDownloadMixin):
    """A component that runs one Hugging Face model, loaded on first use.

    Subclasses set ``MODEL_NAME`` and ``DOWNLOAD_SIZE_BYTES`` and implement
    :meth:`load_pretrained`. The model is read from the component's download
    folder when it was downloaded, or from the Hub otherwise.
    """

    def setup_device(self, label: Optional[str]) -> None:
        """Choose the device and forget any loaded model.

        Parameters
        ----------
        label : str, optional
            The ``device`` parameter.
        """
        self.device = torch_device(label)
        self._pretrained: Any = None

    def load_pretrained(self, source: str) -> Any:
        """Load the model and its processor.

        Parameters
        ----------
        source : str
            A local directory or a Hub repo id.

        Returns
        -------
        Any
            Whatever the tool needs to run, such as a ``(processor, model)``
            pair.
        """
        raise NotImplementedError

    def pretrained(self) -> Any:
        """Return the loaded model, loading it on first use.

        Returns
        -------
        Any
            The value :meth:`load_pretrained` returned.
        """
        if getattr(self, "_pretrained", None) is None:
            self._pretrained = self.load_pretrained(self._pretrained_source())
        return self._pretrained
