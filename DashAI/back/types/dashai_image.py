"""DashAI Image type."""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, Optional

from DashAI.back.types.dashai_data_type import DashAIDataType

if TYPE_CHECKING:
    import numpy as np
    import pyarrow as pa
    from PIL import Image as PILImage


class _LazyPAType:
    _value = None

    def __get__(self, _obj, _objtype=None):
        if _LazyPAType._value is None:
            import pyarrow as pa

            _LazyPAType._value = pa.struct({"bytes": pa.binary(), "path": pa.string()})
        return _LazyPAType._value


@dataclass
class DashAIImage(DashAIDataType):
    """Image type for DashAI datasets.

    Serves dual roles:
    - Column type descriptor: ``DashAIImage()`` (bytes/path are None).
    - Data instance returned by ``DashAIDataset.__getitem__``:
      ``DashAIImage(bytes=b"...", path="cat.jpg")``.
    """

    pa_type: ClassVar["pa.DataType"] = _LazyPAType()
    DISPLAY_NAME: ClassVar[str] = "Image"

    dtype: str = "struct"
    bytes: Optional[bytes] = field(default=None, repr=False)
    path: Optional[str] = field(default=None, repr=False)

    def to_string(self) -> dict:
        return {"type": self.display_name(), "dtype": self.dtype}

    def to_pil(self) -> "PILImage":
        """Decode image bytes to a PIL Image."""
        from PIL import Image as PILImage

        if self.bytes is None:
            raise ValueError("No image bytes available.")
        return PILImage.open(io.BytesIO(self.bytes))

    def to_numpy(self) -> "np.ndarray":
        """Decode image bytes to a NumPy array (H x W x C, uint8)."""
        import numpy as np

        return np.array(self.to_pil())
