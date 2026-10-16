"""Robust parser for the function-calling output contract.

Models are asked for a single JSON object shaped like an OpenAI function
call. In practice they drift from that contract: they wrap it in prose or
markdown fences, serialize ``arguments`` as a JSON string, surround the call
with stray braces, or return the arguments object (or a bare list) directly.
This module tolerates all of that.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from DashAI.back.models.RAG.exceptions import RAGTransformationOutputError

#: Maximum number of characters of raw model output echoed in error messages.
_PREVIEW_LIMIT = 200

#: Matches opening and closing markdown code fences, with or without a language.
_FENCE_RE = re.compile(r"```[a-zA-Z0-9_-]*")

#: Upper bound on decoded candidates, to keep pathological outputs cheap.
_MAX_JSON_CANDIDATES = 64

#: Function-call protocol keys.
_NAME_KEY = "name"
_ARGUMENTS_KEY = "arguments"


def truncate_preview(value: Any) -> str:
    """Return a short, truncated preview of a value.

    Parameters
    ----------
    value : Any
        Value to render, typically raw model output.

    Returns
    -------
    str
        The value stringified and truncated to ``_PREVIEW_LIMIT`` characters,
        with a trailing ellipsis when truncation happened.
    """
    text = str(value)
    if len(text) <= _PREVIEW_LIMIT:
        return text
    return text[:_PREVIEW_LIMIT] + "..."


def _no_json_object_error(raw: Any) -> RAGTransformationOutputError:
    """Build the error reported when no JSON object is found.

    Parameters
    ----------
    raw : Any
        Raw model output.

    Returns
    -------
    RAGTransformationOutputError
        The error instance, echoing a truncated preview of the output.
    """
    return RAGTransformationOutputError(
        f"The model output does not contain a JSON object. "
        f"Preview: {truncate_preview(raw)}"
    )


def _failed_parse_error(
    expected_name: str, argument_key: str, raw: Any
) -> RAGTransformationOutputError:
    """Build the error reported when no candidate can be selected.

    Parameters
    ----------
    expected_name : str
        Function name the technique expects.
    argument_key : str
        Argument key the technique expects.
    raw : Any
        Raw model output.

    Returns
    -------
    RAGTransformationOutputError
        The error instance, echoing a truncated preview of the output.
    """
    return RAGTransformationOutputError(
        f"Failed to parse the '{expected_name}' output as JSON (expected "
        f"argument '{argument_key}'). Preview: {truncate_preview(raw)}"
    )


def resolve_arguments_dict(value: Any) -> Optional[Dict[str, Any]]:
    """Dereference an ``arguments`` value into a mapping when possible.

    Parameters
    ----------
    value : Any
        The value found under a candidate's ``arguments`` key.

    Returns
    -------
    Optional[Dict[str, Any]]
        The argument mapping when ``value`` is a dict, or when it is a string
        encoding a JSON object (OpenAI's tool-call wire format). ``None``
        otherwise.
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return None
        if isinstance(decoded, dict):
            return decoded
    return None


def _usable_name(candidate: Dict[str, Any]) -> Optional[str]:
    """Return a candidate's function name when it is a usable string.

    Parameters
    ----------
    candidate : Dict[str, Any]
        A decoded JSON object.

    Returns
    -------
    Optional[str]
        The ``name`` value when it is a non-empty string; ``None`` when the
        key is absent, not a string, or an empty string (treated as no name).
    """
    name = candidate.get(_NAME_KEY)
    return name if isinstance(name, str) and name else None


def _parse_bare_array(text: str) -> Optional[List[Any]]:
    """Decode the leading JSON array of ``text``, ignoring trailing prose.

    ``raw_decode`` stops at the array's closing bracket, so any prose after the
    array (for instance "hope that helps") is tolerated; the text needs only to
    *start* with the array, not to be exactly one.

    Parameters
    ----------
    text : str
        Text to scan, with fences already stripped.

    Returns
    -------
    Optional[List[Any]]
        The decoded list when ``text`` starts with a well-formed JSON array;
        ``None`` when the text does not start with ``[`` or is malformed.
    """
    if not text.startswith("["):
        return None
    try:
        value, _ = json.JSONDecoder().raw_decode(text, 0)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, list) else None


