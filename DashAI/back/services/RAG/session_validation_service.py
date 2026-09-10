"""Validation service for RAG session parameters.

Centralises all RAG-specific parameter validation for both session
creation (POST) and parameter updates (PUT), keeping the endpoint
layer thin and the validation logic testable in isolation.

Usage
-----
    validation_svc = RAGSessionValidationService(db, component_registry)

    # For session creation (all keys required):
    validated = validation_svc.prepare_RAG_params(raw_params)

    # For parameter updates (partial payloads allowed):
    validated = validation_svc.validate_update_payload(update_params)
"""

import logging
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from DashAI.back.core.component_validation import (
    find_component_refs,
    validate_component_refs,
)
from DashAI.back.core.schema_fields.defaults import resolve_component_defaults
from DashAI.back.core.schema_fields.utils import normalize_payload
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.prompts.generation.default_QA_RAG_generation_prompt import (
    DefaultQARAGGenerationPrompt,
)
from DashAI.back.models.RAG.prompts.generation.default_RAG_generation_prompt import (
    DefaultRAGGenerationPrompt,
)
from DashAI.back.models.RAG.RAG_constants import (
    RAG_MODEL_KEYS,
    RAG_PARAM_GENERATION_MODEL,
)
from DashAI.back.services.RAG.document_service import DocumentService
from DashAI.back.services.RAG.prompt_service import PromptService
from DashAI.back.services.RAG.session_defaults_service import (
    build_default_parameters,
    generation_model_overrides,
)

log = logging.getLogger(__name__)

DEFAULT_PROMPT_NAMES = frozenset(
    {
        DefaultRAGGenerationPrompt.__name__,
        DefaultQARAGGenerationPrompt.__name__,
    }
)


