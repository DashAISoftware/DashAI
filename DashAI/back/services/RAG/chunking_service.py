import json
import logging
from typing import Any

from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.dependencies.database.models import (
    Chunk as ChunkDBModel,
)
from DashAI.back.dependencies.database.models import (
    Document,
    RAGChunkSet,
    RAGChunkSetDocument,
)
from DashAI.back.dependencies.database.models import (
    RAGChunkingModel as ChunkingModelDBModel,
)
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.chunking_models.chunking_model_factory import (
    ChunkingFactoryResult,
)
from DashAI.back.models.RAG.documents.base_document import BaseDocument
from DashAI.back.models.RAG.documents.chunk import Chunk
from DashAI.back.models.RAG.RAG_models_factory import RAGModelsFactory
from DashAI.back.models.RAG.utils import hash_function

log = logging.getLogger(__name__)


class ChunkingService:
    """Service for chunking lifecycle: chunk set identity, model persistence."""

    def __init__(self, db: Session, registry: ComponentRegistry):
        self._db = db
        self._registry = registry

    # ── Chunk set identity ──

    def build_chunk_set_signature(
        self, document_ids: list[int], pipeline_config: dict[str, Any]
    ) -> str:
        """Build SHA-256 signature for deterministic chunk set identity.

        Public because read-only callers (e.g. the index-status service) must
        compute the *same* signature the pipeline will use; a second
        implementation would drift and report a stale index as fresh.
        """
        extractors = {}
        for doc_id in sorted(document_ids):
            db_doc = self._db.get(Document, doc_id)
            if db_doc and db_doc.extractor_id is not None:
                extractors[str(doc_id)] = str(db_doc.extractor_id)
            else:
                extractors[str(doc_id)] = "default"

        payload = json.dumps(
            {
                "doc_ids": sorted(document_ids),
                "doc_extractors": dict(sorted(extractors.items())),
                "config": dict(sorted(pipeline_config.items())),
            },
            sort_keys=True,
        )
        return hash_function(payload)

    def get_or_create_chunk_set(
        self,
        document_ids: list[int],
        pipeline_config: dict[str, Any],
    ) -> RAGChunkSet:
        """Deterministic chunk-set identity via SHA-256.

        1. Build signature
        2. Query RAGChunkSet by signature -> return if exists (CACHE HIT)
        3. Create RAGChunkSet + RAGChunkSetDocument rows
        4. Return new chunk set

        Raises RuntimeError on DB error.
        """
        signature = self.build_chunk_set_signature(document_ids, pipeline_config)
        try:
            existing = (
                self._db.query(RAGChunkSet).filter_by(signature=signature).first()
            )
            if existing:
                return existing

            chunk_set = RAGChunkSet(signature=signature, parameters=pipeline_config)
            self._db.add(chunk_set)
            self._db.commit()
            self._db.refresh(chunk_set)

            for doc_id in sorted(document_ids):
                self._db.add(
                    RAGChunkSetDocument(
                        chunk_set_id=chunk_set.id,
                        document_id=doc_id,
                    )
                )
            self._db.commit()
            return chunk_set
        except exc.SQLAlchemyError as e:
            self._db.rollback()
            log.exception(e)
            raise RuntimeError("Database error during chunk set creation.") from e

    # ── Chunking model lifecycle ──

    def create(
        self,
        documents: dict[int, BaseDocument],
        chunk_set_id: int,
        component_name: str,
        params: dict[str, Any],
    ) -> tuple[int, ChunkingFactoryResult]:
        """Lookup-or-create the chunking model and chunks for a chunk set.

        Chunking models are cached by ``(class_name, parameters)``:

        1. If a cached model exists AND the chunk set already has persisted
           chunks, the model is rebuilt in memory and returned as-is.
        2. If a cached model exists BUT the chunk set has no persisted
           chunks, chunks are computed and persisted now (a cached model
           does not imply the current chunk set was already chunked).
        3. Otherwise (no cached model), the model record is created and the
           chunks are computed and persisted.

        Returns:
            (db_record_id, ChunkingFactoryResult(model, chunks)).
        """
        sorted_params = dict(sorted(params.items()))

        try:
            existing = (
                self._db.query(ChunkingModelDBModel)
                .filter_by(class_name=component_name, parameters=sorted_params)
                .first()
            )
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise RuntimeError("Database error during chunking model lookup.") from e

        if existing is not None:
            chunks = self._fetch_chunks_from_db(chunk_set_id)
            if not chunks:
                result = self._compute_chunks(component_name, params, documents)
                self._persist_chunks_and_update_ids(result, chunk_set_id)
                return existing.id, result
            model_params = {**params, "documents": documents}
            model_class = self._registry[component_name]["class"]
            model = model_class(**model_params)
            model.chunks = chunks
            return existing.id, ChunkingFactoryResult(model=model, chunks=chunks)

        result = self._compute_chunks(component_name, params, documents)
        try:
            record_id = self._save_db_record(result.model)
        except exc.SQLAlchemyError as e:
            self._db.rollback()
            log.exception(e)
            raise RuntimeError(
                "Database error during chunking model persistence."
            ) from e
        self._persist_chunks_and_update_ids(result, chunk_set_id)
        return record_id, result

    # ── Private DB helpers ──

    def _compute_chunks(
        self,
        component_name: str,
        params: dict[str, Any],
        documents: dict[int, BaseDocument],
    ) -> ChunkingFactoryResult:
        """Chunk the documents with the pure factory. Phase 1 only — no DB access."""
        factory = RAGModelsFactory(self._registry)
        return factory.create_chunking_model(component_name, params, documents)

    def _persist_chunks_and_update_ids(
        self, result: ChunkingFactoryResult, chunk_set_id: int
    ) -> None:
        """Persist chunks for a chunk set and patch in-memory chunk ids.

        Chunks are written to the database and the freshly-assigned primary
        keys are propagated back into the in-memory model without any
        additional database queries.
        """
        try:
            id_map = self._persist_chunks(result.chunks, chunk_set_id)
            self._update_chunk_ids(result.model, id_map)
        except exc.SQLAlchemyError as e:
            self._db.rollback()
            log.exception(e)
            raise RuntimeError(
                "Database error during chunking model persistence."
            ) from e

    def _save_db_record(self, model) -> int:
        """Persist a chunking model record to the database.

        Args:
            model: Chunking model instance with a ``parameters`` attribute.

        Returns:
            Primary key of the newly created DB record.
        """
        sorted_params = dict(sorted(model.parameters.items()))
        record = ChunkingModelDBModel(
            class_name=model.__class__.__name__,
            parameters=sorted_params,
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record.id

    def _fetch_chunks_from_db(self, chunk_set_id: int) -> dict[int, dict[int, Chunk]]:
        """Load all chunks for a chunk set from the database.

        Args:
            chunk_set_id: Chunk set identifier.

        Returns:
            Nested dict keyed by ``document_id`` then ``chunk_index``.
        """
        chunks: dict[int, dict[int, Chunk]] = {}
        db_chunks = (
            self._db.query(ChunkDBModel).filter_by(chunk_set_id=chunk_set_id).all()
        )
        for db_chunk in db_chunks:
            if db_chunk.document_id not in chunks:
                chunks[db_chunk.document_id] = {}
            chunk = Chunk(
                id=db_chunk.id,
                document_id=db_chunk.document_id,
                document_position=db_chunk.chunk_index,
                text=db_chunk.text,
            )
            chunks[db_chunk.document_id][db_chunk.chunk_index] = chunk
        return chunks

    def _persist_chunks(
        self,
        chunks: dict[int, dict[int, Chunk]],
        chunk_set_id: int,
    ) -> dict[tuple[int, int], int]:
        """Write chunk rows to the database and return their assigned ids.

        Ids are read right after ``flush()`` (when autoincrement primary
        keys are populated) but before ``commit()``, because the session's
        ``expire_on_commit`` default would otherwise refresh every column
        with a per-row SELECT on the next attribute access.

        Args:
            chunks: Nested dict of chunks keyed by document_id and index.
            chunk_set_id: FK to the owning chunk set.

        Returns:
            Mapping of (document_id, chunk_index) to the DB-assigned chunk
            primary key.
        """
        persisted: list[tuple[int, int, ChunkDBModel]] = []
        for document_id, document_chunks in chunks.items():
            for idx, chunk in document_chunks.items():
                db_chunk = ChunkDBModel(
                    document_id=document_id,
                    chunk_index=idx,
                    chunk_set_id=chunk_set_id,
                    text=chunk.text,
                )
                persisted.append((document_id, idx, db_chunk))
                self._db.add(db_chunk)
        self._db.flush()
        id_map = {(doc_id, idx): db_chunk.id for doc_id, idx, db_chunk in persisted}
        self._db.commit()
        return id_map

    def _update_chunk_ids(self, model, id_map: dict[tuple[int, int], int]) -> None:
        """Patch in-memory chunk ids with their DB-assigned primary keys.

        Uses the mapping built during persistence, so no database queries
        are executed here.

        Args:
            model: Chunking model whose ``chunks`` dict will be mutated.
            id_map: Mapping of (document_id, chunk_index) to the DB-assigned
                chunk primary key.

        Raises:
            KeyError: If a chunk produced by the model is missing from
                ``id_map`` — the caller persisted a different chunk set.
        """
        for document_id, document_chunks in model.get_chunks().items():
            for idx, _chunk in document_chunks.items():
                model.chunks[document_id][idx].id = id_map[(document_id, idx)]
