import logging
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    float_field,
    int_field,
    list_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.exceptions import RAGRetrieverError
from DashAI.back.models.RAG.retrievers.composite.composite_retriever import (
    CompositeRetriever,
)

log = logging.getLogger(__name__)


class MMRRerankerRetrieverSchema(BaseSchema):
    """Schema for :class:`MMRRerankerRetriever`.

    Attributes:
        mmr_lambda: Trade-off between relevance and diversity.
        top_k: Final number of chunks to select. The candidate set size is
            determined by the child retriever's own ``top_k``; the reranker
            only selects ``top_k`` of them.
        children: Exactly one child retriever whose results are re-ranked.
    """

    mmr_lambda: schema_field(
        float_field(ge=0.0, le=1.0),
        placeholder=0.5,
        description=MultilingualString(
            en="Trade-off between relevance (1.0) and diversity (0.0).",
            es="Compromiso entre relevancia (1.0) y diversidad (0.0).",
            pt="Compromisso entre relevância (1.0) e diversidade (0.0).",
            de="Abwägung zwischen Relevanz (1.0) und Diversität (0.0).",
            zh="相关性与多样性之间的权衡（1.0 相关性，0.0 多样性）。",
        ),
    )  # type: ignore

    top_k: schema_field(
        int_field(gt=0),
        placeholder=5,
        description=MultilingualString(
            en="Final number of chunks to select. The candidate set size "
            "is determined by the child retriever's own top_k.",
            es="Número final de fragmentos a seleccionar. El tamaño del "
            "conjunto candidato lo define el top_k propio del recuperador hijo.",
            pt="Número final de fragmentos a selecionar. O tamanho do "
            "conjunto candidato é definido pelo top_k do próprio recuperador filho.",
            de="Endgültige Anzahl der auszuwählenden Chunks. Die Größe des "
            "Kandidatensatzes wird durch den eigenen top_k des Kind-Retrievers "
            "bestimmt.",
            zh="最终要选择的块数量。候选集大小由子检索器自身的 top_k 决定。",
        ),
    )  # type: ignore

    children: schema_field(
        list_field(component_field(parent="RetrieverModel"), min_items=1, max_items=1),
        placeholder=[],
        description=MultilingualString(
            en="The child retriever whose results will be re-ranked.",
            es="El recuperador hijo cuyos resultados serán reordenados.",
            pt="O recuperador filho cujos resultados serão reordenados.",
            de="Der Kind-Retriever, dessen Ergebnisse neu bewertet werden.",
            zh="其结果将被重新排序的子检索器。",
        ),
    )  # type: ignore


