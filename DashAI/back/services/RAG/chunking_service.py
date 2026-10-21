import json
import logging
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.dataloaders.classes.dashai_document import (
    read_content_columns,
    save_document,
)
from DashAI.back.dependencies.database.models import (
    RAGChunkingModel as ChunkingModelDBModel,
)
from DashAI.back.dependencies.database.models import (
    RAGChunkSet,
    RAGChunkSetDocument,
)
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.chunking_models.chunking_model_factory import (
    ChunkingFactoryResult,
)
from DashAI.back.models.RAG.documents.chunk import Chunk
from DashAI.back.models.RAG.documents.source_document import SourceDocument
from DashAI.back.models.RAG.RAG_models_factory import RAGModelsFactory
from DashAI.back.models.RAG.utils import hash_function
from DashAI.back.types.value_types import Text

log = logging.getLogger(__name__)

CHUNK_SETS_DIRNAME = "chunk_sets"


def chunk_document_dir(
    rag_path: str | Path, chunk_set_id: int, document_id: int
) -> Path:
    """Return the folder holding the chunks of one document in a chunk set.

    Parameters
    ----------
    rag_path : str or Path
        The ``RAG_PATH`` setting.
    chunk_set_id : int
        The chunk set.
    document_id : int
        The ``data_document`` id.

    Returns
    -------
    Path
        ``<rag_path>/chunk_sets/<chunk_set_id>/<document_id>``.
    """
    return Path(rag_path) / CHUNK_SETS_DIRNAME / str(chunk_set_id) / str(document_id)


