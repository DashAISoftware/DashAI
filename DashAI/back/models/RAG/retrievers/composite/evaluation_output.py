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
TOP_K_KEY = "top_k"
CHILDREN_KEY = "children"


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


def _validate_top_k(value: Any, raw: str) -> int:
    """Validate the optional ``top_k`` field.

    Parameters
    ----------
    value : Any
        Raw ``top_k`` value from the parsed object.
    raw : str
        Original model output, echoed in the error message.

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


def _validate_children(value: Any, raw: str) -> List[int]:
    """Validate the optional ``children`` field.

    Parameters
    ----------
    value : Any
        Raw ``children`` value from the parsed object.
    raw : str
        Original model output, echoed in the error message.

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


def parse_evaluation_output(raw: str) -> Dict[str, Any]:
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
    Dict[str, Any]
        ``{"sufficient": bool, "top_k": int | None, "children": list[int] | None}``.

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
    if not isinstance(parsed, dict):
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

    return {
        SUFFICIENT_KEY: sufficient,
        TOP_K_KEY: top_k,
        CHILDREN_KEY: children,
    }


def require_for_depth(verdict: Dict[str, Any]) -> int:
    """Return the retrieval size an insufficient depth verdict requires.

    Parameters
    ----------
    verdict : Dict[str, Any]
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
    if verdict.get(SUFFICIENT_KEY):
        raise RAGRetrieverEvaluationError(
            "Expected an insufficient verdict with a retrieval size, but the "
            "verdict is marked sufficient."
        )
    top_k = verdict.get(TOP_K_KEY)
    if top_k is None:
        raise RAGRetrieverEvaluationError(
            "An insufficient depth evaluation must provide a positive 'top_k' "
            "retrieval size."
        )
    return top_k


def require_for_ensemble(verdict: Dict[str, Any], child_count: int) -> List[int]:
    """Return the child indices an insufficient ensemble verdict selects.

    Duplicate indices are collapsed preserving their first-seen order. Every
    index must address a configured child.

    Parameters
    ----------
    verdict : Dict[str, Any]
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
    if verdict.get(SUFFICIENT_KEY):
        raise RAGRetrieverEvaluationError(
            "An ensemble evaluation over an empty pool must select children, "
            "but the verdict is marked sufficient."
        )
    children = verdict.get(CHILDREN_KEY)
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
