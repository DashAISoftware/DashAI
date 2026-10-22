"""LLM-evaluated depth retriever.

Takes exactly one child retriever and delegates retrieval to it. After each
round (except the last) the retriever asks its language model whether the
accumulated pool is sufficient; when it is not, the model also supplies a larger
retrieval size ``top_k`` that drives the next delegation. The retriever is
*blind* to its child's identity: the prompt never names the child beyond the
generic request, it just asks for a bigger retrieval.

The schema placeholders come from :mod:`DashAI.back.models.RAG.RAG_defaults`:
``children`` seeds the default hybrid retriever and ``llm_model`` seeds the
default RAG function-calling LLM. Both are ordinary, fully modifiable values.
"""

from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Tuple

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    int_field,
    list_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.RAG_constants import (
    RAG_PROGRESS_JUSTIFICATION_KEY,
    RAG_PROGRESS_MESSAGE_KEY,
)
from DashAI.back.models.RAG.RAG_defaults import (
    DEFAULT_FUNCTION_CALL_MAX_TRIALS,
    DEFAULT_MAX_CHUNKS,
    DEFAULT_MAX_ITERS,
    MAX_FUNCTION_CALL_TRIALS,
    default_function_calling_llm,
    default_hybrid_retriever,
    default_retrieval_sufficiency_prompt,
)
from DashAI.back.models.RAG.retrievers.composite.evaluation_output import (
    CALL_RETRIEVERS_KEY,
    DISCARD_KEY,
    REQUEST_CHUNKS_KEY,
    SUFFICIENT_KEY,
    validate_call_indices,
)
from DashAI.back.models.RAG.retrievers.composite.llm_evaluated_retriever import (
    LLMEvaluatedRetriever,
)
from DashAI.back.models.RAG.retrievers.composite.retrieval_context import (
    RetrievalContext,
)
from DashAI.back.models.RAG.retrievers.composite.retrieval_pool import RetrievalPool
from DashAI.back.models.RAG.retrievers.exceptions import CompositeValidationError


