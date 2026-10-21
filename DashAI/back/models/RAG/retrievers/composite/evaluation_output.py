"""Fence-tolerant parser for the retrieval-sufficiency evaluation contract.

The LLM-evaluated retrievers ask their language model for a single JSON verdict
that judges whether the retrieved pool is sufficient and, when it is not, how to
proceed. In practice models wrap that object in prose or markdown fences, so
this parser tolerates the *wrapping* but never the *payload*: a missing or
mistyped field raises :class:`RAGRetrieverEvaluationError` instead of being
silently defaulted, because falling back to a guessed verdict would let an
unparseable model response drive retrieval without anyone noticing.

Contract
--------
``{"sufficient": true}`` — the pool answers the query.

An insufficient verdict carries any combination of:

* ``call_retrievers`` — ``{<1-based retriever index>: <top_k>}``;
* ``request_chunks`` — ``{<document id>: [<chunk positions>]}``;
* ``discard`` — ``{<document id>: [<chunk positions>]}``.

Requested and discarded chunks persist across rounds and can override each
other (the last action wins). An insufficient verdict that performs no action at
all is rejected: it cannot make progress.

Unknown keys are tolerated; the contract fields are not.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Dict, List

from DashAI.back.models.RAG.exceptions.retriever import (
    RAGRetrieverEvaluationError,
)

#: Maximum number of characters of raw model output echoed in error messages.
_PREVIEW_LIMIT = 200

#: Matches opening and closing markdown code fences, with or without a language.
_FENCE_RE = re.compile(r"```[a-zA-Z0-9_-]*")

#: Canonical contract field names, shared with the retrievers consuming a verdict.
SUFFICIENT_KEY = "sufficient"
CALL_RETRIEVERS_KEY = "call_retrievers"
REQUEST_CHUNKS_KEY = "request_chunks"
DISCARD_KEY = "discard"


@dataclass(frozen=True)
class RetrievalVerdict:
    """A validated retrieval-sufficiency verdict.

    Attributes
    ----------
    sufficient : bool
        Whether the accumulated pool answers the query.
    call_retrievers : Dict[int, int]
        Mapping of 1-based retriever index to the number of chunks to retrieve
        from it next. Empty when no retriever call is requested.
    request_chunks : Dict[int, List[int]]
        Mapping of document id to chunk positions to include in the pool. Empty
        when no chunk is explicitly requested.
    discard : Dict[int, List[int]]
        Mapping of document id to chunk positions to exclude from the pool.
        Empty when no chunk is discarded.
    """

    sufficient: bool
    call_retrievers: Dict[int, int] = field(default_factory=dict)
    request_chunks: Dict[int, List[int]] = field(default_factory=dict)
    discard: Dict[int, List[int]] = field(default_factory=dict)


def _preview(raw: Any) -> str:
    """Return a short, truncated preview of the raw model output.

    Parameters
    ----------
    raw : Any
        Raw model output.

    Returns
    -------
    str
        The output truncated to at most ``_PREVIEW_LIMIT`` characters, with a
        trailing ellipsis when truncation happened.
    """
    text = str(raw)
    if len(text) <= _PREVIEW_LIMIT:
        return text
    return text[:_PREVIEW_LIMIT] + "..."


def _extract_json_object(text: str) -> str:
    """Extract the substring from the first ``{`` to the last ``}``.

    Parameters
    ----------
    text : str
        Text to scan.

    Returns
    -------
    str
        The candidate JSON object.

    Raises
    ------
    RAGRetrieverEvaluationError
        If no braces are present or their order is inverted.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise RAGRetrieverEvaluationError(
            "The evaluation model output does not contain a JSON object. "
            f"Preview: {_preview(text)}"
        )
    return text[start : end + 1]


