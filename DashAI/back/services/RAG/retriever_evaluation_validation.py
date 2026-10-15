"""Validation for the LLM-evaluated composite retrievers.

Single-responsibility service extracted from ``SessionValidationService``. It
owns the structural and class checks for the nested ``llm_model`` and
``prompt`` references of the LLM-evaluated retrievers and resolves their
schema defaults. Prompt-template validation is injected as a callable so this
class never reaches into ``PromptService`` internals.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List

from DashAI.back.core.schema_fields.defaults import resolve_component_defaults
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.prompts.evaluation import RetrievalSufficiencyPrompt
from DashAI.back.models.RAG.RAG_constants import (
    LLM_EVALUATED_RETRIEVER_NAMES,
    RAG_PARAM_RETRIEVER_MODEL,
)
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)

log = logging.getLogger(__name__)

#: Default sufficiency prompts whose ``template`` may be injected from
#: ``metadata["templates"]`` before schema validation, exactly like the default
#: generation and transformation prompts.
DEFAULT_SUFFICIENCY_PROMPT_NAMES = frozenset({"DefaultRetrievalSufficiencyPrompt"})

#: Nested retriever-parameter keys, hoisted to avoid magic strings.
_PROMPT_KEY = "prompt"
_LLM_MODEL_KEY = "llm_model"


class RetrieverEvaluationValidationService:
    """Validates the nested refs of an LLM-evaluated composite retriever.

    ``validate`` performs the full structural plus class check (prompt family
    and ``llm_model`` subclass enforcement, plus template validation through the
    injected callable). ``apply_defaults`` resolves the nested LLM's and
    prompt's omitted parameters from their schemas.
    """

    def __init__(
        self,
        registry: ComponentRegistry,
        prompt_validator: Callable[[str, str], None],
    ):
        """Initialise the validator.

        Parameters
        ----------
        registry : ComponentRegistry
            Application component registry.
        prompt_validator : Callable[[str, str], None]
            ``PromptService.validate_prompt_template`` injected as a
            dependency; called as ``(component_name, template)`` and raises
            when the template is invalid.
        """
        self._registry = registry
        self._prompt_validator = prompt_validator

    def validate(self, retriever_ref: Dict[str, Any]) -> None:
        """Validate an LLM-evaluated retriever's nested references.

        The retriever must be a ``{component, params}`` dict with a registered
        outer component. Its nested ``prompt`` must be a component reference to
        a :class:`RetrievalSufficiencyPrompt` (or the retriever's declared
        ``EVALUATION_PROMPT_BASE``) and its nested ``llm_model`` a registered
        :class:`TextToTextGenerationTaskModel`. A caller-provided nested prompt
        template is validated here; default templates are injected later by the
        validation service's component-params pass.

        Parameters
        ----------
        retriever_ref : Dict[str, Any]
            The ``retriever_model`` reference, read-only here.

        Raises
        ------
        ValueError
            If the reference is present but malformed.
        """
        where = f"'{RAG_PARAM_RETRIEVER_MODEL}'"
        if not isinstance(retriever_ref, dict):
            raise ValueError(
                f"{where} must be a dict, got {type(retriever_ref).__name__}."
            )
        component_name = retriever_ref.get("component")
        if not isinstance(component_name, str):
            raise ValueError(f"Missing or invalid 'component' in {where}.")
        params = retriever_ref.get("params")
        if not isinstance(params, dict):
            raise ValueError(f"Missing or invalid 'params' in {where}.")
        if component_name not in self._registry:
            raise ValueError(
                f"Component '{component_name}' at {where} is not registered."
            )
        component_class = self._registry[component_name]["class"]

        self._validate_prompt(component_class, component_name, params, where)
        self._validate_llm(params, where)
        log.debug("LLM-evaluated retriever enabled with %s", component_class.__name__)

    def apply_defaults(self, retriever_ref: Dict[str, Any]) -> None:
        """Fill the retriever's omitted nested params from their schemas.

        The retriever's own schema placeholders plus the nested LLM's and
        prompt's placeholders are resolved server-side, sitting *under*
        whatever the caller sent. The resolved default prompt template is later
        injected from its language-driven defaults by the component-params
        pass.

        Parameters
        ----------
        retriever_ref : Dict[str, Any]
            The ``retriever_model`` reference, mutated in place only when the
            shape allows it.
        """
        if not isinstance(retriever_ref, dict):
            return
        name = retriever_ref.get("component")
        params = retriever_ref.get("params")
        if not name or not isinstance(params, dict):
            return

        merged = {**resolve_component_defaults(name, self._registry), **params}
        llm_ref = merged.get(_LLM_MODEL_KEY)
        if isinstance(llm_ref, dict):
            llm_name = llm_ref.get("component")
            llm_params = llm_ref.get("params")
            if llm_name and isinstance(llm_params, dict):
                llm_ref["params"] = {
                    **resolve_component_defaults(llm_name, self._registry),
                    **llm_params,
                }
        prompt_ref = merged.get(_PROMPT_KEY)
        if isinstance(prompt_ref, dict):
            prompt_name = prompt_ref.get("component")
            prompt_params = prompt_ref.get("params")
            if prompt_name and isinstance(prompt_params, dict):
                prompt_ref["params"] = {
                    **resolve_component_defaults(prompt_name, self._registry),
                    **prompt_params,
                }
        retriever_ref["params"] = merged

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_prompt(
        self,
        component_class: type,
        component_name: str,
        params: Dict[str, Any],
        where: str,
    ) -> None:
        """Validate the nested prompt reference and its family.

        Parameters
        ----------
        component_class : type
            The resolved outer retriever class.
        component_name : str
            The outer retriever component name.
        params : Dict[str, Any]
            The retriever params dict.
        where : str
            Human-readable location used in error messages.

        Raises
        ------
        ValueError
            If the prompt reference is missing, unregistered, of the wrong
            family or carries a malformed template.
        """
        prompt_where = f"{where}.params.{_PROMPT_KEY}"
        prompt_ref = params.get(_PROMPT_KEY)
        if not isinstance(prompt_ref, dict) or "component" not in prompt_ref:
            raise ValueError(
                f"'{_PROMPT_KEY}' is required in {where} and must be a "
                "component reference."
            )
        prompt_name = prompt_ref["component"]
        if not isinstance(prompt_name, str):
            raise ValueError(
                f"'component' of {prompt_where} must be a string, got "
                f"{type(prompt_name).__name__}."
            )
        prompt_class = self._resolve_subclass(
            prompt_name, RetrievalSufficiencyPrompt, prompt_where
        )
        prompt_base = getattr(
            component_class, "EVALUATION_PROMPT_BASE", RetrievalSufficiencyPrompt
        )
        if not issubclass(prompt_class, prompt_base):
            raise ValueError(
                f"Retriever '{component_name}' requires a prompt of type "
                f"{prompt_base.__name__} family, got {prompt_class.__name__}."
            )

        prompt_params = prompt_ref.get("params")
        if prompt_params is not None and not isinstance(prompt_params, dict):
            raise ValueError(
                f"'params' of {prompt_where} must be a dict, got "
                f"{type(prompt_params).__name__}."
            )
        template = (
            prompt_params.get("template") if isinstance(prompt_params, dict) else None
        )
        self._validate_nested_template(prompt_name, template)

    def _validate_llm(self, params: Dict[str, Any], where: str) -> None:
        """Validate the nested LLM reference.

        Parameters
        ----------
        params : Dict[str, Any]
            The retriever params dict.
        where : str
            Human-readable location used in error messages.

        Raises
        ------
        ValueError
            If the LLM reference is missing, unregistered, of the wrong type
            or carries a malformed params container.
        """
        llm_where = f"{where}.params.{_LLM_MODEL_KEY}"
        llm_ref = params.get(_LLM_MODEL_KEY)
        if not isinstance(llm_ref, dict) or "component" not in llm_ref:
            raise ValueError(
                f"'{_LLM_MODEL_KEY}' is required in {where} and must be a "
                "component reference."
            )
        llm_name = llm_ref["component"]
        if not isinstance(llm_name, str):
            raise ValueError(
                f"'component' of {llm_where} must be a string, got "
                f"{type(llm_name).__name__}."
            )
        self._resolve_subclass(llm_name, TextToTextGenerationTaskModel, llm_where)
        llm_params = llm_ref.get("params")
        if llm_params is not None and not isinstance(llm_params, dict):
            raise ValueError(
                f"'params' of {llm_where} must be a dict, got "
                f"{type(llm_params).__name__}."
            )

    def _validate_nested_template(self, prompt_name: str, template: Any) -> None:
        """Validate the nested sufficiency prompt's ``template`` value.

        Default sufficiency prompts may omit or blank their template: the
        language-driven template is injected later by the component-params pass
        (see ``SessionValidationService._validate_component_params``). Any
        other prompt must carry a non-blank string template with the required
        placeholders.

        Parameters
        ----------
        prompt_name : str
            Registered prompt component name.
        template : Any
            The raw ``template`` value sent for the prompt, or ``None`` when
            the key is absent.

        Raises
        ------
        ValueError
            If the template is not a string, or is blank/absent for a
            non-default prompt.
        """
        where = f"{RAG_PARAM_RETRIEVER_MODEL}.params.{_PROMPT_KEY}.params.template"
        is_default = prompt_name in DEFAULT_SUFFICIENCY_PROMPT_NAMES
        is_blank = template is None or (
            isinstance(template, str) and not template.strip()
        )
        if is_blank:
            if is_default:
                return
            raise ValueError(
                f"'{where}' must not be blank; provide a template containing "
                "the required placeholders."
            )
        if not isinstance(template, str):
            raise ValueError(
                f"'{where}' must be a string, got {type(template).__name__}."
            )
        self._prompt_validator(prompt_name, template)

    def _resolve_subclass(self, name: str, base: type, where: str) -> type:
        """Resolve ``name`` in the registry and assert it derives from ``base``.

        Parameters
        ----------
        name : str
            Registered component name.
        base : type
            Required ancestor class.
        where : str
            Human-readable location used in the error message.

        Returns
        -------
        type
            The resolved component class.

        Raises
        ------
        ValueError
            If the component is unregistered or not a subclass of ``base``.
        """
        if name not in self._registry:
            raise ValueError(f"Component '{name}' at '{where}' is not registered.")
        klass = self._registry[name]["class"]
        if not issubclass(klass, base):
            raise ValueError(
                f"Component '{name}' at '{where}' must be a {base.__name__}."
            )
        return klass


__all__: List[str] = [
    "DEFAULT_SUFFICIENCY_PROMPT_NAMES",
    "LLM_EVALUATED_RETRIEVER_NAMES",
    "RetrieverEvaluationValidationService",
]