class ChunkingService:
    """Service for chunking lifecycle: chunk set identity, model persistence."""

    def __init__(
        self,
        db: Session,
        registry: ComponentRegistry,
        rag_path: Optional[str] = None,
    ):
        """Store the database session, the registry and the RAG folder.

        Parameters
        ----------
        db : Session
            Database session.
        registry : ComponentRegistry
            Registry resolving chunking model classes.
        rag_path : str, optional
            The ``RAG_PATH`` setting. Required by :meth:`create`, not by the
            signature helpers.
        """
        self._db = db
        self._registry = registry
        self._rag_path = rag_path

    # ── Chunk set identity ──

    def build_chunk_set_signature(
        self,
        session_id: int,
        document_ids: list[int],
        pipeline_config: dict[str, Any],
    ) -> str:
        """Build the SHA-256 identity of a session's chunk set.

        Public because read only callers (the index status service) must
        compute the same signature the pipeline uses. The session is part of
        it: Data documents are shared, and a chunk set shared by two sessions
        would let one session's cleanup destroy the other's index. Documents
        never change after parsing, so their ids identify their text.

        Parameters
        ----------
        session_id : int
            The session owning the chunk set.
        document_ids : list of int
            ``data_document`` ids, in any order.
        pipeline_config : dict
            The chunking configuration.

        Returns
        -------
        str
            The signature.
        """
        payload = json.dumps(
            {
                "session_id": session_id,
                "doc_ids": sorted(document_ids),
                "config": dict(sorted(pipeline_config.items())),
            },
            sort_keys=True,
        )
        return hash_function(payload)

    def get_or_create_chunk_set(
        self,
        session_id: int,
        document_ids: list[int],
        pipeline_config: dict[str, Any],
    ) -> RAGChunkSet:
        """Return the session's chunk set for a configuration, creating it once.

        Parameters
        ----------
        session_id : int
            The session owning the chunk set.
        document_ids : list of int
            ``data_document`` ids the chunk set covers.
        pipeline_config : dict
            The chunking configuration.

        Returns
        -------
        RAGChunkSet
            The existing or freshly created chunk set.

        Raises
        ------
        RuntimeError
            If a database error occurs.
        """
        signature = self.build_chunk_set_signature(
            session_id, document_ids, pipeline_config
        )
        try:
            existing = (
                self._db.query(RAGChunkSet).filter_by(signature=signature).first()
            )
            if existing:
                return existing

            chunk_set = RAGChunkSet(
                signature=signature,
                parameters=pipeline_config,
                session_id=session_id,
            )
            self._db.add(chunk_set)
            self._db.commit()
            self._db.refresh(chunk_set)

            for doc_id in sorted(document_ids):
                self._db.add(
                    RAGChunkSetDocument(chunk_set_id=chunk_set.id, document_id=doc_id)
                )
            self._db.commit()
            return chunk_set
        except exc.SQLAlchemyError as e:
            self._db.rollback()
            log.exception(e)
            raise RuntimeError("Database error during chunk set creation.") from e

    def create(
        self,
        documents: dict[int, SourceDocument],
        chunk_set_id: int,
        component_name: str,
        params: dict[str, Any],
    ) -> tuple[int, ChunkingFactoryResult]:
        """Chunk the documents of a chunk set that are not stored yet.

        The chunking model record is cached by ``(class_name, parameters)``.
        A document whose chunk folder already exists is not chunked again,
        so calling this twice with the same chunk set is cheap.

        Parameters
        ----------
        documents : dict of int to SourceDocument
            The documents of the chunk set, keyed by ``data_document`` id.
        chunk_set_id : int
            The chunk set receiving the chunks.
        component_name : str
            Registered chunking model name.
        params : dict
            Chunking model parameters.

        Returns
        -------
        tuple of (int, ChunkingFactoryResult)
            The chunking model record id and the model with every chunk of
            the chunk set.

        Raises
        ------
        RuntimeError
            If the service has no RAG folder, a document is not part of the
            chunk set, or a database error occurs.
        """
        if self._rag_path is None:
            raise RuntimeError("ChunkingService needs the RAG path to store chunks.")
        model = RAGModelsFactory(self._registry).create_chunking_model(
            component_name, params
        )
        try:
            record_id = self._get_or_create_record(component_name, params)
            links = {
                link.document_id: link
                for link in self._db.query(RAGChunkSetDocument)
                .filter_by(chunk_set_id=chunk_set_id)
                .all()
            }
            for document_id in sorted(documents):
                link = links.get(document_id)
                if link is None:
                    raise RuntimeError(
                        f"Document {document_id} is not part of chunk set "
                        f"{chunk_set_id}."
                    )
                if link.path and Path(link.path).is_dir():
                    continue
                chunked = model.chunk(documents[document_id].content)
                chunked.metadata["source_document_id"] = document_id
                folder = chunk_document_dir(self._rag_path, chunk_set_id, document_id)
                save_document(chunked, folder)
                link.path = str(folder)
                link.n_chunks = chunked.count(Text)
            self._db.commit()
        except exc.SQLAlchemyError as e:
            self._db.rollback()
            log.exception(e)
            raise RuntimeError("Database error during chunking.") from e
        return record_id, ChunkingFactoryResult(
            model=model, chunks=self.read_chunks(chunk_set_id)
        )

    def read_chunks(self, chunk_set_id: int) -> dict[int, dict[int, Chunk]]:
        """Read every stored chunk of a chunk set.

        Parameters
        ----------
        chunk_set_id : int
            The chunk set.

        Returns
        -------
        dict
            Chunks keyed by document id, then by position. ``Chunk.id`` is
            the ordinal over documents sorted by id, then positions.
        """
        links = (
            self._db.query(RAGChunkSetDocument)
            .filter_by(chunk_set_id=chunk_set_id)
            .order_by(RAGChunkSetDocument.document_id)
            .all()
        )
        chunks: dict[int, dict[int, Chunk]] = {}
        next_id = 0
        for link in links:
            if not link.path:
                continue
            columns = read_content_columns(link.path, Text)
            rows = sorted(
                zip(
                    columns["position"],
                    columns["content"],
                    columns["page"],
                    strict=True,
                )
            )
            document_chunks: dict[int, Chunk] = {}
            for position, text, page in rows:
                document_chunks[position] = Chunk(
                    id=next_id,
                    document_id=link.document_id,
                    document_position=position,
                    text=text,
                    page=page,
                )
                next_id += 1
            chunks[link.document_id] = document_chunks
        return chunks

    def _get_or_create_record(self, component_name: str, params: dict) -> int:
        """Return the id of the chunking model record, creating it once.

        Parameters
        ----------
        component_name : str
            Registered chunking model name.
        params : dict
            Chunking model parameters.

        Returns
        -------
        int
            The record id.
        """
        sorted_params = dict(sorted(params.items()))
        existing = (
            self._db.query(ChunkingModelDBModel)
            .filter_by(class_name=component_name, parameters=sorted_params)
            .first()
        )
        if existing is not None:
            return existing.id
        record = ChunkingModelDBModel(
            class_name=component_name, parameters=sorted_params
        )
        self._db.add(record)
        self._db.flush()
        return record.id
