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
from DashAI.back.models.RAG.exceptions.retriever import (
    RAGRetrieverEvaluationError,
)
from DashAI.back.models.RAG.retrievers.composite.composite_retriever import (
    CompositeRetriever,
)
from DashAI.back.models.RAG.retrievers.composite.evaluation_output import (
    RetrievalVerdict,
    parse_evaluation_arguments,
    parse_evaluation_output,
)
from DashAI.back.models.RAG.retrievers.trace_utils import retriever_trace
from DashAI.back.models.text_to_text_generation_model import FunctionCallResult

log = logging.getLogger(__name__)

#: Schema/param key names hoisted to avoid magic strings.
_PARAM_MAX_ITERS = "max_iters"
_PARAM_MAX_CHUNKS = "max_chunks"
_PARAM_PROMPT = "prompt"
_PARAM_LLM_MODEL = "llm_model"
_PARAM_ROUNDS = "rounds"

#: Maximum number of characters of each chunk's text included in the prompt.
#: Referenced by :meth:`LLMEvaluatedRetriever._render_chunks`.
_MAX_CHARS_PER_CHUNK = 400


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

    REPRESENTATION = MultilingualString(
        en="max_iters {max_iters} · max_chunks {max_chunks} · {prompt}",
        es="máx. iteraciones {max_iters} · máx. fragmentos {max_chunks} · {prompt}",
        pt="máx. iterações {max_iters} · máx. trechos {max_chunks} · {prompt}",
        de="max. Iterationen {max_iters} · max. Chunks {max_chunks} · {prompt}",
        zh="最大迭代 {max_iters} · 最大片段 {max_chunks} · {prompt}",
    )

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
    def _chunk_key(chunk: Chunk) -> Tuple[int, int]:
        """Build the pairwise dedup key for a chunk.

        Parameters
        ----------
        chunk : Chunk
            The chunk to key.

        Returns
        -------
        Tuple[int, int]
            ``(document_id, document_position)``.
        """
        return (chunk.document_id, chunk.document_position)

    def _merge_new_chunks(
        self, pool: List[Chunk], new_chunks: List[Chunk]
    ) -> List[Chunk]:
        """Return ``pool`` plus the unseen chunks of ``new_chunks``.

        Deduplicates by ``(document_id, document_position)`` while preserving
        insertion order. Pure: neither argument is mutated.

        Parameters
        ----------
        pool : List[Chunk]
            The chunks accumulated so far.
        new_chunks : List[Chunk]
            Chunks returned by the latest retrieval round.

        Returns
        -------
        List[Chunk]
            A new list with the merged, deduplicated pool.
        """
        merged = list(pool)
        seen = {self._chunk_key(chunk) for chunk in merged}
        for chunk in new_chunks:
            key = self._chunk_key(chunk)
            if key not in seen:
                seen.add(key)
                merged.append(chunk)
        return merged

    def _cap_pool(self, pool: List[Chunk]) -> List[Chunk]:
        """Truncate the pool to ``max_chunks`` preserving order.

        Parameters
        ----------
        pool : List[Chunk]
            The accumulated pool.

        Returns
        -------
        List[Chunk]
            The pool, capped at ``max_chunks`` chunks.
        """
        if len(pool) > self.max_chunks:
            return pool[: self.max_chunks]
        return pool

    @staticmethod
    def _render_chunks(pool: List[Chunk]) -> str:
        """Render the candidate pool as an indexed text block.

        Each chunk contributes one numbered line whose text is truncated to
        ``_MAX_CHARS_PER_CHUNK`` characters so a single oversized chunk cannot
        dominate the prompt. An empty pool renders as an empty string.

        Parameters
        ----------
        pool : List[Chunk]
            The candidate chunks.

        Returns
        -------
        str
            One ``[i] <text>`` line per chunk, joined by newlines.
        """
        lines = [
            f"[{index}] {chunk.text[:_MAX_CHARS_PER_CHUNK]}"
            for index, chunk in enumerate(pool, start=1)
        ]
        return "\n".join(lines)

    def _render_children_catalog(self) -> str:
        """Render the child retriever catalog as an indexed text block.

        Returns
        -------
        str
            One ``[i] <ClassName> (top_k=<n>)`` line per child, joined by
            newlines.
        """
        return "\n".join(
            f"[{index}] {type(child).__name__} (top_k={child.retrieval_top_k})"
            for index, child in enumerate(self._children)
        )

    def _evaluate(
        self, query: str, pool: List[Chunk], include_children_catalog: bool
    ) -> RetrievalVerdict:
        """Render the prompt and obtain the model's sufficiency verdict.

        When the configured model supports function calling, the verdict is
        requested through the subclass's function schema; otherwise the prompt
        is answered as text and parsed by the tolerant text parser.

        Parameters
        ----------
        query : str
            The user query under evaluation.
        pool : List[Chunk]
            The currently accumulated chunk pool.
        include_children_catalog : bool
            Whether to render the child-retriever catalog into the prompt. The
            depth retriever is blind to its child and never does; the ensemble
            retriever always does.

        Returns
        -------
        RetrievalVerdict
            The parsed verdict (see :func:`parse_evaluation_output`).

        Raises
        ------
        RAGRetrieverEvaluationError
            If the model output is empty, not a string, malformed, or the
            function-calling route fails validation.
        """
        catalog = self._render_children_catalog() if include_children_catalog else None
        prompt_text = self.prompt.format(
            input=query,
            chunks=self._render_chunks(pool),
            children_catalog=catalog,
            pool_size=len(pool),
        )
        if self.llm_model.supports_function_calling():
            return self._call_function_calling(prompt_text)
        output = self.llm_model.generate([{"role": "user", "content": prompt_text}])
        raw = self._extract_raw_output(output)
        return parse_evaluation_output(raw)

    def _call_function_calling(self, prompt_text: str) -> RetrievalVerdict:
        """Call the model through its function-calling interface.

        Parameters
        ----------
        prompt_text : str
            The rendered evaluation prompt sent as the user message.

        Returns
        -------
        RetrievalVerdict
            The validated verdict carried by the function call's arguments.

        Raises
        ------
        RAGRetrieverEvaluationError
            If the subclass declares no function spec, the model reports
            function-calling support without implementing it, the backend
            raises ``ValueError``/``RuntimeError``, or the returned call
            violates the contract.
        """
        if (
            not self.EXPECTED_FUNCTION
            or not self.FUNCTION_DESCRIPTION
            or not self.FUNCTION_PARAMETERS
        ):
            raise RAGRetrieverEvaluationError(
                f"{type(self).__name__} does not declare a function spec to use "
                "function calling; declare EXPECTED_FUNCTION, "
                "FUNCTION_DESCRIPTION and FUNCTION_PARAMETERS or use a "
                "model without function calling."
            )
        spec = {
            "name": self.EXPECTED_FUNCTION,
            "description": self.FUNCTION_DESCRIPTION,
            "parameters": self.FUNCTION_PARAMETERS,
        }
        try:
            result = self.llm_model.generate_function_call(
                messages=[{"role": "user", "content": prompt_text}],
                functions=[spec],
            )
        except NotImplementedError as err:
            raise RAGRetrieverEvaluationError(
                f"{type(self.llm_model).__name__} reports function calling "
                "support but does not implement generate_function_call."
            ) from err
        except (ValueError, RuntimeError) as err:
            raise RAGRetrieverEvaluationError(
                f"Function calling failed: {err}"
            ) from err
        return self._validate_function_call_result(result)

    def _validate_function_call_result(self, result: Any) -> RetrievalVerdict:
        """Validate a function-call response and resolve its arguments.

        Parameters
        ----------
        result : Any
            The raw return value of ``generate_function_call``.

        Returns
        -------
        RetrievalVerdict
            The validated verdict, with JSON-encoded arguments resolved.

        Raises
        ------
        RAGRetrieverEvaluationError
            If the result is not a :class:`FunctionCallResult`, it has no name,
            it names a function other than :attr:`EXPECTED_FUNCTION`, or its
            arguments do not satisfy the verdict contract.
        """
        if not isinstance(result, FunctionCallResult):
            raise RAGRetrieverEvaluationError(
                "The function-calling model returned an unexpected output shape: "
                f"{type(result).__name__}."
            )
        if not result.name:
            raise RAGRetrieverEvaluationError(
                "The function-calling model did not report a function name."
            )
        if result.name != self.EXPECTED_FUNCTION:
            raise RAGRetrieverEvaluationError(
                f"The model called '{result.name}' instead of the expected "
                f"'{self.EXPECTED_FUNCTION}'."
            )
        return parse_evaluation_arguments(result.arguments)

    @staticmethod
    def _extract_raw_output(output: Any) -> str:
        """Extract the raw string from the model output list.

        Parameters
        ----------
        output : Any
            The list returned by ``generate``.

        Returns
        -------
        str
            The first element of the output.

        Raises
        ------
        RAGRetrieverEvaluationError
            If the list is empty or its first element is not a string.
        """
        if not output:
            raise RAGRetrieverEvaluationError(
                "The evaluation model returned an empty output."
            )
        raw = output[0]
        if not isinstance(raw, str):
            raise RAGRetrieverEvaluationError(
                f"The evaluation model output is not a string: {type(raw).__name__}."
            )
        return raw

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
