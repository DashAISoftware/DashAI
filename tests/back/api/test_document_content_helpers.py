"""Tests for the shared document content read helpers."""

import io
from pathlib import Path

import pytest
from fastapi.exceptions import HTTPException
from PIL import Image

from DashAI.back.api.document_content import (
    image_response,
    read_content_page,
    read_outline,
    require_content_type,
)
from DashAI.back.dataloaders.classes.dashai_document import (
    DashAIDocument,
    DocumentItem,
    save_document,
)
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Text


def _png_bytes() -> bytes:
    """Encode a tiny red PNG.

    Returns
    -------
    bytes
        The PNG file content.
    """
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture(name="document_dir")
def fixture_document_dir(tmp_path: Path) -> Path:
    """Save a title, an image and a paragraph over two pages.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory.

    Returns
    -------
    Path
        The saved document directory.
    """
    directory = tmp_path / "document"
    save_document(
        DashAIDocument.from_items(
            [
                DocumentItem(Text, "Annual\nreport", page=1, kind="title"),
                DocumentItem(
                    DashAIImage,
                    DashAIImage(bytes=_png_bytes(), path="figure.png"),
                    page=1,
                ),
                DocumentItem(Text, "Body text.", page=2),
            ]
        ),
        directory,
    )
    return directory


def test_content_page_interleaves_types_with_given_image_urls(document_dir):
    page = read_content_page(
        document_dir, "all", 0, 50, lambda position: f"/images/{position}"
    )

    assert page["content_type"] == "all"
    assert page["total"] == 3
    assert [
        (item["type"], item["position"], item["page"], item["kind"])
        for item in page["items"]
    ] == [
        ("Text", 0, 1, "title"),
        ("Image", 1, 1, "image"),
        ("Text", 2, 2, "paragraph"),
    ]
    assert page["items"][1]["url"] == "/images/1"
    assert "content" not in page["items"][1]
    assert page["items"][2]["attrs"] == {}


def test_content_page_filters_by_type_and_paginates(document_dir):
    page = read_content_page(document_dir, "Text", 1, 1, str)

    assert page["total"] == 2
    assert [item["content"] for item in page["items"]] == ["Body text."]


def test_outline_labels_titles_only(document_dir):
    outline = read_outline(document_dir)

    assert outline["total"] == 3
    assert [item["label"] for item in outline["items"]] == [
        "Annual report",
        None,
        None,
    ]


def test_unknown_type_and_image_lookups(document_dir):
    with pytest.raises(HTTPException) as unknown:
        require_content_type("Table")
    with pytest.raises(HTTPException) as not_an_image:
        image_response(document_dir, 0)
    served = image_response(document_dir, 1, headers={"Cache-Control": "no-cache"})

    assert unknown.value.status_code == 422
    assert not_an_image.value.status_code == 404
    assert served.media_type == "image/png"
    assert served.headers["cache-control"] == "no-cache"