class MMRRerankerRetriever(CompositeRetriever):
    """Re-ranks retrieval results using Maximum Marginal Relevance for diversity.

    The child retriever (the ranker) determines the candidate set via its
    own configuration; this reranker selects ``top_k`` chunks for
    diversity by balancing relevance and similarity among them.
    """

    SCHEMA = MMRRerankerRetrieverSchema
    DISPLAY_NAME: str = MultilingualString(
        en="MMR Reranker",
        es="Reordenador MMR",
        pt="Reordenador MMR",
        de="MMR-Reranker",
        zh="MMR 重排序器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Re-ranks retrieval results using Maximum Marginal Relevance for diversity.",
        es="Reordena resultados de recuperación usando Maximum Marginal Relevance "
        "para diversidad.",
        pt="Reordena resultados de recuperação usando Maximum Marginal Relevance "
        "para diversidade.",
        de="Bewertet Abrufergebnisse mithilfe von Maximum Marginal Relevance "
        "für Diversität neu.",
        zh="使用最大边际相关性（MMR）对检索结果重新排序以提升多样性。",
    )

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return UI metadata including the declarative operation summary."""
        return {
            **super().get_metadata(),
            "operation_summary": {
                "kind": "rerank",
                "fields": [
                    {"param": "mmr_lambda", "label": "Lambda"},
                    {"param": "top_k", "label": "Top K"},
                ],
            },
        }

    def __init__(self, **kwargs):
        """Initialize the MMR reranker.

        Args:
            **kwargs: Must contain ``mmr_lambda``, ``top_k``, and
                ``children`` (exactly one child).
        """
        super().__init__(**kwargs)
        self.mmr_lambda = self.params.pop("mmr_lambda")
        self._top_k = self.params.pop("top_k")

    @property
    def retrieval_top_k(self) -> int:
        """Return the final number of chunks selected.

        Returns:
            The value of ``top_k``.
        """
        return self._top_k

    def retrieve(self, query: str, **kwargs) -> List[Chunk]:
        """Retrieve and re-rank chunks using MMR diversity.

        Fetches the candidate set from the child retriever (whose own
        configuration determines the candidate count), computes pairwise
        cosine similarity among the candidates, then selects a diverse
        subset via the MMR algorithm.

        Args:
            query: The search query string.
            **kwargs: Additional retrieval parameters.

        Returns:
            A list of :class:`Chunk` instances selected for relevance
            and diversity.

        Raises:
            RAGRetrieverError: If the child retriever raises while scoring
                the candidate chunks.
        """
        child = self._children[0]
        candidates = child.retrieve(query)
        if len(candidates) <= self._top_k:
            return candidates

        chunk_ids: List[int] = [c.id for c in candidates]
        scored: List[Tuple[int, float]] = child.score_chunks(chunk_ids, query)
        id_to_dist = dict(scored)

        ordered = []
        for c in candidates:
            if c.id in id_to_dist:
                ordered.append(c)
        if len(ordered) <= self._top_k:
            return ordered[: self._top_k]

        relevance = np.array([1.0 - id_to_dist[c.id] for c in ordered])
        ordered_ids: List[int] = [c.id for c in ordered]
        try:
            vectors = child.get_chunk_vectors(ordered_ids)
        except (ValueError, RAGRetrieverError):
            return ordered[: self._top_k]

        if len(vectors) != len(ordered):
            log.warning(
                "MMRRerankerRetriever: vector count (%d) != ordered chunk count (%d). "
                "Falling back to top-k without MMR.",
                len(vectors),
                len(ordered),
            )
            return ordered[: self._top_k]

        pairwise = cosine_similarity(vectors)
        selected = self._mmr_select(relevance, pairwise)
        return [ordered[i] for i in selected]

    def score_chunks(self, chunk_ids: List[int], query: str) -> List[Tuple[int, float]]:
        """Score chunks by delegating to the child retriever.

        Args:
            chunk_ids: List of chunk IDs to score.
            query: The search query string.

        Returns:
            A list of ``(chunk_id, distance)`` tuples from the child.
        """
        child = self._children[0]
        return child.score_chunks(chunk_ids, query)

    def _mmr_select(
        self,
        relevance: np.ndarray,
        pairwise: np.ndarray,
    ) -> List[int]:
        """Select indices using Maximum Marginal Relevance.

        Greedily picks the next candidate that maximises:
        ``lambda * relevance(c) - (1 - lambda) * max_similarity(c, selected)``

        Args:
            relevance: Relevance scores for all candidates (shape ``(n,)``).
            pairwise: Pairwise cosine similarity matrix (shape ``(n, n)``).

        Returns:
            List of selected indices (up to ``self._top_k``).
        """
        n = len(relevance)
        best = int(np.argmax(relevance))
        selected = [best]
        remaining = [i for i in range(n) if i != best]

        while len(selected) < self._top_k and remaining:
            scores = np.empty(len(remaining))
            for j, cand in enumerate(remaining):
                max_pair = max(pairwise[cand][s] for s in selected)
                scores[j] = (
                    self.mmr_lambda * relevance[cand]
                    - (1.0 - self.mmr_lambda) * max_pair
                )
            best_idx = int(np.argmax(scores))
            selected.append(remaining[best_idx])
            remaining.pop(best_idx)

        return selected
