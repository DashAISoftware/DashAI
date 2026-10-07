"""Read helpers that serve a saved DashAIDocument through the API.

The Data module documents (``/api/v1/documents``) and the document notebooks
(``/api/v1/notebook``) both serve their parsed content through these
functions, so the two return the same item shape. None of them loads the
whole document: each reads only the content types and columns it needs.
"""

import io
import os
from typing import Any, Callable, Dict, List, Mapping, Optional, Union

from fastapi import Response, status
from fastapi.exceptions import HTTPException

CONTENT_TYPES = ("Text", "Image")
OUTLINE_LABEL_KINDS = ("title", "heading", "caption")
OUTLINE_LABEL_LENGTH = 120


def require_content_type(content_type: str) -> None:
    """Fail with 422 unless ``content_type`` is ``"all"`` or a known type.

    Parameters
    ----------
    content_type : str
        Requested content type.

    Raises
    ------
    HTTPException
        422 for anything other than ``"all"``, ``"Text"`` or ``"Image"``.
    """
    if content_type != "all" and content_type not in CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown content type '{content_type}'. Use all, Text or Image.",
        )


def read_content_page(
    directory: Union[str, os.PathLike],
    content_type: str,
    offset: int,
    limit: int,
    image_url: Callable[[int], str],
) -> Dict[str, Any]:
    """Read one page of a saved document's items, in reading order.

    Image bytes are never read: an Image item carries the URL that serves it.

    Parameters
    ----------
    directory : str or os.PathLike
        Directory written by ``save_document``.
    content_type : str
        ``"all"``, ``"Text"`` or ``"Image"``, already validated with
        :func:`require_content_type`.
    offset : int
        Index of the first item of the page.
    limit : int
        Page size.
    image_url : Callable[[int], str]
        Builds the URL of the Image item at a reading order position.

    Returns
    -------
    Dict[str, Any]
        ``content_type``, ``total``, ``offset``, ``limit`` and ``items``;
        every item has ``type``, ``position``, ``page``, ``kind`` and
        ``attrs``, plus ``content`` (Text) or ``url`` (Image).
    """
    from DashAI.back.dataloaders.classes.dashai_document import read_content_columns
    from DashAI.back.types.dashai_image import DashAIImage
    from DashAI.back.types.value_types import Text

    entries: List[Dict[str, Any]] = []
    if content_type in ("all", "Text"):
        texts = read_content_columns(directory, Text)
        entries.extend(
            {
                "type": "Text",
                "position": position,
                "page": page,
                "kind": kind,
                "attrs": attrs,
                "content": text,
            }
            for text, position, page, kind, attrs in zip(
                texts["content"],
                texts["position"],
                texts["page"],
                texts["kind"],
                texts["attrs"],
                strict=True,
            )
        )
    if content_type in ("all", "Image"):
        images = read_content_columns(directory, DashAIImage, with_content=False)
        entries.extend(
            {
                "type": "Image",
                "position": position,
                "page": page,
                "kind": kind,
                "attrs": attrs,
                "url": image_url(position),
            }
            for position, page, kind, attrs in zip(
                images["position"],
                images["page"],
                images["kind"],
                images["attrs"],
                strict=True,
            )
        )
    entries.sort(key=lambda entry: entry["position"])
    return {
        "content_type": content_type,
        "total": len(entries),
        "offset": offset,
        "limit": limit,
        "items": entries[offset : offset + limit],
    }


def read_outline(directory: Union[str, os.PathLike]) -> Dict[str, Any]:
    """Read the structure of a saved document without its content.

    Parameters
    ----------
    directory : str or os.PathLike
        Directory written by ``save_document``.

    Returns
    -------
    Dict[str, Any]
        ``total`` and ``items`` in reading order; each item has
        ``position``, ``type``, ``kind``, ``page``, ``level`` and a short
        single line ``label`` for titles, headings and captions.
    """
    from DashAI.back.dataloaders.classes.dashai_document import read_content_columns
    from DashAI.back.types.dashai_image import DashAIImage
    from DashAI.back.types.value_types import Text

    texts = read_content_columns(directory, Text)
    images = read_content_columns(directory, DashAIImage, with_content=False)
    entries: List[Dict[str, Any]] = [
        {
            "position": position,
            "type": "Text",
            "kind": kind,
            "page": page,
            "level": attrs.get("level"),
            "label": " ".join(text.split())[:OUTLINE_LABEL_LENGTH]
            if kind in OUTLINE_LABEL_KINDS
            else None,
        }
        for text, position, page, kind, attrs in zip(
            texts["content"],
            texts["position"],
            texts["page"],
            texts["kind"],
            texts["attrs"],
            strict=True,
        )
    ]
    entries.extend(
        {
            "position": position,
            "type": "Image",
            "kind": kind,
            "page": page,
            "level": None,
            "label": None,
        }
        for position, page, kind in zip(
            images["position"], images["page"], images["kind"], strict=True
        )
    )
    entries.sort(key=lambda entry: entry["position"])
    return {"total": len(entries), "items": entries}


def image_media_type(data: bytes) -> str:
    """Detect an image MIME type with Pillow.

    Parameters
    ----------
    data : bytes
        Encoded image.

    Returns
    -------
    str
        The MIME type, ``application/octet-stream`` when unknown.
    """
    from PIL import Image

    try:
        with Image.open(io.BytesIO(data)) as image:
            return Image.MIME.get(image.format, "application/octet-stream")
    except Exception:
        return "application/octet-stream"


def image_response(
    directory: Union[str, os.PathLike],
    position: int,
    headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """Serve the bytes of the Image item at a reading order position.

    Only that item's bytes are copied out of the image file.

    Parameters
    ----------
    directory : str or os.PathLike
        Directory written by ``save_document``.
    position : int
        Global position of the item.
    headers : Mapping[str, str], optional
        Extra response headers.

    Returns
    -------
    Response
        The image bytes with their detected media type.

    Raises
    ------
    HTTPException
        404 when no Image item sits at ``position``.
    """
    from DashAI.back.dataloaders.classes.dashai_document import read_content_at
    from DashAI.back.types.dashai_image import DashAIImage

    value = read_content_at(directory, DashAIImage, position)
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    data = value["bytes"]
    return Response(content=data, media_type=image_media_type(data), headers=headers)
