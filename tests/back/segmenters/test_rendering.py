"""Tests for turning a mask into a masked image."""

import io

import numpy as np
from PIL import Image

from DashAI.back.segmenters.base_segmenter import SegmentInstance
from DashAI.back.segmenters.rendering import render_segment


def _instance():
    """A 4 x 4 mask covering the middle 2 x 2 block of an 8 x 8 image."""
    mask = np.zeros((8, 8), dtype=bool)
    mask[3:5, 3:5] = True
    return SegmentInstance(mask=mask, score=0.9, bbox=(3, 3, 5, 5))


def _source():
    return Image.new("RGB", (8, 8), (255, 0, 0))


def _source_with_variation():
    """8x8 red source with white 2x2 block in top-left corner.

    The colour variation is essential for the blur test to detect
    bugs where blurring happens after composite instead of before.
    With uniform colour, blur is a no-op and cannot catch the bug.
    """
    img = Image.new("RGB", (8, 8), (255, 0, 0))
    pixels = img.load()
    for x in range(2):
        for y in range(2):
            pixels[x, y] = (255, 255, 255)
    return img


def _decode(data):
    return Image.open(io.BytesIO(data)).convert("RGB")


def test_crop_to_bbox_returns_bbox_sized_image():
    data = render_segment(
        _source(), _instance(), crop_to_bbox=True, background_fill="black"
    )

    assert _decode(data).size == (2, 2)


def test_without_crop_keeps_original_size():
    data = render_segment(
        _source(), _instance(), crop_to_bbox=False, background_fill="black"
    )

    assert _decode(data).size == (8, 8)


def test_black_fill_blanks_pixels_outside_the_mask():
    image = _decode(
        render_segment(
            _source(), _instance(), crop_to_bbox=False, background_fill="black"
        )
    )

    assert image.getpixel((3, 3)) == (255, 0, 0)
    assert image.getpixel((0, 0)) == (0, 0, 0)


def test_white_fill_uses_white_outside_the_mask():
    image = _decode(
        render_segment(
            _source(), _instance(), crop_to_bbox=False, background_fill="white"
        )
    )

    assert image.getpixel((0, 0)) == (255, 255, 255)


def test_blur_fill_keeps_masked_pixels_exact():
    """Blur background preserves masked pixels; detects blur-after-composite bug.

    The source has spatial colour variation (white block in corner) so that
    if blurring occurs after composite instead of before, white bleeds into
    the background and this test fails. With uniform colour, this bug is
    undetectable.
    """
    image = _decode(
        render_segment(
            _source_with_variation(),
            _instance(),
            crop_to_bbox=False,
            background_fill="blur",
        )
    )

    # Pixel inside mask must be bit-exact to source (red), not blurred
    assert image.getpixel((4, 4)) == (255, 0, 0)
    # Background pixel near white block must have changed due to blur
    # At (2, 2), the red background was blurred with the nearby white block,
    # so it should not be pure red anymore
    assert image.getpixel((2, 2)) != (255, 0, 0)


def test_output_is_png():
    data = render_segment(
        _source(), _instance(), crop_to_bbox=True, background_fill="black"
    )

    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_non_square_image_guards_height_width_ordering():
    """Guards the mask shape check against transposed dimensions."""
    # 12 wide by 6 high image (width > height to catch transposition)
    image = Image.new("RGB", (12, 6), (255, 0, 0))

    # Mask of correct shape (6, 12) = (height, width)
    mask = np.zeros((6, 12), dtype=bool)
    mask[2:4, 8:10] = True  # Set a region at x=8-10 (outside height range)
    instance = SegmentInstance(mask=mask, score=0.9, bbox=(8, 2, 10, 4))

    data = render_segment(image, instance, crop_to_bbox=False, background_fill="black")
    result = _decode(data)

    # Output size should be (12, 6) - width first, height second
    assert result.size == (12, 6)
    # Pixel inside mask keeps source color
    assert result.getpixel((9, 3)) == (255, 0, 0)
    # Pixel outside mask gets black fill
    assert result.getpixel((0, 0)) == (0, 0, 0)


def test_non_square_crop_guards_height_width_ordering():
    """Guards bbox cropping respects height and width ordering."""
    # 12 wide by 6 high image
    image = Image.new("RGB", (12, 6), (255, 0, 0))

    # Mask of correct shape (6, 12) with region at x=8-10
    mask = np.zeros((6, 12), dtype=bool)
    mask[2:4, 8:10] = True
    instance = SegmentInstance(mask=mask, score=0.9, bbox=(8, 2, 10, 4))

    data = render_segment(image, instance, crop_to_bbox=True, background_fill="black")
    result = _decode(data)

    # Cropped size should be (width, height) = (10-8, 4-2) = (2, 2)
    assert result.size == (2, 2)


def test_transposed_mask_shape_raises_error():
    """Guards that transposed mask shape is rejected."""
    # 12 wide by 6 high image
    image = Image.new("RGB", (12, 6), (255, 0, 0))

    # Mask with TRANSPOSED shape (12, 6) instead of correct (6, 12)
    mask = np.zeros((12, 6), dtype=bool)
    mask[2:4, 8:10] = True
    instance = SegmentInstance(mask=mask, score=0.9, bbox=(8, 2, 10, 4))

    # Should raise ValueError about shape mismatch
    import pytest

    with pytest.raises(ValueError, match="Mask shape .* does not match image size"):
        render_segment(image, instance, crop_to_bbox=False, background_fill="black")
