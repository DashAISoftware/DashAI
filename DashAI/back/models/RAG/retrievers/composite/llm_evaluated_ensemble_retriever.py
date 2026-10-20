"""LLM-evaluated ensemble retriever.

Takes two or more child retrievers. The language model is shown a catalog of the
children (index, class name and configured ``top_k``) and chooses which children
to consult each round. A child consulted again in a later round is delegated
with an *escalated* retrieval size, so re-selection widens that child's
contribution. Sufficiency is judged over the accumulated pool.

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
from DashAI.back.models.RAG.RAG_defaults import (
    DEFAULT_MAX_CHUNKS,
    DEFAULT_MAX_ITERS,
    default_function_calling_llm,
    default_keyword_retriever,
    default_retrieval_sufficiency_prompt,
    default_semantic_retriever,
)
from DashAI.back.models.RAG.retrievers.composite.evaluation_output import (
    CHILDREN_KEY,
    SUFFICIENT_KEY,
    require_for_ensemble,
)
from DashAI.back.models.RAG.retrievers.composite.llm_evaluated_retriever import (
    LLMEvaluatedRetriever,
)


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
    Each round consults the chosen children (re-consulting a child escalates its
    ``top_k``), merges the results and — except for the final round — judges the
    pool. An insufficient verdict selects the next round's children.
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
        en="Consults two or more child retrievers chosen by an LLM, escalating"
        " the size of re-consulted children until the pool suffices.",
        es="Consulta dos o más recuperadores hijos elegidos por un LLM,"
        " aumentando el tamaño de los hijos reconsultados hasta que el conjunto"
        " sea suficiente.",
        pt="Consulta dois ou mais recuperadores filhos escolhidos por um LLM,"
        " aumentando o tamanho dos filhos reconsultados até que o conjunto seja"
        " suficiente.",
        de="Konsultiert zwei oder mehr vom LLM gewählte Kind-Retriever und"
        " erhöht die Größe erneut konsultierter Kinder, bis der Pool ausreicht.",
        zh=(
            "咨询由 LLM 选择的两个或更多子检索器，并提升被再次咨询"
            "子检索器的规模，直到池足够。"
        ),
    )

    EXPECTED_FUNCTION: ClassVar[str] = "evaluate_retrieval_sufficiency"
    FUNCTION_DESCRIPTION: ClassVar[str] = (
        "Decide whether the retrieved chunks are sufficient to answer the user "
        "message and, when they are not, which child retrievers to consult next."
    )
    # ``children`` stays optional in the JSON schema; the runtime validator
    # requires it whenever ``sufficient`` is false.
    FUNCTION_PARAMETERS: ClassVar[Dict[str, Any]] = {
        "type": "object",
        "properties": {
            SUFFICIENT_KEY: {
                "type": "boolean",
                "description": (
                    "Whether the retrieved chunks suffice. When false, children "
                    "is required."
                ),
            },
            CHILDREN_KEY: {
                "type": "array",
                "items": {"type": "integer", "minimum": 0},
                "minItems": 1,
                "description": (
                    "When insufficient, the indices of the child retrievers to "
                    "consult in the next round."
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
            If a verdict is malformed, selects no children, or selects an
            out-of-range child index.
        """
        pool: List[Chunk] = []
        child_nodes: List[Dict[str, Any]] = []
        rounds: List[Dict[str, Any]] = []
        consult_counts = [0] * len(self._children)

        planning = self._evaluate(query, pool, include_children_catalog=True)
        indices = require_for_ensemble(planning, len(self._children))

        for round_index in range(self.max_iters):
            remaining = self.max_chunks - len(pool)
            calls, retrieved, nodes = self._consult(
                query, indices, remaining, consult_counts
            )
            child_nodes.extend(nodes)
            pool = self._cap_pool(self._merge_new_chunks(pool, retrieved))
            entry: Dict[str, Any] = {
                "round": round_index + 1,
                "calls": calls,
                "verdict": None,
            }
            rounds.append(entry)

            remaining = self.max_chunks - len(pool)
            if remaining <= 0 or round_index == self.max_iters - 1:
                break

            verdict = self._evaluate(query, pool, include_children_catalog=True)
            if verdict.sufficient:
                entry["verdict"] = True
                break
            entry["verdict"] = False
            indices = require_for_ensemble(verdict, len(self._children))

        return pool, self._build_trace(pool, child_nodes, rounds)

    def _consult(
        self,
        query: str,
        indices: List[int],
        remaining: int,
        consult_counts: List[int],
    ) -> Tuple[List[Dict[str, Any]], List[Chunk], List[Dict[str, Any]]]:
        """Consult the chosen children and collect their results.

        Each child is delegated a retrieval size of
        ``child.retrieval_top_k * (1 + times_already_consulted)``, capped by
        ``max_chunks``. The consultation counter is advanced per successful
        call so a re-consulted child widens on every later round. The size is a
        per-call hint, not a pool increment: the pool cap is enforced by the
        merge/cap step, while capping the call keeps the child from fetching
        more than the pool may ever hold.

        Parameters
        ----------
        query : str
            The search query string.
        indices : List[int]
            Validated, deduplicated child indices to consult.
        remaining : int
            Budget left before the pool reaches ``max_chunks``; ``<= 0`` skips
            the round entirely.
        consult_counts : List[int]
            Per-child number of previous consultations (mutated in place).

        Returns
        -------
        Tuple[List[Dict[str, Any]], List[Chunk], List[Dict[str, Any]]]
            The per-child call summaries, the concatenated retrieved chunks
            and the child trace nodes.
        """
        calls: List[Dict[str, Any]] = []
        retrieved: List[Chunk] = []
        nodes: List[Dict[str, Any]] = []
        if remaining <= 0:
            return calls, retrieved, nodes
        for index in indices:
            child = self._children[index]
            requested = min(
                child.retrieval_top_k * (1 + consult_counts[index]),
                self.max_chunks,
            )
            chunks, node = self._delegate(child, query, requested)
            consult_counts[index] += 1
            retrieved.extend(chunks)
            nodes.append(node)
            calls.append(
                {
                    "name": type(child).__name__,
                    "requested_top_k": requested,
                    "returned": len(chunks),
                }
            )
        return calls, retrieved, nodes

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
