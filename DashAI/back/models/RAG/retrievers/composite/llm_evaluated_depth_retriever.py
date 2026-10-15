"""LLM-evaluated depth retriever.

Takes exactly one child retriever and delegates retrieval to it. After each
round (except the last) the retriever asks its language model whether the
accumulated pool is sufficient; when it is not, the model also supplies a larger
retrieval size ``top_k`` that drives the next delegation. The retriever is
*blind* to its child's identity: the prompt never names the child beyond the
generic request, it just asks for a bigger retrieval.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    int_field,
    list_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.retrievers.composite.evaluation_output import (
    require_for_depth,
)
from DashAI.back.models.RAG.retrievers.composite.llm_evaluated_retriever import (
    LLMEvaluatedRetriever,
)
from DashAI.back.models.RAG.retrievers.exceptions import CompositeValidationError


class LLMEvaluatedDepthRetrieverSchema(BaseSchema):
    """Schema for :class:`LLMEvaluatedDepthRetriever`.

    Attributes:
        children: Exactly one child retriever that is delegated to.
        max_chunks: Maximum number of chunks the pool may hold.
        max_iters: Maximum number of retrieval rounds (judgements = iters - 1).
        prompt: The retrieval-sufficiency prompt component.
        llm_model: The text-to-text model that judges sufficiency.
    """

    children: schema_field(
        list_field(component_field(parent="BaseRetriever"), min_items=1, max_items=1),
        placeholder=[],
        description=MultilingualString(
            en="The single child retriever that is delegated to. The retriever"
            " is blind to its identity: the prompt never names it.",
            es="El único recuperador hijo al que se delega. El recuperador es"
            " ciego a su identidad: el prompt nunca lo nombra.",
            pt="O único recuperador filho ao qual se delega. O recuperador é"
            " cego à sua identidade: o prompt nunca o nomeia.",
            de="Der einzige Kind-Retriever, an den delegiert wird. Der"
            " Retriever ist blind gegenüber seiner Identität: der Prompt nennt"
            " ihn nie.",
            zh="被委派的唯一子检索器。该检索器对其身份不可见：提示词从不提及它。",
        ),
    )  # type: ignore

    max_chunks: schema_field(
        int_field(gt=0),
        placeholder=10,
        description=MultilingualString(
            en="Maximum number of chunks the accumulated pool may hold.",
            es="Número máximo de fragmentos que puede contener el conjunto acumulado.",
            pt="Número máximo de trechos que o conjunto acumulado pode conter.",
            de="Maximale Anzahl von Fragmenten im gesammelten Pool.",
            zh="累积池可容纳的最大片段数量。",
        ),
    )  # type: ignore

    max_iters: schema_field(
        int_field(gt=0),
        placeholder=3,
        description=MultilingualString(
            en="Maximum number of retrieval rounds. The final round is not"
            " judged, so there are at most this many minus one LLM calls.",
            es="Número máximo de rondas de recuperación. La ronda final no se"
            " evalúa, por lo que hay como máximo este número menos una llamadas"
            " al LLM.",
            pt="Número máximo de rodadas de recuperação. A rodada final não é"
            " avaliada, portanto há no máximo esse número menos uma chamadas ao"
            " LLM.",
            de="Maximale Anzahl von Abrufrunden. Die letzte Runde wird nicht"
            " bewertet, also höchstens diese Zahl minus eins LLM-Aufrufe.",
            zh="最大检索轮数。最后一轮不评估，因此最多有该数量减一次 LLM 调用。",
        ),
    )  # type: ignore

    prompt: schema_field(
        component_field(parent="RetrievalSufficiencyPrompt"),
        placeholder={"component": "DefaultRetrievalSufficiencyPrompt", "params": {}},
        description=MultilingualString(
            en="The prompt used to judge whether the retrieved chunks suffice.",
            es="El prompt usado para juzgar si los fragmentos recuperados son"
            " suficientes.",
            pt="O prompt usado para julgar se os trechos recuperados são suficientes.",
            de="Der Prompt, um zu beurteilen, ob die abgerufenen Fragmente ausreichen.",
            zh="用于判断已检索片段是否充分的提示词。",
        ),
    )  # type: ignore

    llm_model: schema_field(
        component_field(parent="TextToTextGenerationTaskModel"),
        placeholder={"component": "", "params": {}},
        description=MultilingualString(
            en="The language model that judges retrieval sufficiency.",
            es="El modelo de lenguaje que juzga la suficiencia de la recuperación.",
            pt="O modelo de linguagem que julga a suficiência da recuperação.",
            de="Das Sprachmodell, das die Abrufsuffizienz beurteilt.",
            zh="判断检索充分性的语言模型。",
        ),
    )  # type: ignore


class LLMEvaluatedDepthRetriever(LLMEvaluatedRetriever):
    """Iteratively deepens a single child's retrieval under LLM supervision.

    Round 1 delegates to the child with no size override (its own configuration
    drives). After each round but the last, the pool is judged; an insufficient
    verdict's ``top_k`` becomes the next delegation's retrieval-size hint,
    clamped to the remaining budget, with a progress guarantee that turns a
    zero-progress request into the smallest one that can add a chunk.
    """

    SCHEMA = LLMEvaluatedDepthRetrieverSchema
    DISPLAY_NAME: str = MultilingualString(
        en="LLM-Evaluated Depth Retriever",
        es="Recuperador de Profundidad Evaluado por LLM",
        pt="Retriever de Profundidade Avaliado por LLM",
        de="LLM-bewerteter Tiefen-Retriever",
        zh="LLM 评估深度检索器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Delegates to one child retriever and iteratively deepens it: an LLM"
        " decides whether the pool suffices and how many chunks to retrieve"
        " next.",
        es="Delega en un recuperador hijo y lo profundiza iterativamente: un"
        " LLM decide si el conjunto es suficiente y cuántos fragmentos"
        " recuperar después.",
        pt="Delega a um recuperador filho e aprofunda iterativamente: um LLM"
        " decide se o conjunto é suficiente e quantos trechos recuperar em"
        " seguida.",
        de="Delegiert an einen Kind-Retriever und vertieft ihn iterativ: ein"
        " LLM entscheidet, ob der Pool ausreicht und wie viele Fragmente als"
        " Nächstes abzurufen sind.",
        zh=(
            "委派给一个子检索器并迭代加深：由 LLM 决定池是否充分"
            "以及下一步检索多少片段。"
        ),
    )

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the depth retriever and enforce a single child.

        Parameters
        ----------
        **kwargs
            The common LLM-evaluated retriever parameters.

        Raises
        ------
        CompositeValidationError
            If the retriever is not configured with exactly one child.
        """
        super().__init__(**kwargs)
        if len(self._children) != 1:
            raise CompositeValidationError(
                "LLMEvaluatedDepthRetriever requires exactly one child retriever, "
                f"got {len(self._children)}."
            )

    def retrieve(self, query: str, **kwargs: Any) -> Tuple[List[Chunk], Dict[str, Any]]:
        """Retrieve by delegating to the child and iteratively deepening.

        Parameters
        ----------
        query : str
            The search query string.
        **kwargs
            Unused; delegation sizes come from the LLM verdicts.

        Returns
        -------
        Tuple[List[Chunk], Dict[str, Any]]
            The final pool (at most ``max_chunks`` chunks) and this retriever's
            trace node, whose ``children`` holds every delegated child node and
            whose ``rounds`` holds one summary per retrieval round.

        Raises
        ------
        RAGRetrieverEvaluationError
            If an insufficient verdict omits ``top_k`` or the model output is
            malformed.
        """
        child = self._children[0]
        pool: List[Chunk] = []
        child_nodes: List[Dict[str, Any]] = []
        rounds: List[Dict[str, Any]] = []
        requested_top_k: int | None = None

        for round_index in range(self.max_iters):
            new_chunks, node = self._delegate(child, query, requested_top_k)
            child_nodes.append(node)
            pool = self._cap_pool(self._merge_new_chunks(pool, new_chunks))
            entry: Dict[str, Any] = {
                "round": round_index + 1,
                "name": type(child).__name__,
                "requested_top_k": requested_top_k,
                "returned": len(new_chunks),
                "verdict": None,
            }
            rounds.append(entry)

            remaining = self.max_chunks - len(pool)
            if remaining <= 0 or round_index == self.max_iters - 1:
                break

            verdict = self._evaluate(query, pool, include_children_catalog=False)
            if verdict[self._SUFFICIENT]:
                entry["verdict"] = True
                break
            entry["verdict"] = False
            requested_top_k = self._next_top_k(verdict, len(pool))

        return pool, self._build_trace(pool, child_nodes, rounds)

    def _next_top_k(self, verdict: Dict[str, Any], pool_size: int) -> int:
        """Return the next delegation's retrieval-size hint.

        The model's requested size is capped by ``max_chunks`` (a per-call
        size, not a pool increment). When it would not add a chunk — e.g. a
        deterministic child that already returned that many — it is raised to
        the smallest size that can, so an unhelpful verdict cannot produce a
        zero-progress round. The pool cap itself is enforced by the merge/cap
        step, not by shrinking the request: a request below the current pool
        size would make a deterministic child return its same prefix again and
        stall until ``max_iters``.

        Parameters
        ----------
        verdict : Dict[str, Any]
            An insufficient verdict carrying ``top_k``.
        pool_size : int
            Current number of pooled chunks.

        Returns
        -------
        int
            The retrieval-size hint for the next delegation (at least one
            chunk more than the pool currently holds, when possible).

        Raises
        ------
        RAGRetrieverEvaluationError
            If the verdict lacks a positive ``top_k``.
        """
        size = min(require_for_depth(verdict), self.max_chunks)
        if size <= pool_size:
            size = min(pool_size + 1, self.max_chunks)
        return size

    def score_chunks(self, chunk_ids: List[int], query: str) -> List[Tuple[int, float]]:
        """Score chunks by delegating to the single child.

        Parameters
        ----------
        chunk_ids : List[int]
            List of chunk IDs to score.
        query : str
            The search query string.

        Returns
        -------
        List[Tuple[int, float]]
            A list of ``(chunk_id, distance)`` tuples from the child.
        """
        return self._children[0].score_chunks(chunk_ids, query)
