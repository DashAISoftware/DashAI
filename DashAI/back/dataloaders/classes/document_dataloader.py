"""Intermediate class for dataloaders that produce documents."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional

from DashAI.back.core.schema_fields.utils import schema_placeholder_defaults
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader

if TYPE_CHECKING:
    from DashAI.back.types.dashai_image import DashAIImage

log = logging.getLogger(__name__)

SENSITIVE_PARAMS = frozenset({"password"})
WEB_IMAGE_TYPES = frozenset({"image/png", "image/jpeg", "image/gif", "image/webp"})
PNG_MODES = frozenset({"1", "L", "LA", "P", "RGB", "RGBA", "I;16"})


class DocumentLoaderError(Exception):
    """Raised when a document dataloader cannot parse a file."""


def redact_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Blank the loader parameters that must never be stored or shown.

    Parameters
    ----------
    params : Optional[Dict[str, Any]]
        Loader parameters.

    Returns
    -------
    Dict[str, Any]
        A copy where every key in ``SENSITIVE_PARAMS`` is set to None.
    """
    return {
        key: None if key in SENSITIVE_PARAMS else value
        for key, value in (params or {}).items()
    }


class DocumentDataLoader(BaseDataLoader):
    """DataLoader that parses one file into a ``DashAIDocument``.

    It stays a ``DataLoader`` component; ``DATA_KIND = "document"`` lets
    dataset consumers hide it and lets ``DocumentJob`` require it. Subclasses
    set ``SCHEMA`` and ``SUPPORTED_EXTENSIONS`` and implement
    ``load_document``.
    """

    DATA_KIND: ClassVar[str] = "document"
    CATEGORY: ClassVar[MultilingualString] = MultilingualString(
        en="Document Extractor",
        es="Extractor de Documentos",
        pt="Extrator de Documentos",
        de="Dokument-Extraktor",
        zh="文档提取器",
    )

    @classmethod
    def supports_file(cls, file_name: str) -> bool:
        """Tell whether the loader accepts a file by its extension.

        Parameters
        ----------
        file_name : str
            Name or path of the file.

        Returns
        -------
        bool
            True when the lowercased suffix is in ``SUPPORTED_EXTENSIONS``.
        """
        return Path(file_name).suffix.lower() in cls.SUPPORTED_EXTENSIONS

    def resolve_params(self, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fill the parameters the caller left out and validate them.

        Every schema field declares its default as its ``placeholder``, which
        is also what the frontend form shows, so a payload that omits a field
        validates exactly as the submitted form would have.

        Parameters
        ----------
        params : Optional[Dict[str, Any]]
            Loader parameters as the form sends them.

        Returns
        -------
        Dict[str, Any]
            Every schema field with its validated value.

        Raises
        ------
        pydantic.ValidationError
            If a value breaks the schema.
        """
        merged = {**schema_placeholder_defaults(type(self)), **(params or {})}
        return self.SCHEMA.model_validate(merged).model_dump()

    @staticmethod
    def web_image(data: bytes, name: str) -> "DashAIImage":
        """Wrap extracted image bytes, converting them to PNG when needed.

        Documents are shown in the browser, which cannot draw formats such
        as TIFF (common for scanned pages), JPEG 2000 or BMP. Those are
        converted to PNG; PNG, JPEG, GIF and WebP are kept as they are, and
        bytes Pillow cannot read are kept unchanged.

        Parameters
        ----------
        data : bytes
            The extracted image bytes.
        name : str
            The image name given by the file.

        Returns
        -------
        DashAIImage
            The image, with a ``.png`` name when it was converted.
        """
        import io

        import filetype
        from PIL import Image

        from DashAI.back.types.dashai_image import DashAIImage

        kind = filetype.guess(data)
        if kind is not None and kind.mime in WEB_IMAGE_TYPES:
            return DashAIImage(bytes=data, path=name)
        try:
            with Image.open(io.BytesIO(data)) as image:
                if image.mode not in PNG_MODES:
                    image = image.convert("RGBA" if "A" in image.mode else "RGB")
                buffer = io.BytesIO()
                image.save(buffer, format="PNG", optimize=True)
        except Exception as e:
            log.warning("Could not convert image %s to PNG: %s", name, e)
            return DashAIImage(bytes=data, path=name)
        return DashAIImage(bytes=buffer.getvalue(), path=f"{Path(name).stem}.png")

    def build_metadata(
        self, file_path: str, params: Dict[str, Any], n_pages: Optional[int]
    ) -> Dict[str, Any]:
        """Build the metadata stored with the parsed document.

        Parameters
        ----------
        file_path : str
            Path of the parsed file.
        params : Dict[str, Any]
            The resolved loader parameters.
        n_pages : Optional[int]
            Number of pages, None when the format has no pages.

        Returns
        -------
        Dict[str, Any]
            ``file_name``, ``file_type``, ``n_pages``, ``dataloader``,
            ``dataloader_params``.
        """
        path = Path(file_path)
        return {
            "file_name": path.name,
            "file_type": path.suffix.lower().lstrip("."),
            "n_pages": n_pages,
            "dataloader": type(self).__name__,
            "dataloader_params": redact_params(params),
        }

    def load_data(self, filepath_or_buffer, temp_path, params, n_sample=None):
        """Refuse to build a dataset.

        Raises
        ------
        NotImplementedError
            Always; document loaders implement ``load_document``.
        """
        raise NotImplementedError(
            f"{type(self).__name__} loads documents; use load_document."
        )
