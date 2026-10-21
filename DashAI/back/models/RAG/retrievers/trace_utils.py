"""Trace helpers shared by every retriever.

A retriever's ``retrieve()`` returns ``(chunks, trace)``: the retrieved chunks
and a JSON-serializable *trace node* describing which chunks this retriever
returned and, for composite retrievers, which child nodes produced them.

Trace nodes always carry ``name`` and ``chunks`` and may carry an optional
``description`` (the component description per language) and ``representation``
(the retriever's representation template rendered against the raw construction
parameters captured by the factory, per language). Both optional keys are plain
JSON-serializable dictionaries; raw parameters and templates never reach the
frontend.

The chunk reference string built here is the **single source of truth** for the
join key between the trace and the pipeline's ``Dict`` output row: the pipeline
keys its chunk map by the exact same ``"<document_id>_<position>"`` string, so
the frontend can join a trace reference to a chunk's text/record without
duplicating the chunk payload. The join is a LEFT-OUTER lookup: trace nodes may
reference chunks that did not survive to the pipeline's final chunk map (for
example cascade stages of a sequential retriever or re-rank candidates), so a
missing reference resolves to nothing and is not an error.
"""

import logging
import re
from typing import Any, Dict, List

from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.documents import Chunk
from DashAI.back.models.RAG.retrievers.ref_utils import is_component_ref
from DashAI.back.models.RAG.retrievers.retrieval_contracts import SchemaSummary

log = logging.getLogger(__name__)

#: Text rendered when a representation placeholder cannot be resolved.
_MISSING_VALUE = "—"

#: Languages declared by :class:`MultilingualString`.
_LANGUAGES = ("en", "es", "pt", "de", "zh")

_PLACEHOLDER_RE = re.compile(r"\{([^{}]+)\}")

#: Trace keys populated from the model itself; extras may never shadow them.
_CANONICAL_KEYS = ("name", "chunks", "description", "representation", "schema_summary")


def _render_primitive(value: Any) -> str:
    """Render a scalar parameter value, or :data:`_MISSING_VALUE`."""
    if isinstance(value, (str, int, float, bool)):
        text = str(value)
        return text if text else _MISSING_VALUE
    return _MISSING_VALUE


def _resolve_param(params: Any, path: List[str]) -> str:
    """Resolve a dotted parameter path against raw construction parameters."""
    if not isinstance(params, dict) or not path:
        return _MISSING_VALUE

    head, *rest = path
    if not head:
        return _MISSING_VALUE
    raw = params.get(head)
    if raw is None:
        return _MISSING_VALUE

    ref = raw if is_component_ref(raw) else None
    if not rest:
        if ref is not None:
            return raw["component"] or _MISSING_VALUE
        return _render_primitive(raw)

    if ref is None:
        return _MISSING_VALUE
    return _resolve_param(ref.get("params"), rest)


def _render_template(template: str, params: Any) -> str | None:
    """Interpolate a representation template.

    A template without placeholders is returned as-is. A template whose
    placeholders all fail to resolve returns ``None`` so the frontend can fall
    back to the component description.
    """
    if not isinstance(template, str) or not template:
        return None

    saw_placeholder = False
    resolved_placeholder = False

    def replace(match: re.Match) -> str:
        nonlocal saw_placeholder, resolved_placeholder
        saw_placeholder = True
        path = [segment for segment in match.group(1).strip().split(".") if segment]
        value = _resolve_param(params, path) if path else _MISSING_VALUE
        if value != _MISSING_VALUE:
            resolved_placeholder = True
        return value

    rendered = _PLACEHOLDER_RE.sub(replace, template)
    if saw_placeholder and not resolved_placeholder:
        return None
    return rendered


def _multilingual_texts(value: Any) -> Dict[str, str]:
    """Collect the non-empty language entries of a description/representation."""
    if isinstance(value, MultilingualString):
        return {
            language: text
            for language in _LANGUAGES
            if isinstance(text := getattr(value, language), str) and text
        }
    if isinstance(value, dict):
        return {
            language: text
            for language, text in value.items()
            if language in _LANGUAGES and isinstance(text, str) and text
        }
    if isinstance(value, str) and value:
        return {"en": value}
    return {}


