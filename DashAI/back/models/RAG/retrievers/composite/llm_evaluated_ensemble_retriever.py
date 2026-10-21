"""LLM-evaluated ensemble retriever.

Takes two or more child retrievers. The language model is shown a catalog of the
children (index, class name and configured ``top_k``), chooses which children to
consult each round, and supplies an explicit per-child ``top_k`` for every call.
Sufficiency is judged over the accumulated pool.

The schema placeholders come from :mod:`DashAI.back.models.RAG.RAG_defaults`:
``children`` seeds the default semantic and keyword retrievers and
``llm_model`` seeds the default RAG function-calling LLM. Both are ordinary,
fully modifiable values.
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
from DashAI.back.models.RAG.exceptions.retriever import (
    RAGRetrieverEvaluationError,
)
from DashAI.back.models.RAG.RAG_defaults import (
    DEFAULT_MAX_CHUNKS,
    DEFAULT_MAX_ITERS,
    default_function_calling_llm,
    default_keyword_retriever,
    default_retrieval_sufficiency_prompt,
    default_semantic_retriever,
)
from DashAI.back.models.RAG.retrievers.composite.evaluation_output import (
    CALL_RETRIEVERS_KEY,
    DISCARD_KEY,
    REQUEST_CHUNKS_KEY,
    SUFFICIENT_KEY,
    require_planning_calls,
    validate_call_indices,
)
from DashAI.back.models.RAG.retrievers.composite.llm_evaluated_retriever import (
    LLMEvaluatedRetriever,
)
from DashAI.back.models.RAG.retrievers.composite.retrieval_context import (
    RetrievalContext,
)
from DashAI.back.models.RAG.retrievers.composite.retrieval_pool import RetrievalPool


class LLMEvaluatedEnsembleRetrieverSchema(BaseSchema):
    """Schema for :class:`LLMEvaluatedEnsembleRetriever`.

    Attributes:
        children: At least two child retrievers, from which the LLM chooses.
            Defaults to the default semantic and keyword retrievers; the value
            is fully modifiable.
        max_chunks: Maximum number of chunks the pool may hold.
        max_iters: Maximum number of retrieval rounds.
        prompt: The retrieval-sufficiency prompt component.
        llm_model: The text-to-text model that chooses children and judges.
            Defaults to the default RAG function-calling LLM; the value is
            fully modifiable.
    """

    children: schema_field(
        list_field(component_field(parent="BaseRetriever"), min_items=2),
        placeholder=[default_semantic_retriever(), default_keyword_retriever()],
        description=MultilingualString(
            en="Child retrievers the LLM may consult. A catalog of their"
            " indices, names and top_k values is rendered into the prompt."
            " Defaults to the default semantic and keyword retrievers; you can"
            " change them.",
            es="Recuperadores hijos que el LLM puede consultar. Se renderiza un"
            " catálogo de sus índices, nombres y valores top_k en el prompt."
            " Por defecto usa los recuperadores semántico y de palabras clave"
            " predeterminados; puedes cambiarlos.",
            pt="Recuperadores filhos que o LLM pode consultar. Um catálogo de"
            " seus índices, nomes e valores top_k é renderizado no prompt."
            " Por padrão usa os recuperadores semântico e de palavras-chave"
            " padrão; você pode alterá-los.",
            de="Kind-Retriever, die das LLM konsultieren darf. Ein Katalog ihrer"
            " Indizes, Namen und top_k-Werte wird in den Prompt gerendert."
            " Standardmäßig werden der semantische Standard-Retriever und der"
            " Standard-Stichwort-Retriever verwendet; sie sind änderbar.",
            zh=(
                "LLM 可咨询的子检索器。其索引、名称和 top_k 值的目录会渲染到提示词中。"
                "默认为默认语义检索器和关键词检索器，可随时修改。"
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
            en="Maximum number of retrieval rounds. One planning call plus at"
            " most this many minus one judgement calls.",
            es="Número máximo de rondas de recuperación. Una llamada de"
            " planificación más como máximo este número menos una llamadas de"
            " evaluación.",
            pt="Número máximo de rodadas de recuperação. Uma chamada de"
            " planejamento mais no máximo esse número menos uma chamadas de"
            " avaliação.",
            de="Maximale Anzahl von Abrufrunden. Ein Planungsaufruf plus"
            " höchstens diese Zahl minus eins Bewertungsaufrufe.",
            zh="最大检索轮数。一次规划调用加上最多该数量减一次评估调用。",
        ),
    )  # type: ignore

    prompt: schema_field(
        component_field(parent="RetrievalSufficiencyPrompt"),
        placeholder=default_retrieval_sufficiency_prompt(),
        description=MultilingualString(
            en="The prompt used to choose children and judge sufficiency.",
            es="El prompt usado para elegir hijos y juzgar la suficiencia.",
            pt="O prompt usado para escolher filhos e julgar a suficiência.",
            de="Der Prompt zur Auswahl der Kinder und Beurteilung der Suffizienz.",
            zh="用于选择子检索器并判断充分性的提示词。",
        ),
    )  # type: ignore

    llm_model: schema_field(
        component_field(parent="TextToTextGenerationTaskModel"),
        placeholder=default_function_calling_llm(),
        description=MultilingualString(
            en="The language model that chooses children and judges"
            " sufficiency. Defaults to the default RAG function-calling LLM;"
            " you can change it.",
            es="El modelo de lenguaje que elige hijos y juzga la suficiencia."
            " Por defecto usa el LLM de llamada a funciones RAG predeterminado;"
            " puedes cambiarlo.",
            pt="O modelo de linguagem que escolhe filhos e julga a suficiência."
            " Por padrão usa o LLM de chamada de funções RAG padrão; você pode"
            " alterá-lo.",
            de="Das Sprachmodell, das Kinder auswählt und die Suffizienz"
            " beurteilt. Standardmäßig wird das RAG-Standard-LLM für"
            " Funktionsaufrufe verwendet; es ist änderbar.",
            zh=(
                "选择子检索器并判断充分性的语言模型。默认为默认 RAG 函数调用 LLM，"
                "可随时修改。"
            ),
        ),
    )  # type: ignore


class LLMEvaluatedEnsembleRetriever(LLMEvaluatedRetriever):
    """Consults LLM-chosen children across rounds to build a sufficient pool.

    A planning evaluation over an empty pool selects the first round's children.
    Each round consults the chosen children at the explicit per-child ``top_k``
    supplied by the model, merges the results and — except for the final round —
    judges the pool. An insufficient verdict selects the next round's children.
    """

    SCHEMA = LLMEvaluatedEnsembleRetrieverSchema
    DISPLAY_NAME: str = MultilingualString(
        en="LLM-Evaluated Ensemble Retriever",
        es="Recuperador Conjunto Evaluado por LLM",
        pt="Retriever em Conjunto Avaliado por LLM",
        de="LLM-bewerteter Ensemble-Retriever",
        zh="LLM 评估集成检索器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Consults two or more child retrievers chosen by an LLM, using the"
        " explicit per-child top_k supplied for each call until the pool"
        " suffices.",
        es="Consulta dos o más recuperadores hijos elegidos por un LLM, usando"
        " el top_k explícito por hijo indicado en cada llamada hasta que el"
        " conjunto sea suficiente.",
        pt="Consulta dois ou mais recuperadores filhos escolhidos por um LLM,"
        " usando o top_k explícito por filho indicado em cada chamada até que o"
        " conjunto seja suficiente.",
        de="Konsultiert zwei oder mehr vom LLM gewählte Kind-Retriever mit dem"
        " für jeden Aufruf angegebenen top_k pro Kind, bis der Pool ausreicht.",
        zh=(
            "咨询由 LLM 选择的两个或更多子检索器，并使用每次调用指定的"
            "每个子检索器的 top_k，直到池足够。"
        ),
    )

    EXPECTED_FUNCTION: ClassVar[str] = "evaluate_retrieval_sufficiency"
    FUNCTION_DESCRIPTION: ClassVar[str] = (
        "Decide whether the retrieved chunks are sufficient to answer the user "
        "message. Use call_retrievers with 1-based retriever indices mapped to "
        "the number of chunks to retrieve from that retriever next (indices "
        "range from 1 to the number of retrievers). Use request_chunks and "
        "discard to include or exclude specific chunk positions by document id. "
        "Requested and discarded chunks persist across rounds and can override "
        "each other (the last action wins)."
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
                    "When insufficient, maps 1-based retriever indices to the "
                    "number of chunks to retrieve from them next."
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
        },
        "required": [SUFFICIENT_KEY],
    }

    def retrieve(self, query: str, **kwargs: Any) -> Tuple[List[Chunk], Dict[str, Any]]:
        """Retrieve by consulting LLM-chosen children across rounds.

        Parameters
        ----------
        query : str
            The search query string.
        **kwargs
            Unused; children choices and sizes come from the LLM verdicts.

        Returns
        -------
        Tuple[List[Chunk], Dict[str, Any]]
            The final pool (at most ``max_chunks`` chunks) and this retriever's
            trace node, whose ``children`` holds every consulted child node and
            whose ``rounds`` holds one summary per retrieval round.

        Raises
        ------
        RAGRetrieverEvaluationError
            If a verdict is malformed, requests no retriever while planning, or
            names an out-of-range retriever index.
        """
        context = RetrievalContext.from_retriever(self)
        pool = RetrievalPool(self.max_chunks, context)
        child_nodes: List[Dict[str, Any]] = []
        rounds: List[Dict[str, Any]] = []

        planning = self._evaluate(query, pool, context)
        self._apply_verdict_actions(pool, planning)
        calls = require_planning_calls(planning, len(self._children))
        if pool.size() >= self.max_chunks:
            raise RAGRetrieverEvaluationError(
                "The planning chunk actions left no capacity to consult the "
                f"requested retrievers: the pool already holds {pool.size()} "
                f"of {self.max_chunks} chunks."
            )

        for round_index in range(self.max_iters):
            call_entries: List[Dict[str, Any]] = []
            remaining = self.max_chunks - pool.size()
            if calls and remaining > 0:
                call_entries, nodes = self._consult(query, calls, pool, remaining)
                child_nodes.extend(nodes)
            entry: Dict[str, Any] = {
                "round": round_index + 1,
                "calls": call_entries,
                "verdict": None,
                "call_retrievers": {},
                "request_chunks": {},
                "discard": {},
            }
            rounds.append(entry)

            if round_index == self.max_iters - 1:
                break

            verdict = self._evaluate(query, pool, context)
            calls = validate_call_indices(verdict.call_retrievers, len(self._children))
            entry["verdict"] = verdict.sufficient
            entry["call_retrievers"] = dict(verdict.call_retrievers)
            entry["request_chunks"] = dict(verdict.request_chunks)
            entry["discard"] = dict(verdict.discard)
            if verdict.sufficient:
                # A sufficient verdict is terminal: chunk actions are not
                # applied and unknown positions are never resolved.
                break
            self._apply_verdict_actions(pool, verdict)

        pool_chunks = pool.materialize()
        return pool_chunks, self._build_trace(pool_chunks, child_nodes, rounds)

    def _consult(
        self,
        query: str,
        calls: Dict[int, int],
        pool: RetrievalPool,
        remaining: int,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Consult the requested children and merge their chunks into the pool.

        Parameters
        ----------
        query : str
            The search query string.
        calls : Dict[int, int]
            Validated 1-based retriever index to requested top-k mapping.
        pool : RetrievalPool
            The pool the retrieved chunks are merged into.
        remaining : int
            Free slots before the pool reaches ``max_chunks``. Each child's
            request is capped by it and the budget is reduced by the number of
            chunks the pool actually gained (duplicates add nothing).

        Returns
        -------
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]
            The per-child call summaries and the child trace nodes.
        """
        call_entries: List[Dict[str, Any]] = []
        nodes: List[Dict[str, Any]] = []
        budget = remaining
        discarded = pool.discarded_count()
        for index, requested_top_k in calls.items():
            if budget <= 0:
                break
            child = self._children[index - 1]
            request_limit = self.max_chunks + discarded
            requested = min(requested_top_k, request_limit)
            before = pool.size()
            chunks, node = self._delegate(child, query, requested)
            pool.add(chunks)
            added = pool.size() - before
            nodes.append(node)
            budget = max(budget - added, 0)
            call_entries.append(
                {
                    "name": type(child).__name__,
                    "requested_top_k": requested,
                    "returned": len(chunks),
                }
            )
        return call_entries, nodes

    def score_chunks(self, chunk_ids: List[int], query: str) -> List[Tuple[int, float]]:
        """Aggregate chunk scores across all children by averaging.

        Each child scores the chunks independently; all scores for the same
        chunk are averaged. Results are sorted by distance (ascending). Chunks
        no child scored are omitted.

        Parameters
        ----------
        chunk_ids : List[int]
            List of chunk IDs to score.
        query : str
            The search query string.

        Returns
        -------
        List[Tuple[int, float]]
            A list of ``(chunk_id, average_distance)`` tuples sorted by distance.
        """
        if not chunk_ids or not self._children:
            return []

        accumulator: Dict[int, List[float]] = {cid: [] for cid in chunk_ids}
        for child in self._children:
            for cid, distance in child.score_chunks(chunk_ids, query):
                accumulator[cid].append(distance)

        merged = [
            (cid, sum(distances) / len(distances))
            for cid, distances in accumulator.items()
            if distances
        ]
        merged.sort(key=lambda pair: pair[1])
        return merged
