"""Backend-resolved defaults for a RAG session.

``schema_field`` never sets a pydantic default, so historically the client had
to send a fully expanded configuration for all four RAG components. This module
resolves that configuration server-side, which is what lets a session be created
from just a name and a generation model.

The defaults are deliberately expressed as *presets* rather than loose parameter
bags: every default configuration therefore matches a named preset, so the
session view can always show a friendly label instead of a class name.
"""

from typing import Any, Dict, Optional

from DashAI.back.core.schema_fields.defaults import resolve_component_defaults
from DashAI.back.models.RAG.RAG_constants import (
    RAG_PARAM_CHUNKING_MODEL,
    RAG_PARAM_PROMPT,
    RAG_PARAM_RETRIEVER_MODEL,
)
from DashAI.back.services.RAG.chunking_presets import get_default_chunking
from DashAI.back.services.RAG.retriever_presets import get_default_retriever

#: Prompt used when the client does not choose one.
DEFAULT_PROMPT = "DefaultRAGGenerationPrompt"

#: Context window a RAG session assumes when the caller does not set one.
#:
#: Every text-generation model ships the same conservative ``context_window``
#: placeholder (512), which is far too small once retrieved chunks and a prompt
#: template are in play — no usable RAG configuration fits. The frontend used to
#: paper over this by overriding the value on model selection; the override
#: belongs here, where it applies to every client and is visible in the stored
#: configuration.
RAG_CONTEXT_WINDOW = 10000

#: Room a RAG session reserves for the answer itself, for the same reason.
RAG_MAX_TOKENS = 1000

#: Context window for the query-transformation stage's nested LLM.
#:
#: Model schemas ship a conservative 512 placeholder that cannot hold the
#: technique prompt plus the stage's own default two-message history. A
#: transformation call carries only that history block and the instructions —
#: never retrieved chunks — so it does not need the generation 10000 window,
#: but it needs far more than 512. Resolved server-side so every client sees
#: the value in the stored configuration.
RAG_TRANSFORMATION_LLM_CONTEXT_WINDOW = 2048

#: Languages the default prompt ships templates for.
_PROMPT_LANGUAGES = ("en", "es", "pt")


def _resolve_prompt_language(accept_language: Optional[str]) -> str:
    """Pick the default prompt language from an ``Accept-Language`` header.

    Falls back to English for any language the default prompt has no template
    for, so the resolved configuration is always valid.
    """
    code = (accept_language or "en").split(",")[0].split(";")[0].split("-")[0].lower()
    return code if code in _PROMPT_LANGUAGES else "en"


def build_default_parameters(
    registry, accept_language: Optional[str] = None
) -> Dict[str, Any]:
    """Return the default configuration for the components the user need not pick.

    ``generation_model`` is intentionally absent: it has no sensible default,
    so it stays required at session creation. ``documents`` is absent because a
    session starts empty and gains documents as they are uploaded into it.

    Parameters
    ----------
    registry : ComponentRegistry
        Registry used to resolve each component's schema placeholders.
    accept_language : str | None
        Request language, used to pick the default prompt template.

    Returns
    -------
    dict
        ``{chunking_model, retriever_model, prompt}``, each a fully resolved
        ``{"component": str, "params": dict}`` reference.
    """
    prompt_params = resolve_component_defaults(DEFAULT_PROMPT, registry)
    prompt_params["language"] = _resolve_prompt_language(accept_language)

    return {
        RAG_PARAM_CHUNKING_MODEL: get_default_chunking(registry),
        RAG_PARAM_RETRIEVER_MODEL: get_default_retriever(registry),
        RAG_PARAM_PROMPT: {"component": DEFAULT_PROMPT, "params": prompt_params},
    }


def generation_model_overrides() -> Dict[str, Any]:
    """Return the generation parameters a RAG session needs room for.

    Applied under anything the caller sends explicitly, so a user who sets
    their own context window keeps it.

    Returns
    -------
    dict
        ``{context_window, max_tokens}``.
    """
    return {
        "context_window": RAG_CONTEXT_WINDOW,
        "max_tokens": RAG_MAX_TOKENS,
    }


def transformation_llm_overrides() -> Dict[str, Any]:
    """Return the context window the query-transformation LLM needs.

    Applied under anything the caller sends explicitly, so a user who sets
    their own ``context_window`` keeps it. The window only has to cover the
    technique prompt plus the stage's history block, never retrieved chunks,
    hence 2048 rather than the generation 10000 window.

    Returns
    -------
    dict
        ``{context_window}``. Models without a ``context_window``-shaped
        parameter (for example DeepSeek's ``n_ctx``) ignore the extra key, the
        same way the generation overrides do.
    """
    return {
        "context_window": RAG_TRANSFORMATION_LLM_CONTEXT_WINDOW,
    }
