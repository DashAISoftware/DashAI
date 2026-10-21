"""Document and corpus knowledge shared by the LLM-evaluated retrievers.

``RetrievalContext`` is the single owner of "which chunks exist and which
documents they belong to". It never formats text: prompt rendering belongs to
the prompt components and verdict parsing belongs to the evaluator.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Dict, List, Mapping

from DashAI.back.models.RAG.documents import Chunk, RAGDocument
from DashAI.back.models.RAG.retrievers.retrieval_contracts import (
    DOCUMENT_CHUNKS,
    DOCUMENT_ID,
    DOCUMENT_NAME,
    DOCUMENT_PAGES,
    DocumentSummary,
)

#: Maximum nesting depth inspected when collecting child documents/corpora.
_MAX_CONTEXT_DEPTH = 32


class RetrievalContext:
    """Read-only document and corpus knowledge for one retrieval run.

    Parameters
    ----------
    documents : Mapping[int, RAGDocument]
        Known documents keyed by document id.
    corpus : Mapping[int, Mapping[int, Chunk]]
        Full chunk corpus keyed by document id and chunk id.
    """

    def __init__(
        self,
        documents: Mapping[int, RAGDocument],
        corpus: Mapping[int, Mapping[int, Chunk]],
    ) -> None:
        self._documents: Dict[int, RAGDocument] = dict(documents)
        self._corpus: Dict[int, Dict[int, Chunk]] = {}
        for document_id, document_chunks in corpus.items():
            self._corpus[document_id] = dict(document_chunks)

    @classmethod
    def from_retriever(cls, retriever: Any) -> "RetrievalContext":
        """Build a context from a retriever and, when needed, its children.

        Parameters
        ----------
        retriever : Any
            Retriever whose ``documents`` and ``chunks`` attributes are read.
            Partial mappings are merged with the children's knowledge; parent
            entries win on document-id collisions.

        Returns
        -------
        RetrievalContext
            A context exposing the merged documents and corpus.
        """
        return cls(
            cls._collect_documents(retriever),
            cls._collect_corpus(retriever),
        )

    @classmethod
    def _collect_documents(
        cls, retriever: Any, depth: int = 0
    ) -> Dict[int, RAGDocument]:
        """Collect documents from a retriever or, recursively, its children.

        Parameters
        ----------
        retriever : Any
            Retriever whose ``documents`` mapping is inspected first.
        depth : int
            Current nesting depth; recursion stops at ``_MAX_CONTEXT_DEPTH``.

        Returns
        -------
        Dict[int, RAGDocument]
            Merged document mapping keyed by document id. Entries owned by the
            current retriever win over descendant entries with the same id.
        """
        collected: Dict[int, RAGDocument] = {}
        documents = getattr(retriever, "documents", None) or {}
        for document_id, document in documents.items():
            collected[document_id] = document
        if depth >= _MAX_CONTEXT_DEPTH:
            return collected
        try:
            children = retriever.get_children()
        except NotImplementedError:
            children = []
        for child in children:
            child_documents = cls._collect_documents(child, depth + 1)
            for document_id, document in child_documents.items():
                collected.setdefault(document_id, document)
        return collected

    @classmethod
    def _collect_corpus(
        cls, retriever: Any, depth: int = 0
    ) -> Dict[int, Dict[int, Chunk]]:
        """Collect the retriever's own corpus or, recursively, its children's.

        Parameters
        ----------
        retriever : Any
            Retriever whose ``chunks`` mapping is inspected first.
        depth : int
            Current nesting depth; recursion stops at ``_MAX_CONTEXT_DEPTH``.

        Returns
        -------
        Dict[int, Dict[int, Chunk]]
            Merged corpus keyed by document id and chunk id.
        """
        chunks = getattr(retriever, "chunks", None)
        if chunks:
            collected: Dict[int, Dict[int, Chunk]] = {}
            for document_id, document_chunks in chunks.items():
                collected[document_id] = dict(document_chunks)
            return collected
        if depth >= _MAX_CONTEXT_DEPTH:
            return {}
        try:
            children = retriever.get_children()
        except NotImplementedError:
            children = []
        corpus: Dict[int, Dict[int, Chunk]] = {}
        for child in children:
            child_corpus = cls._collect_corpus(child, depth + 1)
            for document_id, document_chunks in child_corpus.items():
                corpus.setdefault(document_id, {}).update(document_chunks)
        return corpus

    def corpus(self) -> Mapping[int, Mapping[int, Chunk]]:
        """Return a deeply read-only view of the corpus mapping.

        Returns
        -------
        Mapping[int, Mapping[int, Chunk]]
            The corpus keyed by document id and chunk id. Both the outer mapping
            and each per-document chunk mapping are read-only.
        """
        frozen: Dict[int, Mapping[int, Chunk]] = {}
        for document_id, document_chunks in self._corpus.items():
            frozen[document_id] = MappingProxyType(document_chunks)
        return MappingProxyType(frozen)

    def documents(self) -> Mapping[int, RAGDocument]:
        """Return a read-only view of the document mapping.

        Returns
        -------
        Mapping[int, RAGDocument]
            The known documents keyed by document id.
        """
        return MappingProxyType(self._documents)

    def get_chunk(self, document_id: int, position: int) -> Chunk | None:
        """Return the chunk at a document position.

        Parameters
        ----------
        document_id : int
            Document id to search.
        position : int
            Zero-based ``Chunk.document_position`` to resolve.

        Returns
        -------
        Chunk | None
            The matching chunk, or ``None`` when the position is absent.
        """
        document_chunks = self._corpus.get(document_id, {})
        for chunk in document_chunks.values():
            if chunk.document_position == position:
                return chunk
        return None

    def document_payload(self) -> List[DocumentSummary]:
        """Return one structured summary entry per known document.

        Entries are sorted by document id and carry the raw document name
        (``None`` when the document is missing), chunk count and highest page
        number (``0`` when the chunks have no pages).

        Returns
        -------
        List[DocumentSummary]
            The document summaries in ascending document-id order.
        """
        document_ids = sorted(set(self._documents) | set(self._corpus))
        payload: List[DocumentSummary] = []
        for document_id in document_ids:
            document = self._documents.get(document_id)
            name = getattr(document, DOCUMENT_NAME, None)
            document_chunks = list(self._corpus.get(document_id, {}).values())
            max_page = 0
            for chunk in document_chunks:
                if chunk.page is None:
                    continue
                if chunk.page > max_page:
                    max_page = chunk.page
            payload.append(
                {
                    DOCUMENT_ID: document_id,
                    DOCUMENT_NAME: name,
                    DOCUMENT_CHUNKS: len(document_chunks),
                    DOCUMENT_PAGES: max_page,
                }
            )
        return payload