def _coerce_key(value: Any, key: str, minimum: int, raw: Any) -> int:
    """Coerce a mapping key to an integer honouring the contract bounds.

    Parameters
    ----------
    value : Any
        Raw mapping key (an integer or a digit string).
    key : str
        Contract field name, echoed in error messages.
    minimum : int
        Smallest accepted value.
    raw : Any
        Original payload, echoed in the error message.

    Returns
    -------
    int
        The coerced key.

    Raises
    ------
    RAGRetrieverEvaluationError
        If the key is neither an integer nor a digit string, or is below
        ``minimum``.
    """
    if isinstance(value, bool):
        raise RAGRetrieverEvaluationError(
            f"'{key}' keys must be integers greater than or equal to {minimum}, "
            f"got {value!r}. Preview: {_preview(raw)}"
        )
    if isinstance(value, int):
        coerced = value
    elif isinstance(value, str) and value.isdigit():
        coerced = int(value)
    else:
        raise RAGRetrieverEvaluationError(
            f"'{key}' keys must be integers greater than or equal to {minimum}, "
            f"got {value!r}. Preview: {_preview(raw)}"
        )
    if coerced < minimum:
        raise RAGRetrieverEvaluationError(
            f"'{key}' keys must be integers greater than or equal to {minimum}, "
            f"got {value!r}. Preview: {_preview(raw)}"
        )
    return coerced


def _coerce_value(value: Any, key: str, minimum: int, raw: Any) -> int:
    """Coerce a mapping value to an integer honouring the contract bounds."""
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise RAGRetrieverEvaluationError(
            f"'{key}' values must be integers greater than or equal to {minimum}, "
            f"got {value!r}. Preview: {_preview(raw)}"
        )
    return value


def _validate_call_retrievers(value: Any, raw: Any) -> Dict[int, int]:
    """Validate the ``call_retrievers`` mapping.

    Parameters
    ----------
    value : Any
        Raw ``call_retrievers`` value from the parsed verdict.
    raw : Any
        Original payload, echoed in error messages.

    Returns
    -------
    Dict[int, int]
        1-based retriever index to requested chunk count.

    Raises
    ------
    RAGRetrieverEvaluationError
        If the value is not a mapping, a key cannot be coerced to an index
        ``>= 1``, two keys collide after coercion, or a value is not an integer
        ``>= 1``.
    """
    if not isinstance(value, Mapping):
        raise RAGRetrieverEvaluationError(
            f"'{CALL_RETRIEVERS_KEY}' must be a mapping of retriever index to "
            f"top_k, got {type(value).__name__}. Preview: {_preview(raw)}"
        )
    calls: Dict[int, int] = {}
    seen: set[int] = set()
    for raw_index, raw_top_k in value.items():
        index = _coerce_key(raw_index, CALL_RETRIEVERS_KEY, 1, raw)
        if index in seen:
            raise RAGRetrieverEvaluationError(
                f"'{CALL_RETRIEVERS_KEY}' contains duplicate key {index!r} "
                f"after integer coercion. Preview: {_preview(raw)}"
            )
        seen.add(index)
        calls[index] = _coerce_value(raw_top_k, CALL_RETRIEVERS_KEY, 1, raw)
    return calls


def _validate_chunk_map(value: Any, key: str, raw: Any) -> Dict[int, List[int]]:
    """Validate a ``request_chunks``/``discard`` document-to-positions mapping.

    Parameters
    ----------
    value : Any
        Raw mapping from the parsed verdict.
    key : str
        Contract field name, echoed in error messages.
    raw : Any
        Original payload, echoed in error messages.

    Returns
    -------
    Dict[int, List[int]]
        Document id to chunk positions, deduplicated in first-seen order.

    Raises
    ------
    RAGRetrieverEvaluationError
        If the value is not a mapping, a document id cannot be coerced to an
        id ``>= 0``, two ids collide after coercion, a value is not a list, or
        a position is not an integer ``>= 0``.
    """
    if not isinstance(value, Mapping):
        raise RAGRetrieverEvaluationError(
            f"'{key}' must be a mapping of document id to chunk positions, got "
            f"{type(value).__name__}. Preview: {_preview(raw)}"
        )
    chunks: Dict[int, List[int]] = {}
    seen: set[int] = set()
    for raw_document_id, raw_positions in value.items():
        document_id = _coerce_key(raw_document_id, key, 0, raw)
        if document_id in seen:
            raise RAGRetrieverEvaluationError(
                f"'{key}' contains duplicate key {document_id!r} after integer "
                f"coercion. Preview: {_preview(raw)}"
            )
        seen.add(document_id)
        if not isinstance(raw_positions, list):
            raise RAGRetrieverEvaluationError(
                f"'{key}' values must be lists of chunk positions, got "
                f"{type(raw_positions).__name__}. Preview: {_preview(raw)}"
            )
        positions: List[int] = []
        for raw_position in raw_positions:
            position = _coerce_value(raw_position, key, 0, raw)
            if position not in positions:
                positions.append(position)
        chunks[document_id] = positions
    return chunks


