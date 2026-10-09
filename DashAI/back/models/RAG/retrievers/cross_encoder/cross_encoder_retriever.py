from abc import ABC, abstractmethod
from typing import List, Tuple

import numpy as np
from scipy.special import expit

from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.exceptions import (
    RAGRetrieverEmptyChildrenError,
    RAGRetrieverError,
)
from DashAI.back.models.RAG.retrievers.composite.composite_retriever import (
    CompositeRetriever,
)


class CrossEncoderRetriever(CompositeRetriever, ABC):
    """Abstract base for cross-encoder re-rankers.

    A cross-encoder processes (query, document) pairs jointly through a
    single transformer forward pass, producing a relevance score per pair.
    Because scoring every chunk in the corpus is expensive, cross-encoders
    are used as *re-rankers*: a fast child retriever (BM25, bi-encoder)
    fetches a candidate set, and the cross-encoder re-scores and re-orders it.

    Responsibility split between the ranker and the reranker:

    - **Ranker (child retriever):** decides how many candidates are fetched.
      This is configured on the child itself (its own ``top_k``).
    - **Reranker (this class):** re-scores the retrieved candidates and
      returns the top ``top_k`` of them. It has no ``retrieval_factor`` or
      any other knob that expands the candidate set.

    Subclasses must implement :meth:`_cross_score` to return relevance
    scores for a list of candidate chunks.  Higher scores indicate higher
    relevance.
    """

    DISPLAY_NAME: str = "Cross-Encoder Retriever"
    DESCRIPTION: str = (
        "Abstract re-ranker that uses a cross-encoder model to re-score "
        "candidates retrieved by a child retriever."
    )

    def __init__(self, **kwargs):
        """Initialize the cross-encoder retriever.

        Pops ``top_k`` from *kwargs* so that concrete subclasses can rely
        on ``self._top_k``.

        Args:
            **kwargs: Must contain ``children`` (exactly one child) and
                ``top_k``.
        """
        super().__init__(**kwargs)
        self._top_k: int = self.params.pop("top_k")

    @property
    def retrieval_top_k(self) -> int:
        """Return the final number of chunks after re-ranking.

        Returns:
            The configured ``top_k`` value.
        """
        return self._top_k

    def save(self, filename: str = "") -> None:
        """Persist the cross-encoder retriever's state.

        Cross-encoder models are downloaded on demand and have no
        persisted state, so saving is not supported by the base class.

        Args:
            filename: Optional filename override. Ignored.

        Raises:
            NotImplementedError: Always. Subclasses that need to persist
                additional state must override this method.
        """
        raise NotImplementedError(
            f"{type(self).__name__} has no persisted state to save: "
            "cross-encoder models are downloaded on demand. Subclasses "
            "must override save() if they need to persist state."
        )

    def load(self, filename: str = "") -> None:
        """Initialize the cross-encoder model.

        Cross-encoder models are downloaded on demand and have no
        persisted state, so the base class cannot load anything from
        disk.

        Args:
            filename: Optional filename override. Ignored.

        Raises:
            NotImplementedError: Always. Subclasses must override this
                method to initialize the model.
        """
        raise NotImplementedError(
            f"{type(self).__name__} cannot be loaded from disk: "
            "cross-encoder models are downloaded on demand. Subclasses "
            "must override load() to initialize the model."
        )

    @abstractmethod
    def _cross_score(self, query: str, chunks: List[Chunk]) -> List[float]:
        """Score candidate chunks with the cross-encoder model.

        Args:
            query: The search query string.
            chunks: Candidate chunks to score (already ordered by the
                child retriever).

        Returns:
            A list of relevance scores in the same order as *chunks*.
            Higher values indicate higher relevance.
        """
        raise NotImplementedError

    def retrieve(self, query: str, top_k: int | None = None, **kwargs) -> List[Chunk]:
        """Retrieve and re-rank chunks using the cross-encoder.

        Fetches a candidate set from the single child retriever (whose own
        configuration determines the number of candidates), then re-ranks
        them with the cross-encoder model.

        Args:
            query: The search query string.
            top_k: Optional override for the final number of chunks to
                return. When ``None``, the configured ``top_k`` of this
                :class:`CrossEncoderRetriever` is used (the default final
                K selected by the reranker).
            **kwargs: Additional retrieval parameters.

        Returns:
            A list of :class:`Chunk` instances re-ranked by cross-encoder
            relevance (up to ``top_k`` items). When the candidate count
            does not exceed the effective top-k, the chunks are returned
            in child order without re-scoring.

        Raises:
            RAGRetrieverEmptyChildrenError: If no child retriever is
                configured.
            RAGRetrieverError: If ``top_k`` is not an integer >= 1.
        """
        if not self._children:
            raise RAGRetrieverEmptyChildrenError(
                f"{type(self).__name__} requires exactly one child retriever."
            )
        child = self._children[0]
        effective_k = top_k if top_k is not None else self._top_k
        if not isinstance(effective_k, int) or effective_k < 1:
            raise RAGRetrieverError(
                f"top_k must be an integer >= 1, got {effective_k!r}."
            )
        candidates = child.retrieve(query)

        if len(candidates) <= effective_k:
            return candidates

        scores = self._cross_score(query, candidates)
        scored = list(zip(candidates, scores, strict=True))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, _ in scored[:effective_k]]

    def score_chunks(self, chunk_ids: List[int], query: str) -> List[Tuple[int, float]]:
        """Score a set of chunk IDs against the query with the cross-encoder.

        Resolves the requested chunk IDs through the injected ``chunks``
        mapping, scores the corresponding chunks jointly with the query,
        and converts each raw logit to a distance in ``[0, 1]``
        (``1 - sigmoid(logit)``) where lower means more relevant.

        Args:
            chunk_ids: List of chunk IDs to score.
            query: The search query string.

        Returns:
            A list of ``(chunk_id, distance)`` tuples sorted ascending
            by distance (lower is more relevant).

        Raises:
            RAGRetrieverError: If the infrastructure has not been
                injected.
        """
        chunks = getattr(self, "chunks", None)
        if chunks is None:
            raise RAGRetrieverError(
                "Cross-encoder infrastructure not injected. "
                "Call inject_infra() before score_chunks()."
            )
        chunk_map = {}
        for doc_chunks in chunks.values():
            for chunk in doc_chunks.values():
                chunk_map[chunk.id] = chunk

        valid = []
        for cid in chunk_ids:
            if cid in chunk_map:
                valid.append((cid, chunk_map[cid]))
        if not valid:
            return []

        scores = self._cross_score(query, [chunk for _, chunk in valid])
        distances = [1.0 - float(expit(score)) for score in scores]
        scored = list(zip([cid for cid, _ in valid], distances, strict=True))
        scored.sort(key=lambda x: x[1])
        return scored

    def get_chunk_vectors(self, chunk_ids: List[int]) -> np.ndarray:
        """Return chunk vectors from the child retriever.

        Delegates to the child retriever so this cross-encoder can be
        used as a child of an :class:`MMRRerankerRetriever`.

        Args:
            chunk_ids: List of chunk IDs whose vectors are needed.

        Returns:
            A 2D numpy array of chunk vectors from the child retriever.

        Raises:
            RAGRetrieverEmptyChildrenError: If no child retriever is
                configured.
            RAGRetrieverError: If the child retriever does not implement
                :meth:`get_chunk_vectors`.
        """
        if not self._children:
            raise RAGRetrieverEmptyChildrenError(
                f"{type(self).__name__} requires exactly one child retriever."
            )
        child = self._children[0]
        get_vectors = getattr(child, "get_chunk_vectors", None)
        if get_vectors is None:
            raise RAGRetrieverError(
                f"Child retriever {type(child).__name__} does not support "
                "get_chunk_vectors()."
            )
        return get_vectors(chunk_ids)

    def init_model(self) -> None:
        """Initialize the model by loading it.

        Delegates to :meth:`load` so the ``init_model() -> retrieve()``
        lifecycle pattern used elsewhere works.

        Raises:
            NotImplementedError: If the concrete subclass has not
                overridden :meth:`load`.
        """
        self.load()
