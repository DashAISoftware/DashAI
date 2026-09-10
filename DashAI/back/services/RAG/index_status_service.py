"""Read-only view of whether a RAG session's documents are already indexed.

Indexing is not a job of its own: chunking, embedding and retriever fitting all
happen inside ``RAGJob`` while answering a chat message, and everything is
content-addressed, so "is this indexed?" is answered by looking for the rows the
pipeline would otherwise create.

This service only reads. It never chunks, embeds or writes, so it is safe to
call on every page load.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import (
    Chunk as ChunkDBModel,
)
from DashAI.back.dependencies.database.models import (
    Document,
    GenerativeSession,
    GenerativeSessionParameterHistory,
    RAGChunkSet,
)
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.RAG_constants import (
    RAG_PARAM_CHUNKING_MODEL,
    RAG_PARAM_DOCUMENTS,
    RAG_PARAM_RETRIEVER_MODEL,
)
from DashAI.back.models.RAG.retrievers.dense.dense_retriever import DenseRetriever
from DashAI.back.models.RAG.retrievers.sparse.sparse_retriever import SparseRetriever
from DashAI.back.services.RAG.chunking_service import ChunkingService
from DashAI.back.services.RAG.retriever_db_service import RetrieverDBService

log = logging.getLogger(__name__)

#: Session has never been indexed under any configuration.
STATUS_NOT_INDEXED = "not_indexed"
#: A previous configuration was indexed, the current one is not.
STATUS_STALE = "stale"
#: Everything the pipeline needs is already on disk and in the database.
STATUS_INDEXED = "indexed"

_MESSAGES = {
    STATUS_NOT_INDEXED: MultilingualString(
        en="The documents will be indexed when you send your first message.",
        es="Los documentos se indexarán cuando envíes tu primer mensaje.",
        pt="Os documentos serão indexados quando você enviar a primeira mensagem.",
        de="Die Dokumente werden beim Senden der ersten Nachricht indexiert.",
        zh="文档将在你发送第一条消息时建立索引。",
    ),
    STATUS_STALE: MultilingualString(
        en=(
            "The configuration changed, so the documents will be re-indexed "
            "with your next message."
        ),
        es=(
            "La configuración cambió, así que los documentos se reindexarán "
            "en tu próximo mensaje."
        ),
        pt=(
            "A configuração mudou, então os documentos serão reindexados na "
            "sua próxima mensagem."
        ),
        de=(
            "Die Konfiguration hat sich geändert, daher werden die Dokumente "
            "mit der nächsten Nachricht neu indexiert."
        ),
        zh="配置已更改，文档将在你的下一条消息时重新建立索引。",
    ),
    STATUS_INDEXED: MultilingualString(
        en="The documents are indexed and ready to answer questions.",
        es="Los documentos están indexados y listos para responder preguntas.",
        pt="Os documentos estão indexados e prontos para responder perguntas.",
        de="Die Dokumente sind indexiert und bereit für Fragen.",
        zh="文档已建立索引，可以开始提问。",
    ),
}


class IndexStatusService:
    """Reports the indexing state of a RAG session without mutating anything."""

    def __init__(self, db: Session, registry: ComponentRegistry):
        """Initialise the service.

        Parameters
        ----------
        db : Session
            SQLAlchemy session used for the read-only lookups.
        registry : ComponentRegistry
            Registry used to tell dense retrievers from sparse ones.
        """
        self._db = db
        self._registry = registry
        # Reused so the signature matches the one the pipeline computes; a
        # second implementation would drift and misreport a stale index.
        self._chunking = ChunkingService(db, registry)
        self._retrievers = RetrieverDBService(db)

    # ── Public API ────────────────────────────────────────────────────

    def get_status(self, session_id: int) -> Dict[str, Any]:
        """Return the indexing status of a RAG session.

        Parameters
        ----------
        session_id : int
            The generative session to inspect.

        Returns
        -------
        dict
            ``{status, chunk_set_id, total_chunks, retriever_ready, documents,
            message}``. ``message`` is a :class:`MultilingualString` the caller
            is expected to localize.

        Raises
        ------
        ValueError
            If the session does not exist.
        """
        session = self._db.get(GenerativeSession, session_id)
        if session is None:
            raise ValueError(f"Generative session {session_id} does not exist.")

        parameters = dict(session.parameters or {})
        # Documents come from the session parameters, never from
        # RAGDocumentPipelineSessionLink: nothing in production writes that
        # table, so it is always empty.
        document_ids = [
            doc_id for doc_id in parameters.get(RAG_PARAM_DOCUMENTS) or [] if doc_id
        ]

        chunk_set = self._find_chunk_set(document_ids, parameters)
        counts = self._chunk_counts(chunk_set.id, document_ids) if chunk_set else {}
        documents = self._describe_documents(document_ids, counts)
        total_chunks = sum(counts.values())

        retriever_ready = bool(chunk_set) and self._retriever_ready(
            parameters.get(RAG_PARAM_RETRIEVER_MODEL), chunk_set.id
        )
        all_chunked = bool(document_ids) and all(doc["indexed"] for doc in documents)
        status = self._resolve_status(
            session_id=session_id,
            parameters=parameters,
            all_chunked=all_chunked,
            retriever_ready=retriever_ready,
        )

        return {
            "status": status,
            "chunk_set_id": chunk_set.id if chunk_set else None,
            "total_chunks": total_chunks,
            "retriever_ready": retriever_ready,
            "documents": documents,
            "message": _MESSAGES[status],
        }

    # ── Private helpers ───────────────────────────────────────────────

    def _resolve_status(
        self,
        session_id: int,
        parameters: Dict[str, Any],
        all_chunked: bool,
        retriever_ready: bool,
    ) -> str:
        """Classify the session into one of the three indexing states."""
        if all_chunked and retriever_ready:
            return STATUS_INDEXED
        if self._was_indexed_before(session_id, parameters):
            return STATUS_STALE
        return STATUS_NOT_INDEXED

    def _pipeline_config(self, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build the chunk-set config for a parameters payload, if complete."""
        chunking = parameters.get(RAG_PARAM_CHUNKING_MODEL)
        if not isinstance(chunking, dict) or not chunking.get("component"):
            return None
        return {
            RAG_PARAM_CHUNKING_MODEL: {
                "component": chunking["component"],
                "params": chunking.get("params") or {},
            }
        }

    def _find_chunk_set(
        self, document_ids: List[int], parameters: Dict[str, Any]
    ) -> Optional[RAGChunkSet]:
        """Return the chunk set matching a configuration, without creating it."""
        config = self._pipeline_config(parameters)
        if not document_ids or config is None:
            return None
        signature = self._chunking.build_chunk_set_signature(document_ids, config)
        return self._db.query(RAGChunkSet).filter_by(signature=signature).first()

    def _was_indexed_before(
        self, session_id: int, current_parameters: Dict[str, Any]
    ) -> bool:
        """Whether an earlier configuration of this session left chunks behind.

        Distinguishes "changed the settings on a working session" from "brand
        new session", which is the difference the user needs to see: only the
        former warrants a re-indexing warning.
        """
        current = self._pipeline_config(current_parameters)
        history = (
            self._db.query(GenerativeSessionParameterHistory)
            .filter_by(session_id=session_id)
            .order_by(GenerativeSessionParameterHistory.modified_at.desc())
            .all()
        )
        for entry in history:
            parameters = dict(entry.parameters or {})
            config = self._pipeline_config(parameters)
            if config is None or config == current:
                continue
            document_ids = [
                doc_id for doc_id in parameters.get(RAG_PARAM_DOCUMENTS) or [] if doc_id
            ]
            chunk_set = self._find_chunk_set(document_ids, parameters)
            if chunk_set and self._chunk_counts(chunk_set.id, document_ids):
                return True
        return False

    def _chunk_counts(
        self, chunk_set_id: int, document_ids: List[int]
    ) -> Dict[int, int]:
        """Return ``{document_id: chunk_count}`` for a chunk set."""
        if not document_ids:
            return {}
        rows = (
            self._db.query(ChunkDBModel.document_id, func.count(ChunkDBModel.id))
            .filter(
                ChunkDBModel.chunk_set_id == chunk_set_id,
                ChunkDBModel.document_id.in_(document_ids),
            )
            .group_by(ChunkDBModel.document_id)
            .all()
        )
        return dict(rows)

    def _describe_documents(
        self, document_ids: List[int], counts: Dict[int, int]
    ) -> List[Dict[str, Any]]:
        """Build the per-document rows the UI renders next to each file."""
        documents = []
        for document_id in document_ids:
            record = self._db.get(Document, document_id)
            chunks = counts.get(document_id, 0)
            documents.append(
                {
                    "document_id": document_id,
                    "file_name": record.file_name if record else None,
                    "chunks": chunks,
                    "indexed": chunks > 0,
                }
            )
        return documents

    def _retriever_ready(
        self, retriever: Optional[Dict[str, Any]], chunk_set_id: int
    ) -> bool:
        """Whether every unit retriever in a config is already fitted.

        Composite retrievers are never cached by the pipeline — only their
        children are — so a composite is ready exactly when all of its leaves
        are.
        """
        if not isinstance(retriever, dict) or not retriever.get("component"):
            return False
        params = retriever.get("params") or {}

        children = params.get("children")
        if isinstance(children, list) and children:
            return all(
                self._retriever_ready(child, chunk_set_id)
                for child in children
                if isinstance(child, dict)
            )

        component = retriever["component"]
        if component not in self._registry:
            return False
        model_class = self._registry[component]["class"]
        sorted_params = dict(sorted(params.items()))
        try:
            if issubclass(model_class, DenseRetriever):
                return (
                    self._retrievers.find_dense(component, sorted_params, chunk_set_id)
                    is not None
                )
            if issubclass(model_class, SparseRetriever):
                return (
                    self._retrievers.find_sparse(component, sorted_params, chunk_set_id)
                    is not None
                )
        except Exception:  # pragma: no cover - defensive, status must not 500
            log.exception("Retriever lookup failed for %s", component)
            return False
        # A retriever that is neither dense nor sparse (e.g. a reranker with no
        # children) has nothing persisted to check, so it is never a blocker.
        return True
