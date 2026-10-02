"""Intermediate class for dataloaders that produce documents."""

from pathlib import Path
from typing import Any, ClassVar, Dict, Optional

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader

SENSITIVE_PARAMS = frozenset({"password"})


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
    set ``SCHEMA``, ``SUPPORTED_EXTENSIONS`` and ``DEFAULT_PARAMS`` and
    implement ``load_document``.
    """

    DATA_KIND: ClassVar[str] = "document"
    CATEGORY: ClassVar[MultilingualString] = MultilingualString(
        en="Document Uploading",
        es="Carga de Documentos",
        pt="Carregamento de Documentos",
        de="Dokument-Upload",
        zh="文档上传",
    )
    DEFAULT_PARAMS: ClassVar[Dict[str, Any]] = {}

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
        """Merge ``params`` over ``DEFAULT_PARAMS`` and validate them.

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
        merged = {**self.DEFAULT_PARAMS, **(params or {})}
        return self.SCHEMA.model_validate(merged).model_dump()

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