def _render_representation(model: Any) -> Dict[str, str] | None:
    """Render the class representation template against ``model._trace_params``."""
    templates = _multilingual_texts(type(model).get_representation())
    if not templates:
        return None

    params = getattr(model, "_trace_params", {})
    rendered = {
        language: text
        for language, template in templates.items()
        if (text := _render_template(template, params)) is not None
    }
    return rendered or None


def _serialize_description(model: Any) -> Dict[str, str] | None:
    """Serialize the description declared by the model's own class.

    Only a class that declares ``DESCRIPTION`` in its own ``__dict__`` yields a
    description, so anonymous test stubs inheriting the generic base
    description do not emit one.
    """
    description = _multilingual_texts(type(model).__dict__.get("DESCRIPTION"))
    return description or None


def _serialize_schema_summary(model: Any) -> SchemaSummary | None:
    """Return the model's recursive schema summary, or ``None`` on failure.

    Parameters
    ----------
    model : Any
        Retriever whose summary is serialized into the trace node.

    Returns
    -------
    SchemaSummary | None
        The summary, or ``None`` when the model exposes no summary method or
        raises while building it. Unexpected failures are logged so a broken
        retriever does not degrade traces silently.
    """
    getter = getattr(model, "get_schema_summary", None)
    if getter is None:
        return None
    try:
        return getter()
    except Exception:  # noqa: BLE001 - a broken summary must not break the trace
        log.warning(
            "Failed to build the schema summary for %s.",
            type(model).__name__,
            exc_info=True,
        )
        return None


def chunk_ref(chunk: Chunk) -> str:
    """Build the canonical reference string for a chunk.

    The format is ``f"<document_id>_<document_position>"`` — the SAME string the
    pipeline uses as the ``Dict`` output row key. Keeping the format here is what
    lets a trace node reference a chunk without repeating its text.

    Parameters
    ----------
    chunk : Chunk
        The chunk to reference.

    Returns
    -------
    str
        The ``"<document_id>_<position>"`` reference string.
    """
    return f"{chunk.document_id}_{chunk.document_position}"


def retriever_trace(model: Any, chunks: List[Chunk], **extras: Any) -> Dict[str, Any]:
    """Build a trace node describing one retriever's run.

    Parameters
    ----------
    model : Any
        The retriever instance that produced *chunks*; its class name becomes
        the node's ``name``. Its own ``DESCRIPTION`` and rendered
        representation, when declared, become localized dictionaries.
    chunks : List[Chunk]
        The chunks the retriever returned, in retrieval order. Their references
        become the node's ``chunks`` list.
    **extras : Any
        Technique-specific keys merged into the node (e.g. ``children`` for
        composites, ``scores`` for the cross-encoder). They cannot shadow the
        canonical ``name``, ``chunks``, ``description`` or ``representation``.

    Returns
    -------
    Dict[str, Any]
        A JSON-serializable trace node with ``name`` and ``chunks``, plus
        ``description`` and ``representation`` when available, whose references
        join the pipeline's ``Dict`` output row.
    """
    canonical = [key for key in _CANONICAL_KEYS if key in extras]
    if canonical:
        raise ValueError(
            "Trace node keys "
            + ", ".join(f"'{key}'" for key in canonical)
            + " are canonical and cannot be overridden by extras."
        )

    node: Dict[str, Any] = {
        "name": type(model).__name__,
        "chunks": [chunk_ref(chunk) for chunk in chunks],
    }

    description = _serialize_description(model)
    if description is not None:
        node["description"] = description

    representation = _render_representation(model)
    if representation is not None:
        node["representation"] = representation

    schema_summary = _serialize_schema_summary(model)
    if schema_summary is not None:
        node["schema_summary"] = schema_summary

    node.update(extras)
    return node
