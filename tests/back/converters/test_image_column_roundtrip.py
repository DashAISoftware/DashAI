"""Verify that DashAIImage columns survive the pandas round trip converters use."""

import io

import numpy as np
import pandas as pd
import pyarrow as pa
import pytest
from PIL import Image

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Float


def _png_bytes(color, size=(8, 8)):
    """Return the PNG encoding of a solid colour image.

    Parameters
    ----------
    color : tuple of int
        RGB colour of the generated image.
    size : tuple of int, optional
        Width and height in pixels. Defaults to ``(8, 8)``.

    Returns
    -------
    bytes
        PNG encoded image data.
    """
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def _frame():
    """Build a two row frame with one image column and one float column."""
    return pd.DataFrame(
        {
            "image": [
                {"bytes": _png_bytes((255, 0, 0)), "path": "red.png"},
                {"bytes": _png_bytes((0, 255, 0)), "path": "green.png"},
            ],
            "value": [1.5, 2.5],
        }
    )


def test_image_column_survives_to_dashai_dataset():
    dataset = to_dashai_dataset(
        _frame(), types={"image": DashAIImage(), "value": Float(pa.float64())}
    )

    assert isinstance(dataset.types["image"], DashAIImage)
    assert len(dataset) == 2

    # Verify against the real Arrow schema (Finding 1 fix)
    assert dataset.arrow_table.schema.field("image").type == DashAIImage.pa_type

    # Check both rows' pixel content and path field (Finding 2 fix)
    expected_colors = [(255, 0, 0), (0, 255, 0)]
    expected_paths = ["red.png", "green.png"]

    for row_idx in range(2):
        image = dataset[row_idx]["image"]
        assert isinstance(image, DashAIImage)
        assert image.to_pil().size == (8, 8)

        # Verify pixel content matches what went in
        pixel_array = np.array(image.to_pil())
        expected_color = expected_colors[row_idx]
        # Check a pixel from the solid-colour image
        assert tuple(pixel_array[0, 0, :3]) == expected_color

        # Verify path field survived
        assert image.path == expected_paths[row_idx]


def test_image_column_survives_to_pandas_and_back():
    dataset = to_dashai_dataset(
        _frame(), types={"image": DashAIImage(), "value": Float(pa.float64())}
    )

    frame = dataset.to_pandas()
    rebuilt = to_dashai_dataset(
        frame, types={"image": DashAIImage(), "value": Float(pa.float64())}
    )

    assert isinstance(rebuilt.types["image"], DashAIImage)

    # Verify against the real Arrow schema (Finding 1 fix)
    assert rebuilt.arrow_table.schema.field("image").type == DashAIImage.pa_type

    # Check both rows' pixel content and path field (Finding 2 fix)
    expected_colors = [(255, 0, 0), (0, 255, 0)]
    expected_paths = ["red.png", "green.png"]

    for row_idx in range(2):
        image = rebuilt[row_idx]["image"]
        assert isinstance(image, DashAIImage)
        assert image.to_pil().size == (8, 8)

        # Verify pixel content matches what went in
        pixel_array = np.array(image.to_pil())
        expected_color = expected_colors[row_idx]
        # Check a pixel from the solid-colour image
        assert tuple(pixel_array[0, 0, :3]) == expected_color

        # Verify path field survived
        assert image.path == expected_paths[row_idx]


@pytest.mark.xfail(
    strict=True,
    reason=(
        "to_dashai_dataset does not preserve dashai_types metadata through "
        "Dataset.from_pandas, so an image column loses its type when no "
        "explicit types argument is given. Converters that rebuild a dataset "
        "must pass types= explicitly. This test will start failing, and should "
        "then be un-marked, if metadata round-tripping is ever fixed."
    ),
)
def test_image_column_survives_without_explicit_types():
    """Test the metadata path that most converters actually use (Finding 3).

    Most real converters call to_dashai_dataset(x_new) without explicit types,
    routing through get_types_from_arrow_metadata instead of the explicit types path.
    """
    dataset = to_dashai_dataset(
        _frame(), types={"image": DashAIImage(), "value": Float(pa.float64())}
    )

    frame = dataset.to_pandas()
    # Rebuild WITHOUT explicit types argument
    rebuilt = to_dashai_dataset(frame)

    # Verify the image type was inferred from metadata
    assert isinstance(rebuilt.types["image"], DashAIImage)

    # Verify against the real Arrow schema
    assert rebuilt.arrow_table.schema.field("image").type == DashAIImage.pa_type

    # Check both rows' pixel content and path field
    expected_colors = [(255, 0, 0), (0, 255, 0)]
    expected_paths = ["red.png", "green.png"]

    for row_idx in range(2):
        image = rebuilt[row_idx]["image"]
        assert isinstance(image, DashAIImage)
        assert image.to_pil().size == (8, 8)

        # Verify pixel content matches what went in
        pixel_array = np.array(image.to_pil())
        expected_color = expected_colors[row_idx]
        # Check a pixel from the solid-colour image
        assert tuple(pixel_array[0, 0, :3]) == expected_color

        # Verify path field survived
        assert image.path == expected_paths[row_idx]
