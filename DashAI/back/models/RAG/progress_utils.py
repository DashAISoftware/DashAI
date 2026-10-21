"""Context-local progress channel for a single RAG pipeline run.

The RAG pipeline is synchronous and runs in one thread. It exposes its reporter
through a :class:`contextvars.ContextVar` so that deeply nested collaborators
(query transformers, LLM-evaluated retrievers) can publish short user-facing
status messages without threading a reporter parameter through every call.

This is deliberately a *context-local, single-threaded* channel: the context
variable is set by :func:`progress_scope` around one pipeline run and reset on
exit. A future threaded retriever would have to propagate the context explicitly
(``contextvars.copy_context()`` or an equivalent mechanism) because a plain
thread does not inherit it.

Messages and justifications are LLM-authored and therefore optional. When the
model omits them nothing is emitted, which keeps the existing stage-only payload
contract byte-identical.
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Callable, Dict, Iterator, Optional

from DashAI.back.models.RAG.RAG_constants import (
    RAG_PROGRESS_JUSTIFICATION_KEY,
    RAG_PROGRESS_MESSAGE_KEY,
    RAG_PROGRESS_STAGE_KEY,
)

#: Callback receiving one JSON-serializable progress payload.
ProgressReporter = Callable[[Dict[str, Any]], None]

#: The reporter of the current pipeline run, if any.
_current_reporter: ContextVar[Optional[ProgressReporter]] = ContextVar(
    "rag_progress_reporter", default=None
)

#: Matches any run of whitespace so payload text stays on one line.
_WHITESPACE_RE = re.compile(r"\s+")

#: Matches invisible format/bidi controls (zero-width spaces, BOM, RTL marks).
_INVISIBLE_RE = re.compile(
    r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u206f\ufeff]"
)

#: Sentinel used to detect truncation caps too small for an ellipsis.
_ELLIPSIS = "..."


def sanitize_text(value: str) -> str:
    """Remove characters that cannot be JSON/UTF-8 encoded safely.

    LLM output occasionally contains lone surrogates (which make
    ``json.dumps(..., ensure_ascii=False).encode("utf-8")`` fail) or invisible
    format/bidi controls (which render as an empty status line). Both are
    replaced or removed here before the text reaches a progress payload or a
    trace row.

    Parameters
    ----------
    value : str
        Text to sanitize.

    Returns
    -------
    str
        The text with lone surrogates replaced by ``"?"`` and invisible format
        controls removed.
    """
    text = value.encode("utf-8", "replace").decode("utf-8")
    return _INVISIBLE_RE.sub("", text)


def normalize_progress_text(value: Any, *, max_length: int = 600) -> str:
    """Normalize an optional LLM-authored progress string.

    Parameters
    ----------
    value : Any
        Candidate text. Only ``str`` values are accepted; anything else yields
        an empty string so ancillary model drift can never raise. Lone
        surrogates and invisible format controls are removed.
    max_length : int, optional
        Maximum length of the returned text. Values above the cap are truncated
        with a trailing ``"..."``. Defaults to ``600``.

    Returns
    -------
    str
        The whitespace-collapsed, stripped text, or ``""`` for non-strings,
        empty strings and whitespace-only strings.
    """
    if not isinstance(value, str):
        return ""
    text = _WHITESPACE_RE.sub(" ", sanitize_text(value)).strip()
    if not text:
        return ""
    if max_length <= 0:
        return ""
    if len(text) <= max_length:
        return text
    if max_length <= len(_ELLIPSIS):
        return text[:max_length]
    return text[: max_length - len(_ELLIPSIS)].rstrip() + _ELLIPSIS


@contextmanager
def progress_scope(reporter: Optional[ProgressReporter]) -> Iterator[None]:
    """Install ``reporter`` as the current progress channel for the block.

    Parameters
    ----------
    reporter : ProgressReporter or None
        Reporter invoked by :func:`report_progress`. ``None`` disables
        reporting for the block.

    Yields
    ------
    None
        The context is active only while the ``with`` block runs; the previous
        reporter is restored even when the block raises.
    """
    token = _current_reporter.set(reporter)
    try:
        yield
    finally:
        _current_reporter.reset(token)


def report_progress(
    stage: str,
    *,
    message: Optional[str] = None,
    justification: Optional[str] = None,
    **extras: Any,
) -> None:
    """Emit one progress payload to the reporter in scope.

    The payload always carries ``stage`` first, then ``message`` and/or
    ``justification`` only when they normalize to a non-empty string, then any
    ``extras``. ``stage``, ``message`` and ``justification`` are explicit
    parameters, so Python's argument binding already prevents ``extras`` from
    shadowing them.

    Parameters
    ----------
    stage : str
        Pipeline stage name, e.g. ``"retrieving"``.
    message : str or None, optional
        Optional user-facing status sentence.
    justification : str or None, optional
        Optional short rationale for the decision.
    **extras : Any
        Additional JSON-serializable payload keys (e.g. ``queries``).

    Returns
    -------
    None
        Nothing is emitted when no reporter is in scope.
    """
    reporter = _current_reporter.get()
    if reporter is None:
        return

    payload: Dict[str, Any] = {RAG_PROGRESS_STAGE_KEY: stage}
    normalized_message = normalize_progress_text(message)
    normalized_justification = normalize_progress_text(justification)
    if normalized_message:
        payload[RAG_PROGRESS_MESSAGE_KEY] = normalized_message
    if normalized_justification:
        payload[RAG_PROGRESS_JUSTIFICATION_KEY] = normalized_justification
    payload.update(extras)

    reporter(payload)