def _validate_verdict(parsed: Any, raw: Any) -> RetrievalVerdict:
    """Validate a parsed verdict against the retrieval-sufficiency contract.

    Parameters
    ----------
    parsed : Any
        The decoded verdict payload, expected to be a mapping.
    raw : Any
        Original payload (a string or a decoded mapping), echoed in error
        messages.

    Returns
    -------
    RetrievalVerdict
        The validated verdict.

    Raises
    ------
    RAGRetrieverEvaluationError
        If the payload is not a mapping, ``sufficient`` is missing or not a
        boolean, an action map has the wrong type/shape, a chunk is both
        requested and discarded, or an insufficient verdict performs no action.
    """
    if not isinstance(parsed, Mapping):
        raise RAGRetrieverEvaluationError(
            f"The evaluation output is not a JSON object. Preview: {_preview(raw)}"
        )

    sufficient = parsed.get(SUFFICIENT_KEY)
    if not isinstance(sufficient, bool):
        raise RAGRetrieverEvaluationError(
            f"'sufficient' must be present and a boolean. Preview: {_preview(raw)}"
        )

    calls: Dict[int, int] = {}
    if CALL_RETRIEVERS_KEY in parsed:
        calls = _validate_call_retrievers(parsed[CALL_RETRIEVERS_KEY], raw)

    requests: Dict[int, List[int]] = {}
    if REQUEST_CHUNKS_KEY in parsed:
        requests = _validate_chunk_map(
            parsed[REQUEST_CHUNKS_KEY], REQUEST_CHUNKS_KEY, raw
        )

    discards: Dict[int, List[int]] = {}
    if DISCARD_KEY in parsed:
        discards = _validate_chunk_map(parsed[DISCARD_KEY], DISCARD_KEY, raw)

    for document_id, positions in requests.items():
        conflicting = set(positions) & set(discards.get(document_id, []))
        if conflicting:
            raise RAGRetrieverEvaluationError(
                f"Chunk positions {sorted(conflicting)} of document "
                f"{document_id} cannot be both requested and discarded in the "
                f"same verdict. Preview: {_preview(raw)}"
            )

    if not sufficient and not calls:
        has_requested_positions = False
        for positions in requests.values():
            if positions:
                has_requested_positions = True
                break
        has_discarded_positions = False
        if not has_requested_positions:
            for positions in discards.values():
                if positions:
                    has_discarded_positions = True
                    break
        if not has_requested_positions and not has_discarded_positions:
            raise RAGRetrieverEvaluationError(
                "An insufficient verdict must perform at least one action with "
                f"at least one chunk position: '{CALL_RETRIEVERS_KEY}', "
                f"'{REQUEST_CHUNKS_KEY}' or '{DISCARD_KEY}'. "
                f"Preview: {_preview(raw)}"
            )

    return RetrievalVerdict(
        sufficient=sufficient,
        call_retrievers=calls,
        request_chunks=requests,
        discard=discards,
    )


