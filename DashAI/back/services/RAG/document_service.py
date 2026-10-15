"""Load the Data module documents a RAG pipeline indexes.

Documents are parsed once, when they are uploaded through the Data module,
and their content never changes afterwards. RAG reads that stored content
instead of extracting text again, so every session using a document sees the
same text.
"""

import logging
from pathlib import Path
from typing import Dict, List

from sqlalchemy.orm import Session

from DashAI.back.core.enums.status import DocumentStatus
from DashAI.back.dataloaders.classes.dashai_document import load_document
from DashAI.back.dependencies.database.models import DataDocument
from DashAI.back.models.RAG.documents.source_document import SourceDocument

log = logging.getLogger(__name__)

_CONTENT_DIRNAME = "document"


class DocumentService:
    """Turn ``DataDocument`` rows into the documents the RAG chunkers read.

    Parameters
    ----------
    db : Session
        Database session used to look the documents up.
    """

    def __init__(self, db: Session):
        self.db = db

    def load(self, document_ids: List[int]) -> Dict[int, SourceDocument]:
        """Load the parsed text of several documents.

        Parameters
        ----------
        document_ids : list of int
            ``data_document`` primary keys.

        Returns
        -------
        dict of int to SourceDocument
            One entry per requested document.

        Raises
        ------
        ValueError
            If a document does not exist or has not finished parsing.
        """
        documents: Dict[int, SourceDocument] = {}
        for document_id in document_ids:
            record = self.db.get(DataDocument, document_id)
            if record is None:
                raise ValueError(
                    f"Document with ID {document_id} not found in database."
                )
            if record.status != DocumentStatus.FINISHED:
                raise ValueError(
                    f"Document with ID {document_id} is not ready: its parsing "
                    f"status is {record.status.name}."
                )
            content = load_document(str(Path(record.file_path) / _CONTENT_DIRNAME))
            documents[document_id] = SourceDocument(
                id=record.id, file_name=record.name, content=content
            )
        return documents
