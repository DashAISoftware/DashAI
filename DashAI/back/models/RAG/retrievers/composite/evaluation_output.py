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
``{"sufficient": false, "top_k": <int >= 1>}`` — the depth retriever must
delegate again for a larger retrieval size.
``{"sufficient": false, "children": [<int indices >= 0>]}`` — the ensemble
retriever must consult the listed child retrievers.

Unknown keys are tolerated; the contract fields are not.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, List, Optional

from DashAI.back.models.RAG.exceptions.retriever import (
    RAGRetrieverEvaluationError,
)

#: Maximum number of characters of raw model output echoed in error messages.
_PREVIEW_LIMIT = 200

#: Matches opening and closing markdown code fences, with or without a language.
_FENCE_RE = re.compile(r"```[a-zA-Z0-9_-]*")

#: Canonical contract field names, shared with the retrievers consuming a verdict.
SUFFICIENT_KEY = "sufficient"
TOP_K_KEY = "top_k"
CHILDREN_KEY = "children"


@dataclass(frozen=True)
class RetrievalVerdict:
    """A validated retrieval-sufficiency verdict.

    Attributes
    ----------
    sufficient : bool
        Whether the accumulated pool answers the query.
    top_k : Optional[int]
        For an insufficient depth verdict, the retrieval size the next round
        should request. Must be at least ``1`` when present.
    children : Optional[List[int]]
        For an insufficient ensemble verdict, the child retriever indices to
        consult next. Indices must be at least ``0`` when present.
    """

    sufficient: bool
    top_k: Optional[int] = None
    children: Optional[List[int]] = None


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


def _validate_top_k(value: Any, raw: Any) -> int:
    """Validate the optional ``top_k`` field.

    Parameters
    ----------
    value : Any
        Raw ``top_k`` value from the parsed object.
    raw : Any
        Original payload (a string or a decoded mapping), echoed in the error
        message.

    Returns
    -------
    int
        The validated positive retrieval size.

    Raises
    ------
    RAGRetrieverEvaluationError
        If the value is not an integer greater than or equal to ``1``.
    """
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise RAGRetrieverEvaluationError(
            "'top_k' must be an integer greater than or equal to 1, got "
            f"{value!r}. Preview: {_preview(raw)}"
        )
    return value


def _validate_children(value: Any, raw: Any) -> List[int]:
    """Validate the optional ``children`` field.

    Parameters
    ----------
    value : Any
        Raw ``children`` value from the parsed object.
    raw : Any
        Original payload (a string or a decoded mapping), echoed in the error
        message.

    Returns
    -------
    List[int]
        The validated list of non-negative child indices (unchanged order).

    Raises
    ------
    RAGRetrieverEvaluationError
        If the value is not a list of integers greater than or equal to ``0``.
    """
    if not isinstance(value, list):
        raise RAGRetrieverEvaluationError(
            f"'children' must be a list of integers, got {type(value).__name__}. "
            f"Preview: {_preview(raw)}"
        )
    for index in value:
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            raise RAGRetrieverEvaluationError(
                "'children' must contain only integers greater than or equal to "
                f"0, got {index!r}. Preview: {_preview(raw)}"
            )
    return list(value)


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
        boolean, or an optional field is present with the wrong type/shape.
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

    top_k: int | None = None
    if TOP_K_KEY in parsed:
        top_k = _validate_top_k(parsed[TOP_K_KEY], raw)

    children: List[int] | None = None
    if CHILDREN_KEY in parsed:
        children = _validate_children(parsed[CHILDREN_KEY], raw)

    return RetrievalVerdict(
        sufficient=sufficient,
        top_k=top_k,
        children=children,
    )


def parse_evaluation_output(raw: str) -> RetrievalVerdict:
    """Parse the retrieval-sufficiency verdict out of raw model output.

    Markdown fences are stripped, the substring from the first ``{`` to the last
    ``}`` is taken, and the result must be a JSON object carrying a boolean
    ``sufficient`` field. The optional ``top_k`` and ``children`` fields are
    validated when present; unknown keys are ignored.

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
        an optional field is present with the wrong type/shape.
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


def require_for_depth(verdict: RetrievalVerdict) -> int:
    """Return the retrieval size an insufficient depth verdict requires.

    Parameters
    ----------
    verdict : RetrievalVerdict
        A verdict produced by :func:`parse_evaluation_output`.

    Returns
    -------
    int
        The requested retrieval size (contract field ``top_k``).

    Raises
    ------
    RAGRetrieverEvaluationError
        If the verdict is marked sufficient (the caller should have returned) or
        an insufficient verdict omits ``top_k``.
    """
    if verdict.sufficient:
        raise RAGRetrieverEvaluationError(
            "Expected an insufficient verdict with a retrieval size, but the "
            "verdict is marked sufficient."
        )
    if verdict.top_k is None:
        raise RAGRetrieverEvaluationError(
            "An insufficient depth evaluation must provide a positive 'top_k' "
            "retrieval size."
        )
    return verdict.top_k


def require_for_ensemble(verdict: RetrievalVerdict, child_count: int) -> List[int]:
    """Return the child indices an insufficient ensemble verdict selects.

    Duplicate indices are collapsed preserving their first-seen order. Every
    index must address a configured child.

    Parameters
    ----------
    verdict : RetrievalVerdict
        A verdict produced by :func:`parse_evaluation_output`.
    child_count : int
        Number of child retrievers available to the ensemble.

    Returns
    -------
    List[int]
        Deduplicated, order-preserving child indices.

    Raises
    ------
    RAGRetrieverEvaluationError
        If the verdict is marked sufficient, ``children`` is missing or empty,
        or any index is out of range for ``child_count``.
    """
    if verdict.sufficient:
        raise RAGRetrieverEvaluationError(
            "An ensemble evaluation over an empty pool must select children, "
            "but the verdict is marked sufficient."
        )
    children = verdict.children
    if not children:
        raise RAGRetrieverEvaluationError(
            "An insufficient ensemble evaluation must select a non-empty "
            "'children' list."
        )
    deduplicated: List[int] = []
    for index in children:
        if index < 0 or index >= child_count:
            raise RAGRetrieverEvaluationError(
                f"Child index {index} is out of range for {child_count} "
                "configured children."
            )
        if index not in deduplicated:
            deduplicated.append(index)
    return deduplicated
