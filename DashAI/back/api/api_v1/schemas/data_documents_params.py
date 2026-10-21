"""Schemas for the persistent documents of the Data module."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from DashAI.back.core.enums.status import DocumentStatus
from DashAI.back.dataloaders.classes.document_dataloader import redact_params


class DataDocumentCreateParams(BaseModel):
    """Body of ``POST /api/v1/documents/``.

    Attributes
    ----------
    name : str
        Unique document name.
    file_name : str
        Name of the file the user is about to upload. Its extension must be
        one the loader supports.
    dataloader : str
        Registry name of a ``DocumentDataLoader`` component.
    dataloader_params : Dict[str, Any]
        Loader parameters. Missing keys take the loader defaults.
    """

    name: str
    file_name: str
    dataloader: str
    dataloader_params: Dict[str, Any] = Field(default_factory=dict)


class DataDocumentFromNotebookParams(BaseModel):
    """Body of ``POST /api/v1/documents/from-notebook``.

    Attributes
    ----------
    name : str
        Unique name of the new document.
    notebook_id : int
        The document notebook whose working copy becomes the new document.
    """

    name: str
    notebook_id: int


class DataDocumentUpdateParams(BaseModel):
    """Body of ``PATCH /api/v1/documents/{id}``.

    Attributes
    ----------
    name : Optional[str]
        New name, or None to keep the current one.
    folder_id : Optional[int]
        Folder to move into. Sending ``null`` explicitly removes the folder;
        leaving the key out keeps it.
    """

    name: Optional[str] = None
    folder_id: Optional[int] = None


class DataDocumentSchema(BaseModel):
    """A ``DataDocument`` row as the API serves it.

    Attributes
    ----------
    id : int
        Primary key.
    name : str
        Unique document name.
    file_name : Optional[str]
        Original file name.
    file_type : Optional[str]
        Lowercase extension without the dot.
    file_path : Optional[str]
        The ``<DOCUMENTS_PATH>/<uuid>`` folder, empty until the job starts.
    dataloader : Optional[str]
        Loader component name.
    dataloader_params : Optional[Dict[str, Any]]
        Resolved loader parameters.
    content_counts : Optional[Dict[str, int]]
        Items per DashAI type name, for example ``{"Text": 12, "Image": 3}``.
    total_pages : Optional[int]
        Number of pages, None for formats without pages.
    folder_id : Optional[int]
        Folder holding the document.
    status : DocumentStatus
        Parsing status.
    created : datetime
        Creation time.
    last_modified : datetime
        Last change time.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_path: Optional[str] = None
    dataloader: Optional[str] = None
    dataloader_params: Optional[Dict[str, Any]] = None
    content_counts: Optional[Dict[str, int]] = None
    total_pages: Optional[int] = None
    folder_id: Optional[int] = None
    status: DocumentStatus
    created: datetime
    last_modified: datetime

    @field_validator("dataloader_params")
    @classmethod
    def _hide_secrets(cls, value: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Never return sensitive loader parameters such as passwords.

        Parameters
        ----------
        value : Optional[Dict[str, Any]]
            Stored loader parameters.

        Returns
        -------
        Optional[Dict[str, Any]]
            The parameters with sensitive values blanked.
        """
        return None if value is None else redact_params(value)
