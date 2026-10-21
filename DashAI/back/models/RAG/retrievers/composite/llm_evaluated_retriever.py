"""Abstract base for LLM-evaluated composite retrievers.

Both concrete retrievers share the same idea: retrieve a pool of chunks, ask a
language model whether that pool is sufficient to answer the query, and — when
it is not — retrieve again according to the model's verdict. The language model
is a parameter *of the retriever itself* (not of the RAG pipeline). Any parse or
validation failure of the verdict raises; there are no silent fallbacks.

The evaluation has two routes. When the configured model supports function
calling, the verdict is obtained through ``generate_function_call`` with the
subclass's JSON schema, so the arguments shape is constrained by the backend.
Otherwise the prompt is answered as text and parsed by the tolerant text parser.

Subclasses differ only in how they choose the *next* retrieval: the depth
retriever asks for a larger retrieval size from its single child, while the
ensemble retriever asks the model to pick which of its children to consult.
"""

from __future__ import annotations

import logging
from abc import ABC
from typing import Any, ClassVar, Dict, List, Tuple

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.exceptions import (
    RAGRetrieverCompositeValidationError,
    RAGRetrieverMissingParameterError,
)
from DashAI.back.models.RAG.progress_utils import report_progress
from DashAI.back.models.RAG.RAG_constants import (
    RAG_PROGRESS_JUSTIFICATION_KEY,
    RAG_PROGRESS_MESSAGE_KEY,
    RAG_PROGRESS_STAGE_RETRIEVING,
)
from DashAI.back.models.RAG.retrievers.composite.composite_retriever import (
    CompositeRetriever,
)
from DashAI.back.models.RAG.retrievers.composite.evaluation_output import (
    RetrievalVerdict,
)
from DashAI.back.models.RAG.retrievers.composite.retrieval_context import (
    RetrievalContext,
)
from DashAI.back.models.RAG.retrievers.composite.retrieval_evaluator import (
    RetrievalEvaluator,
)
from DashAI.back.models.RAG.retrievers.composite.retrieval_pool import RetrievalPool
from DashAI.back.models.RAG.retrievers.trace_utils import retriever_trace

log = logging.getLogger(__name__)

#: Schema/param key names hoisted to avoid magic strings.
_PARAM_MAX_ITERS = "max_iters"
_PARAM_MAX_CHUNKS = "max_chunks"
_PARAM_PROMPT = "prompt"
_PARAM_LLM_MODEL = "llm_model"


