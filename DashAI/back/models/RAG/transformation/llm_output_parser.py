"""Robust parser for the function-calling output contract.

Models are asked for a single JSON object shaped like an OpenAI function
call. In practice they wrap it in prose or markdown fences, or they omit the
``{"name": ..., "arguments": ...}`` wrapper and return the arguments object
directly. This module tolerates all of that.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from DashAI.back.models.RAG.exceptions import RAGTransformationOutputError

#: Maximum number of characters of raw model output echoed in error messages.
_PREVIEW_LIMIT = 200

#: Matches opening and closing markdown code fences, with or without a language.
_FENCE_RE = re.compile(r"```[a-zA-Z0-9_-]*")


def _preview(raw: Any) -> str:
    """Return a short, truncated preview of the raw output.

    Parameters
    ----------
    raw : Any
        Raw model output.

    Returns
    -------
    str
        The output truncated to ``_PREVIEW_LIMIT`` characters, with a trailing
        ellipsis when truncation happened.
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
    RAGTransformationOutputError
        If no braces are present.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise RAGTransformationOutputError(
            "The model output does not contain a JSON object. Preview: "
            f"{_preview(text)}"
        )
    return text[start : end + 1]


def parse_function_call_output(
    raw: str,
    expected_name: str,
    argument_key: str,
) -> Dict[str, Any]:
    """Parse the function-calling contract out of raw model output.

    Parameters
    ----------
    raw : str
        Raw model output.
    expected_name : str
        Function name the technique expects; used in error messages.
    argument_key : str
        Argument key the technique expects; used in error messages.

    Returns
    -------
    Dict[str, Any]
        The arguments mapping. When the model emitted a full
        ``{"name", "arguments"}`` object, the ``arguments`` mapping is
        returned; otherwise the top-level object is returned.

    Raises
    ------
    RAGTransformationOutputError
        If the output contains no JSON object, the JSON is invalid, or the
        parsed value is not a mapping.
    """
    text = _FENCE_RE.sub("", str(raw)).strip()
    candidate = _extract_json_object(text)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as err:
        raise RAGTransformationOutputError(
            f"Failed to parse the '{expected_name}' output as JSON (expected "
            f"argument '{argument_key}'). Preview: {_preview(raw)}"
        ) from err
    if not isinstance(parsed, dict):
        raise RAGTransformationOutputError(
            f"The '{expected_name}' output is not a JSON object. Preview: "
            f"{_preview(raw)}"
        )
    # When the model emits the full wrapper, its function name must match the
    # technique's. A top-level object without "name" is the tolerated drift
    # (arguments-only or bare arguments) and stays on the permissive path.
    called_name = parsed.get("name")
    if "name" in parsed and called_name != expected_name:
        raise RAGTransformationOutputError(
            f"The model called '{called_name}' instead of the expected "
            f"'{expected_name}'. Preview: {_preview(raw)}"
        )
    arguments = parsed.get("arguments")
    if isinstance(arguments, dict):
        return arguments
    return parsed