class LLMEvaluatedDepthRetrieverSchema(BaseSchema):
    """Schema for :class:`LLMEvaluatedDepthRetriever`.

    Attributes:
        children: Exactly one child retriever that is delegated to. Defaults to
            the default hybrid retriever; the value is fully modifiable.
        max_chunks: Maximum number of chunks the pool may hold.
        max_iters: Maximum number of retrieval rounds (judgements = iters - 1).
        prompt: The retrieval-sufficiency prompt component.
        llm_model: The text-to-text model that judges sufficiency. Defaults to
            the default RAG function-calling LLM; the value is fully modifiable.
        function_call_max_trials: Maximum number of function-call attempts, the
            first call included.
    """

    children: schema_field(
        list_field(component_field(parent="BaseRetriever"), min_items=1, max_items=1),
        placeholder=[default_hybrid_retriever()],
        description=MultilingualString(
            en="The single child retriever that is delegated to. The retriever"
            " is blind to its identity: the prompt never names it. Defaults to"
            " the default hybrid retriever; you can change it.",
            es="El único recuperador hijo al que se delega. El recuperador es"
            " ciego a su identidad: el prompt nunca lo nombra. Por defecto usa"
            " el recuperador híbrido predeterminado; puedes cambiarlo.",
            pt="O único recuperador filho ao qual se delega. O recuperador é"
            " cego à sua identidade: o prompt nunca o nomeia. Por padrão usa o"
            " recuperador híbrido padrão; você pode alterá-lo.",
            de="Der einzige Kind-Retriever, an den delegiert wird. Der"
            " Retriever ist blind gegenüber seiner Identität: der Prompt nennt"
            " ihn nie. Standardmäßig wird der hybride Standard-Retriever"
            " verwendet; er ist änderbar.",
            zh=(
                "被委派的唯一子检索器。该检索器对其身份不可见：提示词从不提及它。"
                "默认为默认混合检索器，可随时修改。"
            ),
        ),
    )  # type: ignore

    max_chunks: schema_field(
        int_field(gt=0),
        placeholder=DEFAULT_MAX_CHUNKS,
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
        placeholder=DEFAULT_MAX_ITERS,
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

    function_call_max_trials: schema_field(
        int_field(ge=1, le=MAX_FUNCTION_CALL_TRIALS, strict=True),
        placeholder=DEFAULT_FUNCTION_CALL_MAX_TRIALS,
        description=MultilingualString(
            en="Maximum number of function-call attempts, including the first."
            " When the model returns an unusable call or unparseable JSON"
            " arguments, the call is retried until this limit is reached."
            " Only applies to models with function calling.",
            es="Número máximo de intentos de llamada a funciones, incluido el"
            " primero. Cuando el modelo devuelve una llamada inutilizable o"
            " argumentos JSON no analizables, la llamada se reintenta hasta"
            " alcanzar este límite. Solo se aplica a modelos con llamada a"
            " funciones.",
            pt="Número máximo de tentativas de chamada de função, incluindo a"
            " primeira. Quando o modelo retorna uma chamada inutilizável ou"
            " argumentos JSON não analisáveis, a chamada é repetida até atingir"
            " esse limite. Aplica-se apenas a modelos com chamada de função.",
            de="Maximale Anzahl von Funktionsaufrufversuchen, einschließlich des"
            " ersten. Wenn das Modell einen unbrauchbaren Aufruf oder nicht"
            " analysierbare JSON-Argumente liefert, wird der Aufruf bis zu"
            " diesem Limit wiederholt. Gilt nur für Modelle mit"
            " Funktionsaufrufen.",
            zh="函数调用尝试的最大次数，包括首次调用。当模型返回不可用的调用"
            "或无法解析的 JSON 参数时，会重试调用直到达到此限制。仅适用于"
            "支持函数调用的模型。",
        ),
        alias=MultilingualString(
            en="Function call max trials",
            es="Máximo de intentos de llamada a funciones",
            pt="Máximo de tentativas de chamada de função",
            de="Max. Funktionsaufrufversuche",
            zh="函数调用最大尝试次数",
        ),
    ) = DEFAULT_FUNCTION_CALL_MAX_TRIALS  # type: ignore

    prompt: schema_field(
        component_field(parent="RetrievalSufficiencyPrompt"),
        placeholder=default_retrieval_sufficiency_prompt(),
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
        placeholder=default_function_calling_llm(),
        description=MultilingualString(
            en="The language model that judges retrieval sufficiency. Defaults"
            " to the default RAG function-calling LLM; you can change it.",
            es="El modelo de lenguaje que juzga la suficiencia de la"
            " recuperación. Por defecto usa el LLM de llamada a funciones RAG"
            " predeterminado; puedes cambiarlo.",
            pt="O modelo de linguagem que julga a suficiência da recuperação."
            " Por padrão usa o LLM de chamada de funções RAG padrão; você pode"
            " alterá-lo.",
            de="Das Sprachmodell, das die Abrufsuffizienz beurteilt."
            " Standardmäßig wird das RAG-Standard-LLM für Funktionsaufrufe"
            " verwendet; es ist änderbar.",
            zh=("判断检索充分性的语言模型。默认为默认 RAG 函数调用 LLM，可随时修改。"),
        ),
    )  # type: ignore


class LLMEvaluatedDepthRetriever(LLMEvaluatedRetriever):
    """Iteratively deepens a single child's retrieval under LLM supervision.

    Round 1 delegates to the child with no size override (its own configuration
    drives). After each round but the last, the pool is judged; an insufficient
    verdict's ``top_k`` becomes the next delegation's retrieval-size hint,
    clamped to the remaining budget, with a progress guarantee that turns a
    zero-progress request into the smallest one that can add a chunk.

    A composite child interprets that hint under its own contract. The default
    hybrid child keeps its configured budget and may therefore fill the pool
    before the first judgement; raise ``max_chunks`` or choose a child that
    honours the hint when deeper rounds are required.
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

    EXPECTED_FUNCTION: ClassVar[str] = "evaluate_retrieval_sufficiency"
    FUNCTION_DESCRIPTION: ClassVar[str] = (
        "Decide whether the retrieved chunks are sufficient to answer the user "
        "message. Use call_retrievers with 1-based retriever indices mapped to "
        "the number of chunks to retrieve from that retriever next (only index "
        "1 is valid here). Use request_chunks and discard to include or exclude "
        "specific chunk positions by document id. Requested and discarded chunks "
        "persist across rounds and can override each other (the last action "
        "wins)."
    )
    FUNCTION_PARAMETERS: ClassVar[Dict[str, Any]] = {
        "type": "object",
        "properties": {
            SUFFICIENT_KEY: {
                "type": "boolean",
                "description": (
                    "Whether the retrieved chunks suffice to answer the user message."
                ),
            },
            CALL_RETRIEVERS_KEY: {
                "type": "object",
                "additionalProperties": {"type": "integer", "minimum": 1},
                "description": (
                    "When insufficient, maps the 1-based retriever index (only "
                    "1 is valid) to the number of chunks to retrieve next."
                ),
            },
            REQUEST_CHUNKS_KEY: {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 0},
                },
                "description": (
                    "Maps document ids to chunk positions to include in the pool "
                    "even if no retriever returned them."
                ),
            },
            DISCARD_KEY: {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 0},
                },
                "description": (
                    "Maps document ids to chunk positions to exclude from the "
                    "pool even if a retriever returns them."
                ),
            },
            RAG_PROGRESS_MESSAGE_KEY: {
                "type": "string",
                "description": (
                    "Optional one short user-facing sentence in the prompt "
                    "language describing what you did."
                ),
            },
            RAG_PROGRESS_JUSTIFICATION_KEY: {
                "type": "string",
                "description": (
                    "Optional one short sentence in the prompt language "
                    "explaining why you did it."
                ),
            },
        },
        "required": [SUFFICIENT_KEY],
    }

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
            If a verdict is malformed or names an out-of-range retriever.
        """
        child = self._children[0]
        context = RetrievalContext.from_retriever(self)
        pool = RetrievalPool(self.max_chunks, context)
        child_nodes: List[Dict[str, Any]] = []
        rounds: List[Dict[str, Any]] = []
        requested_top_k: int | None = None
        max_requested = 0
        should_delegate = True

        for round_index in range(self.max_iters):
            delegating = should_delegate and pool.size() < self.max_chunks
            entry: Dict[str, Any] = {
                "round": round_index + 1,
                "name": type(child).__name__,
                "requested_top_k": requested_top_k if delegating else None,
                "returned": 0,
                "verdict": None,
                "call_retrievers": {},
                "request_chunks": {},
                "discard": {},
            }
            if delegating:
                new_chunks, node = self._delegate(child, query, requested_top_k)
                child_nodes.append(node)
                pool.add(new_chunks)
                # Largest size actually delegated. A child that ignores the
                # ``top_k`` hint cannot extend the loop beyond ``max_iters``.
                max_requested = max(max_requested, len(new_chunks))
                entry["returned"] = len(new_chunks)
            elif should_delegate:
                # The pool is already full; still evaluate so request/discard
                # actions can change its composition.
                should_delegate = False
                requested_top_k = None
            rounds.append(entry)

            if round_index == self.max_iters - 1:
                break

            verdict = self._evaluate(query, pool, context)
            calls = validate_call_indices(verdict.call_retrievers, 1)
            entry["verdict"] = verdict.sufficient
            entry["call_retrievers"] = dict(verdict.call_retrievers)
            entry["request_chunks"] = dict(verdict.request_chunks)
            entry["discard"] = dict(verdict.discard)
            if verdict.sufficient:
                # A sufficient verdict is terminal: chunk actions are not
                # applied and unknown positions are never resolved. Report the
                # verdict's narrative before leaving the loop.
                self._report_verdict_progress(verdict)
                self._record_round_narrative(entry, verdict)
                break

            self._apply_verdict_actions(pool, verdict)
            self._report_verdict_progress(verdict)
            self._record_round_narrative(entry, verdict)
            if 1 in calls:
                requested_top_k = self._next_delegation_size(
                    calls, max_requested, pool.discarded_count()
                )
                should_delegate = True
            else:
                requested_top_k = None
                should_delegate = False

        pool_chunks = pool.materialize()
        return pool_chunks, self._build_trace(pool_chunks, child_nodes, rounds)

    def _next_delegation_size(
        self, calls: Dict[int, int], max_requested: int, discarded_count: int
    ) -> int:
        """Return the next delegation size.

        The model's requested size is capped by ``max_chunks`` plus the number
        of discarded slots. Discarded chunks still occupy the child's prefix,
        so replacing one requires fetching past the pool cap; the pool itself
        keeps materializing at most ``max_chunks`` chunks. When the request
        would not exceed the largest size already delegated, it is raised to the
        smallest size that can add a chunk.
        """
        call_limit = self.max_chunks + discarded_count
        size = min(calls[1], call_limit)
        if size > max_requested:
            return size
        return min(max_requested + 1, call_limit)

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