class SessionValidationService:
    """Validates and normalises RAG session parameters.

    Provides two entry points with different strictness levels:

    - **prepare_RAG_params** — for session creation (POST): all model
      keys are required.
    - **validate_update_payload** — for session updates (PUT): only
      provided keys are validated (partial updates).

    Both methods raise ``ValueError`` on the first validation failure
    with a human-readable message suitable for a 400 response.
    """

    def __init__(
        self,
        db: Session,
        registry: ComponentRegistry,
    ):
        """Initialise the validation service.

        Parameters
        ----------
        db : Session
            SQLAlchemy session for DB lookups (documents, prompts).
        registry : ComponentRegistry
            Application component registry.
        """
        self._db = db
        self._registry = registry
        self._prompt_service = PromptService(db, registry)
        self._document_service = DocumentService(db, registry)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def prepare_RAG_params(  # noqa: N802
        self,
        raw_params: dict[str, Any],
        accept_language: str | None = None,
    ) -> dict[str, Any]:
        """Validate and normalise parameters for a *new* RAG session.

        Only ``documents`` and ``generation_model`` are required: neither has a
        sensible default. ``chunking_model``, ``retriever_model`` and ``prompt``
        are filled in from the backend defaults when the caller omits them, so a
        session can be created from just a name, its documents and a model.

        Parameters
        ----------
        raw_params : dict
            Raw ``parameters`` payload from the create request.
        accept_language : str | None
            Request language, used to pick the default prompt template.

        Returns
        -------
        dict
            Normalised and validated parameters dict, with
            ``prompt_id`` resolved to ``prompt`` if applicable.

        Raises
        ------
        ValueError
            If any validation check fails.
        """
        normalized = normalize_payload(dict(raw_params))

        # ── 0a. Fill in the components the user does not have to choose ──
        # Only keys the caller actually omitted are defaulted; anything sent
        # explicitly wins, including an explicit ``None`` being rejected later.
        defaults = build_default_parameters(self._registry, accept_language)
        if "prompt_id" in normalized:
            defaults.pop("prompt", None)
        normalized = {**defaults, **normalized}

        # ── 0b. Resolve prompt_id early (before structure validation) ──
        # The caller may provide prompt_id (an integer FK) instead of a full
        # prompt component ref.  Convert it *before* validating model keys so
        # that prompt_id is transparently treated as prompt.
        if "prompt_id" in normalized:
            self._prompt_service.validate_prompt_exists(normalized["prompt_id"])
            prompt_id = normalized.pop("prompt_id")
            prompt = self._prompt_service.resolve_prompt_id_to_component(prompt_id)
            normalized["prompt"] = prompt

        # ── 1. Validate structure of every model key (defaults applied) ──
        self._validate_model_keys(normalized, require_all=True)

        # ── 2. Validate components exist in registry ──
        component_errors = validate_component_refs(normalized, self._registry)
        if component_errors:
            raise ValueError("; ".join(component_errors))

        # ── 2b. Fill in the picked generation model's parameters ──
        self._apply_generation_model_defaults(normalized)

        # ── 3. Strictly validate every component's params against its schema ──
        param_errors = self._validate_component_params(normalized)
        if param_errors:
            raise ValueError("; ".join(param_errors))

        # ── 4. Validate documents ──
        self._validate_documents(normalized)

        # ── 5. Validate prompt template placeholders ──
        if "prompt" in normalized:
            self._prompt_service.validate_component_ref(normalized["prompt"])

        return normalized

    def validate_update_payload(
        self,
        new_params: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate a partial RAG parameter update payload.

        Only the keys present in ``new_params`` are validated; missing
        keys are allowed (partial update semantics).

        Parameters
        ----------
        new_params : dict
            Raw update payload from the request body.

        Returns
        -------
        dict
            Normalised and validated params dict, with ``prompt_id``
            resolved to ``prompt`` if applicable.

        Raises
        ------
        ValueError
            If any validation check fails.
        """
        normalized = normalize_payload(dict(new_params))

        # ── 0. Resolve prompt_id early (before schema validation) ──
        # Mirror the POST flow: resolve prompt_id to a ``{component, params}``
        # ref BEFORE validating component schemas so the resolved prompt is
        # validated against its own schema (strict contract on updates too).
        if "prompt_id" in normalized:
            self._prompt_service.validate_prompt_exists(normalized["prompt_id"])
            normalized["prompt"] = self._prompt_service.resolve_prompt_id_to_component(
                normalized["prompt_id"]
            )
            del normalized["prompt_id"]

        # ── 1. Validate structure of provided model keys ──
        self._validate_model_keys(normalized, require_all=False)

        # ── 2. Validate components exist in registry ──
        component_errors = validate_component_refs(normalized, self._registry)
        if component_errors:
            raise ValueError("; ".join(component_errors))

        # ── 2b. Fill in the picked generation model's parameters ──
        self._apply_generation_model_defaults(normalized)

        # ── 3. Strictly validate every component's params against its schema ──
        param_errors = self._validate_component_params(normalized)
        if param_errors:
            raise ValueError("; ".join(param_errors))

        # ── 4. Validate documents if provided ──
        if "documents" in normalized:
            self._validate_documents(normalized)

        # ── 5. Validate prompt component ref (already resolved in step 0) ──
        if "prompt" in normalized:
            self._prompt_service.validate_component_ref(normalized["prompt"])

        return normalized

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_model_keys(
        self,
        normalized: dict[str, Any],
        require_all: bool,
    ) -> None:
        """Check each RAG model key has ``{component, params}`` structure.

        Parameters
        ----------
        normalized : dict
            Normalised parameters dict.
        require_all : bool
            When ``True`` every key in ``_RAG_MODEL_KEYS`` must be
            present; when ``False`` missing keys are skipped.

        Raises
        ------
        ValueError
            If structure validation fails.
        """
        for key in RAG_MODEL_KEYS:
            if key not in normalized:
                if require_all:
                    raise ValueError(f"Missing required parameter '{key}'.")
                continue
            ref = normalized[key]
            if not isinstance(ref, dict):
                raise ValueError(f"'{key}' must be a dict, got {type(ref).__name__}.")
            if "component" not in ref:
                raise ValueError(f"Missing 'component' in '{key}'.")
            if "params" not in ref:
                raise ValueError(f"Missing 'params' in '{key}'.")
            if not isinstance(ref["params"], dict):
                raise ValueError(
                    f"'params' of '{key}' must be a dict, got "
                    f"{type(ref['params']).__name__}."
                )

    def _apply_generation_model_defaults(self, normalized: dict[str, Any]) -> None:
        """Fill the generation model's missing params from its schema.

        The generation model is the one component a user picks *by name*: the
        creation flow asks which model to use, not how to tune it. Its
        parameters are therefore resolved here, from the same schema
        placeholders the parameter form would have shown. Whatever the caller
        does send wins; only omitted keys are filled.

        Scoped deliberately to this one key. Chunking, retrieval and the prompt
        arrive as complete recipes (see
        :mod:`DashAI.back.services.RAG.session_defaults_service`), and a
        partially-specified retriever is a caller bug worth reporting rather
        than silently papering over — one such bug is covered by
        ``test_auto_save_partial_data_rejected``.

        Parameters
        ----------
        normalized : dict
            Normalised parameters dict, mutated in place.
        """
        ref = normalized.get(RAG_PARAM_GENERATION_MODEL)
        if not isinstance(ref, dict):
            return
        name = ref.get("component")
        params = ref.get("params")
        if not name or not isinstance(params, dict):
            return
        defaults = resolve_component_defaults(name, self._registry)
        # RAG-specific overrides sit between the schema placeholders and what
        # the caller sent: they widen the context window a RAG pipeline needs,
        # without overriding a value the caller chose.
        ref["params"] = {**defaults, **generation_model_overrides(), **params}

    def _validate_component_params(self, normalized: dict[str, Any]) -> list[str]:
        """Validate every ``{component, params}`` against its own schema.

        Recursively walks ``normalized`` (via :func:`find_component_refs`) so
        nested sub-components such as the ``BM25VectorizerModel`` inside a
        ``BM25Retriever`` are also validated.

        The only tolerated incomplete payload is the default prompts
        (``DefaultRAGGenerationPrompt`` / ``DefaultQARAGGenerationPrompt``)
        with a language-only ``{"language": ...}`` body: the template is
        injected from the component's ``metadata["templates"]`` *before*
        validation and written back into ``normalized`` so the session
        stores the resolved template. No other component may rely on
        backend-provided defaults.

        Parameters
        ----------
        normalized : dict
            Normalised parameters dict (mutated in place when a default
            prompt template is injected).

        Returns
        -------
        list[str]
            Human-readable error messages (empty list means every
            component validated successfully).
        """
        errors: list[str] = []
        # Process nested refs in reverse (children before parents) so the
        # write-back of a child's normalised types survives the parent's
        # ``model_dump`` (which replaces the nested dict).
        for path, name, params in reversed(find_component_refs(normalized)):
            try:
                component = self._registry[name]
            except KeyError:
                continue  # already reported by validate_component_refs
            schema = component["class"].SCHEMA
            if schema is None:
                continue
            candidate = dict(params)
            template = candidate.get("template")
            if name in DEFAULT_PROMPT_NAMES and not (
                isinstance(template, str) and template.strip()
            ):
                # Default prompts are the ONLY tolerated incomplete payload:
                # inject the language template before validating so an empty,
                # whitespace-only or absent template can never be persisted
                # (it would fail at runtime in ``Prompt.format``).
                templates = getattr(component["class"], "metadata", {}).get("templates")
                language = candidate.get("language")
                if templates and language and language in templates:
                    candidate["template"] = templates[language]
                    params["template"] = candidate["template"]
                # A missing/unknown language is left for the schema to reject.
            try:
                validated = schema.model_validate(candidate)
                params.update(validated.model_dump(exclude_unset=True))
            except ValidationError as e:
                errors.append(f"Invalid parameters for '{name}' at '{path}': {e}")
        return errors

    def _validate_documents(self, normalized: dict[str, Any]) -> None:
        """Check documents list is non-empty and all IDs exist in DB.

        Parameters
        ----------
        normalized : dict
            Normalised parameters dict (must contain ``documents``).

        Raises
        ------
        ValueError
            If documents are empty, not all integers, or any ID is
            missing from the database.
        """
        docs = normalized.get("documents", [])
        if not docs:
            raise ValueError("Documents list must not be empty.")
        if not all(isinstance(d, int) for d in docs):
            raise ValueError("Documents must be a list of integers.")
        self._document_service.validate_exist(docs)