def parse_evaluation_output(raw: str) -> RetrievalVerdict:
    """Parse the retrieval-sufficiency verdict out of raw model output.

    Markdown fences are stripped, the substring from the first ``{`` to the last
    ``}`` is taken, and the result must be a JSON object carrying a boolean
    ``sufficient`` field. The optional action maps are validated when present;
    unknown keys are ignored.

    Parameters
    ----------
    raw : str
        Raw model output.

    Returns
    -------
    RetrievalVerdict
        The validated verdict.

    Raises
    ------
    RAGRetrieverEvaluationError
        If the output contains no JSON object, the JSON is invalid, the parsed
        value is not a mapping, ``sufficient`` is missing or not a boolean, or
        an action map violates the contract.
    """
    text = _FENCE_RE.sub("", str(raw)).strip()
    candidate = _extract_json_object(text)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as err:
        raise RAGRetrieverEvaluationError(
            f"Failed to parse the evaluation output as JSON. Preview: {_preview(raw)}"
        ) from err
    return _validate_verdict(parsed, raw)


def parse_evaluation_arguments(arguments: Any) -> RetrievalVerdict:
    """Validate the arguments payload of a function call as a verdict.

    Function-calling backends return arguments either already decoded as a
    mapping or as a JSON-encoded string emitted under constrained sampling. Both
    are accepted here; the payload is validated against the same strict contract
    as :func:`parse_evaluation_output`, so the two routes cannot diverge.

    Parameters
    ----------
    arguments : Any
        The raw ``FunctionCallResult.arguments`` payload.

    Returns
    -------
    RetrievalVerdict
        The validated verdict.

    Raises
    ------
    RAGRetrieverEvaluationError
        If the payload is a string that fails text parsing, is a mapping that
        violates the contract, or is neither a mapping nor a string.
    """
    if isinstance(arguments, Mapping):
        return _validate_verdict(arguments, arguments)
    if isinstance(arguments, str):
        return parse_evaluation_output(arguments)
    raise RAGRetrieverEvaluationError(
        "The function-calling arguments must be a mapping or a JSON-encoded "
        f"string, got {type(arguments).__name__}. Preview: {_preview(arguments)}"
    )


def validate_call_indices(
    calls: Dict[int, int], retriever_count: int
) -> Dict[int, int]:
    """Validate that every retriever index addresses a configured retriever.

    Parameters
    ----------
    calls : Dict[int, int]
        A validated ``call_retrievers`` mapping.
    retriever_count : int
        Number of retrievers the caller may address.

    Returns
    -------
    Dict[int, int]
        The same mapping, unchanged.

    Raises
    ------
    RAGRetrieverEvaluationError
        If any index is outside ``1..retriever_count``.
    """
    for index in calls:
        if index < 1 or index > retriever_count:
            raise RAGRetrieverEvaluationError(
                f"Retriever index {index} is out of range for "
                f"{retriever_count} configured retriever(s); indices are "
                "1-based."
            )
    return calls


def require_planning_calls(
    verdict: RetrievalVerdict, retriever_count: int
) -> Dict[int, int]:
    """Return the retriever calls of an ensemble planning verdict.

    The planning evaluation runs over an empty pool, so it must be insufficient
    and must request at least one retriever.

    Parameters
    ----------
    verdict : RetrievalVerdict
        The verdict of the planning evaluation.
    retriever_count : int
        Number of child retrievers available to the ensemble.

    Returns
    -------
    Dict[int, int]
        The validated ``call_retrievers`` mapping.

    Raises
    ------
    RAGRetrieverEvaluationError
        If the verdict is marked sufficient, requests no retriever, or names an
        out-of-range retriever index.
    """
    if verdict.sufficient:
        raise RAGRetrieverEvaluationError(
            "An ensemble planning evaluation over an empty pool must be "
            "insufficient and request retrievers, but the verdict is marked "
            "sufficient."
        )
    if not verdict.call_retrievers:
        raise RAGRetrieverEvaluationError(
            "An insufficient ensemble planning evaluation must request at "
            f"least one retriever via '{CALL_RETRIEVERS_KEY}'."
        )
    return validate_call_indices(verdict.call_retrievers, retriever_count)
