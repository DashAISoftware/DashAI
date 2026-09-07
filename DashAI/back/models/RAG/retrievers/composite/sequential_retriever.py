from typing import Any, Dict, List, Tuple

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    list_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.exceptions import RAGRetrieverError
from DashAI.back.models.RAG.retrievers.composite.composite_retriever import (
    CompositeRetriever,
)
from DashAI.back.models.RAG.retrievers.exceptions import CompositeValidationError


class SequentialRetrieverSchema(BaseSchema):
    """Schema for :class:`SequentialRetriever`.

    Attributes:
        children: Ordered list of at least 2 child retrievers.
    """

    children: schema_field(
        list_field(component_field(parent="RetrieverModel"), min_items=2),
        placeholder=[],
        description=MultilingualString(
            en="Ordered list of child retrievers. The first child retrieves"
            " broadly; each subsequent child re-ranks and tightens the"
            " results.",
            es="Lista ordenada de recuperadores hijos. El primero recupera"
            " ampliamente; cada hijo subsiguiente reordena y ajusta los"
            " resultados.",
            pt="Lista ordenada de recuperadores filhos. O primeiro recupera"
            " amplamente; cada filho subsequente reordena e ajusta os"
            " resultados.",
            de="Geordnete Liste der Kind-Retriever. Der erste ruft breit ab;"
            " jedes nachfolgende Kind bewertet neu und verengt die"
            " Ergebnisse.",
            zh="子检索器的有序列表。第一个检索器广泛检索；"
            "每个后续子检索器重新排序并收窄结果。",
        ),
    )  # type: ignore


class SequentialRetriever(CompositeRetriever):
    """Queries multiple retrievers in sequence, re-ranking at each step.

    Each stage narrows the result set by requiring strictly decreasing
    ``top_k`` values.  The last child is the authoritative scorer.
    """

    SCHEMA = SequentialRetrieverSchema
    DISPLAY_NAME: str = MultilingualString(
        en="Sequential Retriever",
        es="Recuperador Secuencial",
        pt="Recuperador Sequencial",
        de="Sequentieller Retriever",
        zh="顺序检索器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Queries multiple retrievers in sequence, re-ranking at each step.",
        es="Consulta múltiples recuperadores en secuencia, reordenando en cada paso.",
        pt="Consulta vários recuperadores em sequência, reordenando em cada etapa.",
        de="Fragt mehrere Retriever nacheinander ab und bewertet bei jedem"
        " Schritt neu.",
        zh="按顺序查询多个检索器，并在每一步重新排序。",
    )

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Return UI metadata including the declarative operation summary."""
        return {
            **super().get_metadata(),
            "operation_summary": {"kind": "fusion", "fields": []},
        }

    def __init__(self, **kwargs):
        """Initialize and validate the sequential cascade.

        Args:
            **kwargs: Must contain a ``children`` key with at least 2
                :class:`RetrieverModel` instances.

        Raises:
            CompositeValidationError: If ``top_k`` values are not strictly
                decreasing.
        """
        super().__init__(**kwargs)
        self._validate()

    def _validate(self) -> None:
        """Validate cascade constraints on children.

        Checks that ``top_k`` values are strictly decreasing so each
        stage narrows the result set.  No type restrictions — any
        ``RetrieverModel`` subclass is allowed as a child (Composite
        pattern).

        Raises:
            CompositeValidationError: If child ``top_k`` values are not
                strictly decreasing.
        """
        children = getattr(self, "_children", [])
        if len(children) < 2:
            return

        children_k = [c.retrieval_top_k for c in children]
        for i in range(1, len(children_k)):
            if children_k[i] >= children_k[i - 1]:
                raise CompositeValidationError(
                    f"Cascade requires strictly decreasing top_k. "
                    f"Child {i} top_k={children_k[i]} >= "
                    f"child {i - 1} top_k={children_k[i - 1]}"
                )

    def retrieve(self, query, **kwargs) -> List[Chunk]:
        """Retrieve chunks through the sequential cascade.

        The first child performs a broad retrieval; each subsequent child
        re-ranks the results and narrows to its ``top_k``.

        Args:
            query: The search query string.
            **kwargs: Additional retrieval parameters forwarded to the
                first child.

        Returns:
            A list of :class:`Chunk` instances after all stages.

        Raises:
            RAGRetrieverError: If any chunk has a ``None`` ID.
        """
        first = self._children[0]
        results = first.retrieve(query, **kwargs)

        for c in results:
            if c.id is None:
                raise RAGRetrieverError(
                    "Chunk with None id encountered in SequentialRetriever. "
                    "Chunks must be persisted before sequential retrieval."
                )

        for child in self._children[1:]:
            chunk_ids = [c.id for c in results]
            scored = child.score_chunks(chunk_ids, query)
            scored = scored[: child.retrieval_top_k]
            id_to_chunk = {c.id: c for c in results}
            results = [id_to_chunk[cid] for cid, _ in scored]

        return results

    def score_chunks(self, chunk_ids: List[int], query: str) -> List[Tuple[int, float]]:
        """Score chunks by delegating to the last child in the cascade.

        The last child produces the final ranking, so it is the
        authoritative scorer.

        Args:
            chunk_ids: List of chunk IDs to score.
            query: The search query string.

        Returns:
            A list of ``(chunk_id, distance)`` tuples sorted by distance.
        """
        if not self._children:
            return []
        return self._children[-1].score_chunks(chunk_ids, query)

    @property
    def retrieval_top_k(self) -> int:
        """Return the ``top_k`` of the last (most restrictive) child.

        Returns:
            The ``top_k`` of the last child, or ``1`` if there are no
            children.
        """
        if self._children:
            return self._children[-1].retrieval_top_k
        return 1
