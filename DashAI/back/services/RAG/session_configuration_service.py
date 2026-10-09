"""Human-readable view of a RAG session's configuration.

A session stores raw component class names (``CharacterChunkModel``,
``ParallelRetriever``) and snake_case parameter keys. Rendering those directly
is what made the creation form and the session view speak two different
vocabularies. This service resolves the stored configuration into the same
friendly vocabulary the pickers use — display names, preset labels, parameter
labels and a precomputed context budget — so the frontend never has to keep a
translation table of its own.

Everything it returns is read-only and derived; nothing here mutates a session.
"""

import logging
from typing import Any, Dict, List, Optional

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import GenerativeSession
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.RAG_constants import (
    RAG_PARAM_CHUNKING_MODEL,
    RAG_PARAM_GENERATION_MODEL,
    RAG_PARAM_PROMPT,
    RAG_PARAM_RETRIEVER_MODEL,
)
from DashAI.back.services.RAG import chunking_presets, retriever_presets
from DashAI.back.services.RAG.session_defaults_service import (
    RAG_CONTEXT_WINDOW,
    RAG_MAX_TOKENS,
)

log = logging.getLogger(__name__)

#: Characters per token, for turning prompt text into a token estimate.
CHARS_PER_TOKEN = 4

_SECTION_NAMES = {
    RAG_PARAM_CHUNKING_MODEL: MultilingualString(
        en="Chunking",
        es="Fragmentación",
        pt="Fragmentação",
        de="Chunking",
        zh="切分",
    ),
    RAG_PARAM_RETRIEVER_MODEL: MultilingualString(
        en="Retrieval",
        es="Recuperación",
        pt="Recuperação",
        de="Abruf",
        zh="检索",
    ),
    RAG_PARAM_PROMPT: MultilingualString(
        en="Prompt",
        es="Prompt",
        pt="Prompt",
        de="Prompt",
        zh="提示词",
    ),
    RAG_PARAM_GENERATION_MODEL: MultilingualString(
        en="Model",
        es="Modelo",
        pt="Modelo",
        de="Modell",
        zh="模型",
    ),
}


