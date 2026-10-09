"""Turn a segmentation mask and its source image into a masked image."""

import io
from typing import TYPE_CHECKING

from DashAI.back.segmenters.base_segmenter import SegmentInstance

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

BACKGROUND_FILLS = ("black", "white", "blur")

_SOLID_FILLS = {"black": (0, 0, 0), "white": (255, 255, 255)}

_BLUR_RADIUS = 8


def render_segment(
    image: "PILImage",
    instance: SegmentInstance,
    crop_to_bbox: bool,
    background_fill: str,
) -> bytes:
    """Render one detected object as a standalone PNG image.

    Parameters
    ----------
    image : PIL.Image.Image
        Source image the instance was detected in.
    instance : SegmentInstance
        The detected object, whose mask must match the size of ``image``.
    crop_to_bbox : bool
        When true, the result is cropped to the instance bounding box.
    background_fill : str
        One of ``"black"``, ``"white"``, or ``"blur"``, applied to every pixel
        outside the mask.

    Returns
    -------
    bytes
        PNG encoded image data.

    Raises
    ------
    ValueError
        If ``background_fill`` is not a recognised value, if the mask dtype
        is not boolean, or if the mask shape does not match the image size.
    """
    import numpy as np
    from PIL import Image, ImageFilter

    if background_fill not in BACKGROUND_FILLS:
        raise ValueError(
            f"Unknown background fill '{background_fill}'. "
            f"Expected one of {list(BACKGROUND_FILLS)}."
        )

    # A non-boolean mask (e.g. float scores from a segmenter that forgot to
    # binarise) would silently corrupt the composite below: multiplying by
    # 255 would not yield a clean 0/255 stencil, and any area-based
    # threshold computed upstream from the same mask would sum probabilities
    # instead of counting pixels. Catch it here, beside the shape check, so
    # no future adapter can reintroduce this.
    if instance.mask.dtype != np.bool_:
        raise ValueError(
            f"Mask dtype {instance.mask.dtype} is not boolean. Segmenters "
            "must produce SegmentInstance.mask as a boolean array."
        )

    rgb = image.convert("RGB")
    width, height = rgb.size
    if instance.mask.shape != (height, width):
        raise ValueError(
            f"Mask shape {instance.mask.shape} does not match image size "
            f"{(height, width)}."
        )

    if background_fill == "blur":
        background = rgb.filter(ImageFilter.GaussianBlur(radius=_BLUR_RADIUS))
    else:
        background = Image.new("RGB", rgb.size, _SOLID_FILLS[background_fill])

    mask_image = Image.fromarray((instance.mask * 255).astype(np.uint8), mode="L")
    composed = Image.composite(rgb, background, mask_image)

    if crop_to_bbox:
        composed = composed.crop(instance.bbox)

    buffer = io.BytesIO()
    composed.save(buffer, format="PNG")
    return buffer.getvalue()


def render_binary_mask(instance: SegmentInstance) -> bytes:
    """Render an instance mask as a single channel PNG.

    Always full source image size, so the mask stays aligned with the
    original image even when the segment image is cropped to the bounding
    box.

    Parameters
    ----------
    instance : SegmentInstance
        The detected object.

    Returns
    -------
    bytes
        PNG encoded single channel image, 255 inside the object and 0
        outside.
    """
    import numpy as np
    from PIL import Image

    image = Image.fromarray((instance.mask * 255).astype(np.uint8), mode="L")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
