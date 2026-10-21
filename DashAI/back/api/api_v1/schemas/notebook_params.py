from datetime import datetime
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, model_validator


class NotebookBase(BaseModel):
    name: Union[str, None] = None
    description: Union[str, None] = None


class NotebookCreate(NotebookBase):
    """Parameters to create a notebook from a dataset or a document.

    Exactly one of ``dataset_id`` and ``document_id`` must be given.
    """

    dataset_id: Optional[int] = None
    document_id: Optional[int] = None

    @model_validator(mode="after")
    def check_exactly_one_source(self) -> "NotebookCreate":
        """Require exactly one notebook source.

        Returns
        -------
        NotebookCreate
            The validated parameters.

        Raises
        ------
        ValueError
            If both or neither of ``dataset_id`` and ``document_id`` are set.
        """
        if (self.dataset_id is None) == (self.document_id is None):
            raise ValueError("Provide exactly one of dataset_id or document_id")
        return self


class Notebook(NotebookBase):
    id: int
    dataset_id: Optional[int] = None
    document_id: Optional[int] = None
    data_kind: Literal["dataset", "document"]
    created: datetime
    last_modified: datetime
    file_path: str


class NotebookUpdateParams(BaseModel):
    name: str = None


class NotebookBulkDeleteParams(BaseModel):
    ids: List[int]