class SessionConfigurationService:
    """Resolves a stored RAG configuration into labels the UI can render."""

    def __init__(self, db, registry: ComponentRegistry):
        """Initialise the service.

        Parameters
        ----------
        db : Session
            SQLAlchemy session used to load the generative session.
        registry : ComponentRegistry
            Registry providing display names, descriptions and schemas.
        """
        self._db = db
        self._registry = registry

    # ── Public API ────────────────────────────────────────────────────

    def get_configuration(self, session_id: int) -> Dict[str, Any]:
        """Return the resolved configuration of a RAG session.

        Parameters
        ----------
        session_id : int
            The generative session to describe.

        Returns
        -------
        dict
            One entry per RAG component plus ``context_budget``. Multilingual
            values are returned as :class:`MultilingualString`; the caller
            localizes them.

        Raises
        ------
        ValueError
            If the session does not exist.
        """
        session = self._db.get(GenerativeSession, session_id)
        if session is None:
            raise ValueError(f"Generative session {session_id} does not exist.")

        parameters = dict(session.parameters or {})
        chunking = parameters.get(RAG_PARAM_CHUNKING_MODEL) or {}
        retriever = parameters.get(RAG_PARAM_RETRIEVER_MODEL) or {}
        prompt = parameters.get(RAG_PARAM_PROMPT) or {}
        generation = parameters.get(RAG_PARAM_GENERATION_MODEL) or {}

        return {
            RAG_PARAM_CHUNKING_MODEL: self._describe_chunking(chunking),
            RAG_PARAM_RETRIEVER_MODEL: self._describe_retriever(retriever),
            RAG_PARAM_PROMPT: self._describe_prompt(prompt),
            RAG_PARAM_GENERATION_MODEL: self._describe_generation(generation),
            "context_budget": self._context_budget(
                chunking, retriever, prompt, generation
            ),
        }

    # ── Per-section descriptions ──────────────────────────────────────

    def _describe_chunking(self, ref: Dict[str, Any]) -> Dict[str, Any]:
        """Describe the chunking component, naming its preset when it has one."""
        section = self._describe_component(RAG_PARAM_CHUNKING_MODEL, ref)
        component = ref.get("component") or ""
        params = ref.get("params") or {}
        preset_key = chunking_presets.match_preset_key(component, params)
        section["preset_key"] = preset_key
        section["preset_display_name"] = self._chunking_preset_name(preset_key)
        chunk_size = params.get("chunk_size")
        if isinstance(chunk_size, int):
            section["summary"] = self._chunk_size_summary(component, chunk_size)
        return section

    def _describe_retriever(self, ref: Dict[str, Any]) -> Dict[str, Any]:
        """Describe the retriever component, naming its preset when it has one."""
        section = self._describe_component(RAG_PARAM_RETRIEVER_MODEL, ref)
        component = ref.get("component") or ""
        params = ref.get("params") or {}
        preset_key: Optional[str] = None
        try:
            preset_key = retriever_presets.match_preset_key(
                component, params, self._registry
            )
        except Exception:  # pragma: no cover - a stale preset must not 500
            log.exception("Retriever preset matching failed for %s", component)
        section["preset_key"] = preset_key
        section["preset_display_name"] = self._retriever_preset_name(preset_key)
        section["top_k"] = retriever_presets.effective_top_k(component, params)
        return section

    def _describe_prompt(self, ref: Dict[str, Any]) -> Dict[str, Any]:
        """Describe the prompt component."""
        return self._describe_component(RAG_PARAM_PROMPT, ref)

    def _describe_generation(self, ref: Dict[str, Any]) -> Dict[str, Any]:
        """Describe the generation model, including availability.

        Download and credential state come straight from the registry, so the
        session view can gate on the same facts the model picker does instead of
        guessing from the class name.
        """
        section = self._describe_component(RAG_PARAM_GENERATION_MODEL, ref)
        component = ref.get("component") or ""
        entry = self._registry_entry(component)
        if entry is None:
            section["requires_download"] = False
            section["downloaded"] = False
            section["credentials_satisfied"] = True
            section["required_credentials"] = []
            return section

        model_class = entry["class"]
        requires_download = bool(getattr(model_class, "REQUIRES_DOWNLOAD", False))
        section["requires_download"] = requires_download
        section["downloaded"] = (
            self._registry.refresh_download_status(component)
            if requires_download
            else True
        )
        section["credentials_satisfied"] = bool(
            entry.get("credentials_satisfied", True)
        )
        section["required_credentials"] = list(entry.get("required_credentials") or [])
        return section

    # ── Shared building blocks ────────────────────────────────────────

    def _registry_entry(self, component: str) -> Optional[Dict[str, Any]]:
        """Return a registry entry, or ``None`` when the component is unknown.

        A component can legitimately disappear — an uninstalled plugin, a
        renamed class — and an old session still references it. Reporting it as
        unknown keeps the endpoint useful instead of failing the whole page.
        """
        if not component or component not in self._registry:
            return None
        return self._registry[component]

    def _describe_component(self, key: str, ref: Dict[str, Any]) -> Dict[str, Any]:
        """Build the common part of a section: names, description, parameters."""
        component = ref.get("component") or ""
        params = ref.get("params") or {}
        entry = self._registry_entry(component)

        if entry is None:
            return {
                "section_name": _SECTION_NAMES[key],
                "component": component,
                # Falling back to the raw name is the one place a class name may
                # surface, and only when nothing better exists.
                "display_name": component or None,
                "description": None,
                "registered": False,
                "params": self._describe_params(None, params),
            }

        return {
            "section_name": _SECTION_NAMES[key],
            "component": component,
            "display_name": entry.get("display_name") or component,
            "description": entry.get("description"),
            "registered": True,
            "params": self._describe_params(entry.get("schema"), params),
        }

    def _describe_params(
        self, schema: Optional[Dict[str, Any]], params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Pair each stored parameter with its label and description.

        Labels come from the schema ``title`` that ``schema_field``'s ``alias``
        feeds, so the UI never has to prettify a snake_case key itself.
        """
        properties = (schema or {}).get("properties") or {}
        described = []
        for name, value in params.items():
            prop = properties.get(name) or {}
            described.append(
                {
                    "name": name,
                    "label": prop.get("title") or name,
                    "description": prop.get("description"),
                    "value": value,
                    "is_component": isinstance(value, dict) and "component" in value,
                }
            )
        return described

    def _chunking_preset_name(self, key: Optional[str]) -> Optional[MultilingualString]:
        """Return the display name of a chunking preset key."""
        if key is None:
            return None
        for preset in chunking_presets.get_chunking_presets(self._registry):
            if preset["key"] == key:
                return preset["display_name"]
        return None

    def _retriever_preset_name(
        self, key: Optional[str]
    ) -> Optional[MultilingualString]:
        """Return the display name of a retriever preset key."""
        if key is None:
            return None
        for preset in retriever_presets.get_retriever_presets(10, self._registry):
            if preset["key"] == key:
                return preset["display_name"]
        return None

    def _chunk_size_summary(
        self, component: str, chunk_size: int
    ) -> MultilingualString:
        """Summarise a chunk size in the unit the chunker actually counts in."""
        if self._chunk_unit(component) == "tokens":
            return MultilingualString(
                en=f"{chunk_size} tokens",
                es=f"{chunk_size} tokens",
                pt=f"{chunk_size} tokens",
                de=f"{chunk_size} Tokens",
                zh=f"{chunk_size} 标记",
            )
        tokens = chunking_presets.estimate_tokens(chunk_size)
        return MultilingualString(
            en=f"{chunk_size} characters ≈ {tokens} tokens",
            es=f"{chunk_size} caracteres ≈ {tokens} tokens",
            pt=f"{chunk_size} caracteres ≈ {tokens} tokens",
            de=f"{chunk_size} Zeichen ≈ {tokens} Tokens",
            zh=f"{chunk_size} 字符 ≈ {tokens} 标记",
        )

    def _chunk_unit(self, component: str) -> str:
        """Return whether a chunker counts characters or tokens."""
        entry = self._registry_entry(component)
        if entry is None:
            return "characters"
        return getattr(entry["class"], "CHUNK_UNIT", "characters")

    # ── Context budget ────────────────────────────────────────────────

    def _chunk_tokens(self, chunking: Dict[str, Any]) -> int:
        """Return the token cost of a single retrieved chunk."""
        params = chunking.get("params") or {}
        chunk_size = params.get("chunk_size")
        if not isinstance(chunk_size, int):
            return 0
        if self._chunk_unit(chunking.get("component") or "") == "tokens":
            return chunk_size
        return chunking_presets.estimate_tokens(chunk_size)

    def _context_budget(
        self,
        chunking: Dict[str, Any],
        retriever: Dict[str, Any],
        prompt: Dict[str, Any],
        generation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute how much of the model's context window is already spoken for.

        The frontend used to do this arithmetic in two duplicated components, one
        of which was fed zeroes and so always reported "valid". Computing it here
        means the session view and the creation flow agree by construction.
        """
        generation_params = generation.get("params") or {}
        context_window = generation_params.get("context_window")
        if not isinstance(context_window, int):
            context_window = RAG_CONTEXT_WINDOW
        max_tokens = generation_params.get("max_tokens")
        if not isinstance(max_tokens, int):
            max_tokens = RAG_MAX_TOKENS

        top_k = retriever_presets.effective_top_k(
            retriever.get("component") or "", retriever.get("params") or {}
        )
        used_by_chunks = self._chunk_tokens(chunking) * top_k

        template = (prompt.get("params") or {}).get("template") or ""
        used_by_prompt = len(template) // CHARS_PER_TOKEN

        available = context_window - used_by_chunks - used_by_prompt - max_tokens
        return {
            "context_window": context_window,
            "max_tokens": max_tokens,
            "used_by_chunks": used_by_chunks,
            "used_by_prompt": used_by_prompt,
            "available": max(0, available),
            "is_valid": available > 0,
        }