class LLMEvaluatedRetriever(CompositeRetriever, ABC):
    """Shared behaviour of the LLM-evaluated composite retrievers.

    Handles construction/validation of the common parameters, the delegation
    contract, the pool merge/cap rules and the prompt rendering + LLM call +
    verdict parsing pipeline. Concrete subclasses implement :meth:`retrieve` and
    :meth:`score_chunks`.

    Attributes:
        max_iters: Maximum number of retrieval rounds (``>= 1``).
        max_chunks: Maximum number of chunks the pool may hold (``>= 1``).
        prompt: The :class:`RetrievalSufficiencyPrompt` instance used to judge
            the pool. Required — no artificial default is assumed.
        llm_model: The :class:`TextToTextGenerationTaskModel` used to judge the
            pool. Required — no artificial default is assumed.
        EXPECTED_FUNCTION: The function name a function-calling model must call.
        FUNCTION_DESCRIPTION: Human-readable description of that function.
        FUNCTION_PARAMETERS: JSON schema of the function's arguments.
    """

    #: Nested ``{component, params}`` reference parameters the factories must
    #: resolve into live component instances before construction.
    COMPONENT_PARAMS: tuple[str, ...] = (_PARAM_LLM_MODEL, _PARAM_PROMPT)

    #: Function-calling contract declared by each concrete retriever.
    EXPECTED_FUNCTION: ClassVar[str] = ""
    FUNCTION_DESCRIPTION: ClassVar[str] = ""
    FUNCTION_PARAMETERS: ClassVar[Dict[str, Any]] = {}

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the retriever with its common parameters.

        Parameters
        ----------
        **kwargs
            Must contain ``children`` (handled by the composite base),
            ``max_iters``, ``max_chunks``, ``prompt`` and ``llm_model``.

        Raises
        ------
        RAGRetrieverMissingParameterError
            If ``max_iters``, ``max_chunks``, ``prompt`` or ``llm_model`` is
            absent.
        RAGRetrieverCompositeValidationError
            If ``max_iters`` or ``max_chunks`` is not a positive integer.
        """
        super().__init__(**kwargs)
        self.max_iters = self._pop_positive_int(_PARAM_MAX_ITERS)
        self.max_chunks = self._pop_positive_int(_PARAM_MAX_CHUNKS)
        self.prompt = self._pop_required(_PARAM_PROMPT)
        self.llm_model = self._pop_required(_PARAM_LLM_MODEL)
        self._evaluator = RetrievalEvaluator(
            self.prompt,
            self.llm_model,
            self.EXPECTED_FUNCTION,
            self.FUNCTION_DESCRIPTION,
            self.FUNCTION_PARAMETERS,
        )

    REPRESENTATION = MultilingualString(
        en="max_iters {max_iters} · max_chunks {max_chunks} · {prompt}",
        es="máx. iteraciones {max_iters} · máx. fragmentos {max_chunks} · {prompt}",
        pt="máx. iterações {max_iters} · máx. trechos {max_chunks} · {prompt}",
        de="max. Iterationen {max_iters} · max. Chunks {max_chunks} · {prompt}",
        zh="最大迭代 {max_iters} · 最大片段 {max_chunks} · {prompt}",
    )

    @classmethod
    def _get_main_parameters(cls) -> Dict[str, str]:
        """Return the round and pool budget paths."""
        return {"max_iters": "max_iters", "max_chunks": "max_chunks"}

    @property
    def retrieval_top_k(self) -> int:
        """Return the pool cap (``max_chunks``)."""
        return self.max_chunks

    def _pop_positive_int(self, key: str) -> int:
        """Pop a required positive integer parameter from ``self.params``.

        Parameters
        ----------
        key : str
            Parameter name.

        Returns
        -------
        int
            The validated positive integer.

        Raises
        ------
        RAGRetrieverMissingParameterError
            If the parameter is absent.
        RAGRetrieverCompositeValidationError
            If the value is not a positive integer.
        """
        if key not in self.params:
            raise RAGRetrieverMissingParameterError(
                f"'{key}' is required to build an LLM-evaluated retriever."
            )
        value = self.params.pop(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise RAGRetrieverCompositeValidationError(
                f"'{key}' must be a positive integer, got {value!r}."
            )
        return value

    def _pop_required(self, key: str) -> Any:
        """Pop a required parameter from ``self.params`` without defaulting.

        Parameters
        ----------
        key : str
            Parameter name.

        Returns
        -------
        Any
            The parameter value.

        Raises
        ------
        RAGRetrieverMissingParameterError
            If the parameter is absent or ``None``.
        """
        if self.params.get(key) is None:
            raise RAGRetrieverMissingParameterError(
                f"'{key}' is required to build an LLM-evaluated retriever; no "
                "default is assumed."
            )
        return self.params.pop(key)

    def _delegate(
        self, child: Any, query: str, top_k: int | None
    ) -> Tuple[List[Chunk], Dict[str, Any]]:
        """Retrieve from a child retriever under the shared delegation contract.

        ``top_k`` is a **retrieval-size hint**, not a hard final count. Unit
        children (BM25/TFIDF/dense) honour it as the number of candidates to
        return; composite children interpret it per their own contract, e.g. the
        cross-encoder treats it as a final count and the MMR reranker ignores it.
        That asymmetry is accepted and documented here rather than worked around
        at the call site.

        Parameters
        ----------
        child : BaseRetriever
            The child retriever to delegate to.
        query : str
            The search query string.
        top_k : int | None
            The retrieval-size hint, or ``None`` to let the child use its own
            configured size.

        Returns
        -------
        Tuple[List[Chunk], Dict[str, Any]]
            The child's ``(chunks, trace node)``.
        """
        if top_k is None:
            return child.retrieve(query)
        return child.retrieve(query, top_k=top_k)

    @staticmethod
    def _apply_verdict_actions(pool: RetrievalPool, verdict: RetrievalVerdict) -> None:
        """Apply a verdict's discard then request actions to the pool."""
        pool.discard(verdict.discard)
        pool.request(verdict.request_chunks)

    def _report_verdict_progress(self, verdict: RetrievalVerdict) -> None:
        """Report a verdict's optional narrative on the retrieving channel.

        The event deliberately omits ``queries``: the pipeline's own
        ``retrieving`` payload already carries the full resolved query list,
        and a retriever only knows the single query it is working on. The
        frontend renders the narrative (or a justification-only detail) without
        needing the query list.

        Parameters
        ----------
        verdict : RetrievalVerdict
            The validated verdict, possibly carrying ``message`` and/or
            ``justification``.

        Returns
        -------
        None
            Nothing is emitted when the verdict has no narrative, so the
            pipeline's own retrieving payload is left untouched.
        """
        if not verdict.message and not verdict.justification:
            return
        report_progress(
            RAG_PROGRESS_STAGE_RETRIEVING,
            message=verdict.message,
            justification=verdict.justification,
        )

    @staticmethod
    def _record_round_narrative(
        entry: Dict[str, Any],
        verdict: RetrievalVerdict,
        *,
        key_prefix: str = "",
    ) -> None:
        """Attach a verdict's optional narrative to a trace round entry.

        Parameters
        ----------
        entry : Dict[str, Any]
            The JSON-serializable round summary.
        verdict : RetrievalVerdict
            The validated verdict whose narrative is recorded.
        key_prefix : str, optional
            Prefix applied to the recorded keys. The ensemble uses
            ``"planning_"`` for its pre-round planning verdict so a later
            post-round verdict cannot overwrite it.

        Returns
        -------
        None
            ``message``/``justification`` are added only when non-empty.
        """
        if verdict.message:
            entry[f"{key_prefix}{RAG_PROGRESS_MESSAGE_KEY}"] = verdict.message
        if verdict.justification:
            entry[f"{key_prefix}{RAG_PROGRESS_JUSTIFICATION_KEY}"] = (
                verdict.justification
            )

    def _evaluate(
        self, query: str, pool: RetrievalPool, context: RetrievalContext
    ) -> RetrievalVerdict:
        """Delegate the prompt rendering and model call to the evaluator.

        Parameters
        ----------
        query : str
            The user query under evaluation.
        pool : RetrievalPool
            The currently accumulated chunk pool.
        context : RetrievalContext
            Document and corpus knowledge for the prompt.

        Returns
        -------
        RetrievalVerdict
            The validated verdict.
        """
        chunks = pool.materialize()
        return self._evaluator.evaluate(
            query=query,
            chunks=chunks,
            pool_size=len(chunks),
            top_k=self.max_chunks,
            children=self.get_children(),
            context=context,
        )

    def _build_trace(
        self,
        pool: List[Chunk],
        child_nodes: List[Dict[str, Any]],
        rounds: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build the retriever trace node with ``children`` and ``rounds``.

        Parameters
        ----------
        pool : List[Chunk]
            The final chunk pool.
        child_nodes : List[Dict[str, Any]]
            The child trace nodes captured across all rounds.
        rounds : List[Dict[str, Any]]
            The JSON-serializable per-round summaries.

        Returns
        -------
        Dict[str, Any]
            The trace node for this retriever.
        """
        return retriever_trace(self, pool, children=child_nodes, rounds=rounds)