def _string_array_arguments(
    text: str, list_argument_key: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Wrap a leading bare string array under ``list_argument_key``.

    Parameters
    ----------
    text : str
        Text to scan, with fences already stripped.
    list_argument_key : str | None
        Argument key used to wrap the array; ``None`` disables the tolerance.

    Returns
    -------
    Optional[Dict[str, Any]]
        ``{list_argument_key: [...]}`` when a key was requested and every
        element of the leading array is a string; ``None`` otherwise (so the
        caller can raise the appropriate diagnostic).
    """
    if list_argument_key is None:
        return None
    array = _parse_bare_array(text)
    if array is None or not all(isinstance(item, str) for item in array):
        return None
    return {list_argument_key: array}


def _iter_json_objects(text: str) -> List[Dict[str, Any]]:
    """Decode the balanced JSON objects found in ``text``, in order.

    ``raw_decode`` is string- and balance-aware and ignores trailing prose, so
    scanning from every ``{`` recovers the intended call even when surrounding
    prose carries stray braces. Once an object decodes, scanning resumes after
    its closing brace so nested objects are not harvested as separate
    candidates; a failed decode only advances one character, which still lets a
    valid inner object rescue a malformed wrapper.

    Parameters
    ----------
    text : str
        Text to scan, with fences already stripped.

    Returns
    -------
    List[Dict[str, Any]]
        The decoded objects, capped at ``_MAX_JSON_CANDIDATES``.
    """
    decoder = json.JSONDecoder()
    objects: List[Dict[str, Any]] = []
    index = text.find("{")
    while index != -1 and len(objects) < _MAX_JSON_CANDIDATES:
        try:
            value, end = decoder.raw_decode(text, index)
        except json.JSONDecodeError:
            index = text.find("{", index + 1)
            continue
        if isinstance(value, dict):
            objects.append(value)
        index = text.find("{", end)
    return objects


def _match_named(
    candidate: Dict[str, Any], expected_name: str, argument_key: str
) -> Optional[Dict[str, Any]]:
    """Return the arguments of a matching named wrapper, else ``None``.

    A candidate matches when its ``name`` equals ``expected_name`` and it
    carries the expected argument either inside a resolvable ``arguments``
    mapping or directly under ``argument_key`` when no ``arguments`` key is
    present. A matching name with keyless arguments is deliberately rejected
    so it cannot shadow a later candidate.

    Parameters
    ----------
    candidate : Dict[str, Any]
        A decoded JSON object.
    expected_name : str
        Function name the technique expects.
    argument_key : str
        Argument key the technique expects.

    Returns
    -------
    Optional[Dict[str, Any]]
        The arguments mapping (or the candidate itself for the ``name`` plus
        bare ``argument_key`` form), otherwise ``None``.
    """
    if _usable_name(candidate) != expected_name:
        return None
    resolved = resolve_arguments_dict(candidate.get(_ARGUMENTS_KEY))
    if resolved is not None and argument_key in resolved:
        return resolved
    if _ARGUMENTS_KEY not in candidate and argument_key in candidate:
        return candidate
    return None


def _match_nameless_nonempty(
    candidate: Dict[str, Any], argument_key: str
) -> Optional[Dict[str, Any]]:
    """Return the arguments of a name-less candidate with a non-empty claim.

    A name-less candidate is accepted when its ``arguments`` resolve to a
    non-empty mapping (or one carrying ``argument_key``), or when it holds a
    non-empty value directly under ``argument_key``. Empty bare values are
    deliberately rejected here so a later non-empty candidate can win; they are
    handled last, purely to produce a precise diagnostic.

    Parameters
    ----------
    candidate : Dict[str, Any]
        A decoded JSON object.
    argument_key : str
        Argument key the technique expects.

    Returns
    -------
    Optional[Dict[str, Any]]
        The arguments mapping (or the candidate itself for the bare
        ``argument_key`` form), otherwise ``None``.
    """
    if _usable_name(candidate) is not None:
        return None
    resolved = resolve_arguments_dict(candidate.get(_ARGUMENTS_KEY))
    if resolved is not None and (resolved or argument_key in resolved):
        return resolved
    if _ARGUMENTS_KEY not in candidate and candidate.get(argument_key):
        return candidate
    return None


def _match_nameless_empty(
    candidate: Dict[str, Any], argument_key: str
) -> Optional[Dict[str, Any]]:
    """Return a name-less candidate holding an empty bare ``argument_key``.

    This is the last-resort form: it lets the technique raise its precise
    "does not contain a non-empty ..." message for a lone ``{"queries": []}``
    after every non-empty candidate has been ruled out.

    Parameters
    ----------
    candidate : Dict[str, Any]
        A decoded JSON object.
    argument_key : str
        Argument key the technique expects.

    Returns
    -------
    Optional[Dict[str, Any]]
        The candidate when it has no ``arguments`` key, carries
        ``argument_key``, and that value is empty; ``None`` otherwise.
    """
    if _usable_name(candidate) is not None:
        return None
    if _ARGUMENTS_KEY in candidate:
        return None
    if argument_key in candidate and not candidate.get(argument_key):
        return candidate
    return None


def _has_attempted_name(candidates: List[Dict[str, Any]], expected_name: str) -> bool:
    """Report whether any candidate names ``expected_name``.

    A named candidate that failed every selection pass still proves a real call
    was attempted, so the diagnosis must be a parse failure rather than an
    array or example being hijacked.

    Parameters
    ----------
    candidates : List[Dict[str, Any]]
        Decoded objects, in document order.
    expected_name : str
        Function name the technique expects.

    Returns
    -------
    bool
        ``True`` when a candidate's usable name equals ``expected_name``.
    """
    return any(_usable_name(candidate) == expected_name for candidate in candidates)


def _first_wrong_name(
    candidates: List[Dict[str, Any]], expected_name: str
) -> Optional[str]:
    """Return the first usable name that is not ``expected_name``.

    Parameters
    ----------
    candidates : List[Dict[str, Any]]
        Decoded objects, in document order.
    expected_name : str
        Function name the technique expects.

    Returns
    -------
    Optional[str]
        The first mismatching name, or ``None`` when every candidate is
        either name-less or correctly named.
    """
    for candidate in candidates:
        name = _usable_name(candidate)
        if name is not None and name != expected_name:
            return name
    return None


def _wrong_name_error(
    wrong_name: str, expected_name: str, raw: Any
) -> RAGTransformationOutputError:
    """Build the error reported when the model called another function.

    Parameters
    ----------
    wrong_name : str
        The function name the model actually used.
    expected_name : str
        Function name the technique expects.
    raw : Any
        Raw model output.

    Returns
    -------
    RAGTransformationOutputError
        The error instance, echoing a truncated preview of the output.
    """
    return RAGTransformationOutputError(
        f"The model called '{wrong_name}' instead of the expected "
        f"'{expected_name}'. Preview: {truncate_preview(raw)}"
    )


def _select_from_candidates(
    candidates: List[Dict[str, Any]],
    text: str,
    expected_name: str,
    argument_key: str,
    list_argument_key: Optional[str],
    raw: Any,
) -> Dict[str, Any]:
    """Select the highest-priority candidate when at least one exists.

    Priority order: a matching named wrapper, then a name-less non-empty
    claim, then the wrong-name / attempted-name diagnostics, then a leading
    bare string array, and finally the empty bare ``argument_key`` form kept
    so the technique can emit its precise error. Raises when none applies.

    Parameters
    ----------
    candidates : List[Dict[str, Any]]
        Decoded objects, in document order.
    text : str
        Fence-stripped output, used for the bare-array fallback.
    expected_name : str
        Function name the technique expects.
    argument_key : str
        Argument key the technique expects.
    list_argument_key : str | None
        Argument key used to wrap a tolerated bare array.
    raw : Any
        Raw model output, used for error previews.

    Returns
    -------
    Dict[str, Any]
        The selected arguments mapping.

    Raises
    ------
    RAGTransformationOutputError
        When no candidate can be selected.
    """
    for candidate in candidates:
        matched = _match_named(candidate, expected_name, argument_key)
        if matched is not None:
            return matched
    for candidate in candidates:
        matched = _match_nameless_nonempty(candidate, argument_key)
        if matched is not None:
            return matched
    wrong_name = _first_wrong_name(candidates, expected_name)
    if wrong_name is not None:
        raise _wrong_name_error(wrong_name, expected_name, raw)
    if _has_attempted_name(candidates, expected_name):
        raise _failed_parse_error(expected_name, argument_key, raw)
    wrapped = _string_array_arguments(text, list_argument_key)
    if wrapped is not None:
        return wrapped
    for candidate in candidates:
        matched = _match_nameless_empty(candidate, argument_key)
        if matched is not None:
            return matched
    raise _failed_parse_error(expected_name, argument_key, raw)


def parse_function_call_output(
    raw: str,
    expected_name: str,
    argument_key: str,
    *,
    list_argument_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Parse the function-calling contract out of raw model output.

    The stripped output is scanned for balanced JSON objects, which are then
    selected in two priority passes: a matching named wrapper first (the real
    answer), then a name-less non-empty arguments object (``arguments``
    present) or a bare ``argument_key`` mapping. A name-less example embedded
    in prose can therefore never outrank a later named call, and an empty
    ``argument_key`` never outranks a later non-empty one. When nothing is
    selectable, a leading top-level JSON array of strings is tolerated and
    wrapped when the technique requested the list form, whether or not stray
    braces appear elsewhere in the text.

    Parameters
    ----------
    raw : str
        Raw model output.
    expected_name : str
        Function name the technique expects; used in error messages.
    argument_key : str
        Argument key the technique expects; used in error messages.
    list_argument_key : str | None, optional
        When provided, a bare top-level JSON array is tolerated and wrapped as
        ``{list_argument_key: [...]}``. Used by the 1-to-n techniques only.

    Returns
    -------
    Dict[str, Any]
        The arguments mapping. When the model emitted a full
        ``{"name", "arguments"}`` object, the ``arguments`` mapping is
        returned; otherwise the top-level object is returned.

    Raises
    ------
    RAGTransformationOutputError
        If the output contains no JSON object, the JSON is invalid, the
        parsed value is not a mapping, or no candidate matches the expected
        function name.
    """
    text = _FENCE_RE.sub("", str(raw)).strip()
    has_brace = "{" in text
    candidates = _iter_json_objects(text) if has_brace else []

    if candidates:
        return _select_from_candidates(
            candidates, text, expected_name, argument_key, list_argument_key, raw
        )

    wrapped = _string_array_arguments(text, list_argument_key)
    if wrapped is not None:
        return wrapped
    if has_brace:
        raise _failed_parse_error(expected_name, argument_key, raw)
    raise _no_json_object_error(raw)
