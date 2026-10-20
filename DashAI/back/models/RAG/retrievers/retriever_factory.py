"""Pure factory for retriever instances.

Builds retriever models from the component registry.
Phase 1 only -- no I/O (embeddings, similarity matrices).
"""

import copy
from dataclasses import dataclass
from typing import Any

from DashAI.back.core.schema_fields.utils import fill_objects, normalize_payload
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.documents.chunk import Chunk
from DashAI.back.models.RAG.exceptions import (
    RAGComponentNotFoundError,
    RAGRetrieverError,
    RAGRetrieverMissingParameterError,
)
from DashAI.back.models.RAG.exceptions.retriever import RAGRetrieverEvaluationError
from DashAI.back.models.RAG.llm_factory import LLMFactory
from DashAI.back.models.RAG.prompts.evaluation import RetrievalSufficiencyPrompt
from DashAI.back.models.RAG.prompts.prompt_factory import PromptFactory
from DashAI.back.models.RAG.retrievers.base_retriever import BaseRetriever
from DashAI.back.models.RAG.retrievers.composite.composite_retriever import (
    CompositeRetriever,
)
from DashAI.back.models.RAG.retrievers.dense.dense_retriever import DenseRetriever
from DashAI.back.models.RAG.retrievers.persistence import (
    DensePersistence,
    SparsePersistence,
)
from DashAI.back.models.RAG.retrievers.sparse.sparse_retriever import SparseRetriever
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)

#: Parameter keys recognized as nested ``{component, params}`` references.
_LLM_MODEL_KEY = "llm_model"
_PROMPT_KEY = "prompt"


def _is_component_ref(value: Any) -> bool:
    """Return whether ``value`` is a ``{component, params}`` reference dict."""
    return isinstance(value, dict) and "component" in value and "params" in value


def _resolve_llm(
    component: str,
    params: dict[str, Any],
    registry: ComponentRegistry,
    llm_resolver: Any,
) -> TextToTextGenerationTaskModel:
    """Instantiate a nested ``llm_model`` reference and type-check it.

    Parameters
    ----------
    component : str
        Registered LLM component name.
    params : dict[str, Any]
        LLM constructor parameters.
    registry : ComponentRegistry
        Application component registry (pure path).
    llm_resolver : Any
        Optional callable ``(component, params) -> result`` returning an object
        with a ``model`` attribute. When ``None``, :class:`LLMFactory` is used.

    Returns
    -------
    TextToTextGenerationTaskModel
        The instantiated model.

    Raises
    ------
    RAGRetrieverEvaluationError
        If the resolved object is not a text-to-text generation model.
    """
    if llm_resolver is not None:
        model = llm_resolver(component, params).model
    else:
        model = LLMFactory(registry).create(component, params).model
    if not isinstance(model, TextToTextGenerationTaskModel):
        raise RAGRetrieverEvaluationError(
            f"Component '{component}' for '{_LLM_MODEL_KEY}' must be a "
            "TextToTextGenerationTaskModel."
        )
    return model


def _resolve_prompt(
    component: str, params: dict[str, Any], registry: ComponentRegistry
) -> RetrievalSufficiencyPrompt:
    """Instantiate a nested ``prompt`` reference and type-check it.

    Parameters
    ----------
    component : str
        Registered prompt component name.
    params : dict[str, Any]
        Prompt constructor parameters.
    registry : ComponentRegistry
        Application component registry.

    Returns
    -------
    RetrievalSufficiencyPrompt
        The instantiated prompt.

    Raises
    ------
    RAGRetrieverEvaluationError
        If the resolved object is not a retrieval-sufficiency prompt.
    """
    model = PromptFactory(registry).create(component, params).model
    if not isinstance(model, RetrievalSufficiencyPrompt):
        raise RAGRetrieverEvaluationError(
            f"Component '{component}' for '{_PROMPT_KEY}' must be a "
            "RetrievalSufficiencyPrompt."
        )
    return model


def resolve_component_params(
    model_class: type,
    params: dict[str, Any],
    registry: ComponentRegistry,
    llm_resolver: Any = None,
) -> dict[str, Any]:
    """Resolve the nested component references declared in ``COMPONENT_PARAMS``.

    For every key listed in ``model_class.COMPONENT_PARAMS`` whose value is a
    ``{component, params}`` reference, the reference is instantiated (through
    :class:`LLMFactory`/``llm_resolver`` for ``llm_model`` and through
    :class:`PromptFactory` for ``prompt``) and the resulting live instance
    replaces the dict. Every other key is left untouched, so composites with an
    empty ``COMPONENT_PARAMS`` behave exactly as before.

    Parameters
    ----------
    model_class : type
        The retriever class about to be constructed.
    params : dict[str, Any]
        Raw construction parameters. Not mutated.
    registry : ComponentRegistry
        Application component registry.
    llm_resolver : Any
        Optional DB-backed resolver used by the setup service; when omitted the
        pure :class:`LLMFactory` path is used.

    Returns
    -------
    dict[str, Any]
        A new params mapping with resolved component instances.
    """
    resolved = dict(params)
    for key in getattr(model_class, "COMPONENT_PARAMS", ()):
        value = resolved.get(key)
        if not _is_component_ref(value):
            continue
        component = value["component"]
        sub_params = value["params"]
        if key == _LLM_MODEL_KEY:
            resolved[key] = _resolve_llm(component, sub_params, registry, llm_resolver)
        elif key == _PROMPT_KEY:
            resolved[key] = _resolve_prompt(component, sub_params, registry)
    return resolved


@dataclass(frozen=True)
class RetrieverFactoryResult:
    """Result of building a retriever via :class:`RetrieverFactory`.

    Attributes:
        model: The fully constructed :class:`BaseRetriever` instance.
    """

    model: BaseRetriever


class RetrieverFactory:
    """Creates retriever instances. Phase 1 only — no I/O.

    Builds retriever models from the component registry, handling both
    unit (leaf) and composite retrievers.  Schema validation and
    infrastructure injection are performed during construction.

    Args:
        registry: Application component registry for resolving
            component name strings.
        RAG_path: Root path for RAG data storage.
        chunks: Nested mapping of document IDs to chunk IDs to
            :class:`Chunk` instances.
    """

    def __init__(
        self,
        registry: ComponentRegistry,
        RAG_path: str,  # noqa: N803
        chunks: dict[int, dict[int, Chunk]],
    ):
        self._registry = registry
        self._RAG_path = RAG_path
        self._chunks = chunks

    def create(
        self,
        component_name: str,
        params: dict[str, Any],
        persistence: DensePersistence | SparsePersistence | None = None,
    ) -> RetrieverFactoryResult:
        params = normalize_payload(params)
        # Composite creation pops ``children`` from the mapping, so snapshot the
        # raw configuration first for trace representation rendering.
        trace_params = copy.deepcopy(params)
        try:
            model_class = self._registry[component_name]["class"]
        except KeyError as err:
            raise RAGComponentNotFoundError(
                f"Component '{component_name}' not found in registry"
            ) from err

        if issubclass(model_class, CompositeRetriever):
            result = self._create_composite(model_class, params)
        else:
            result = self._create_unit(model_class, params, persistence)

        result.model.set_trace_params(trace_params)
        return result

    def _create_composite(self, model_class, params) -> RetrieverFactoryResult:
        """Build a composite retriever by recursively creating children.

        Args:
            model_class: The :class:`CompositeRetriever` subclass to
                instantiate.
            params: Configuration parameters; the ``children`` key is
                consumed and replaced with built :class:`BaseRetriever`
                instances.

        Returns:
            A :class:`RetrieverFactoryResult` wrapping the new composite.
        """
        children_configs = params.pop("children", [])
        children_instances = [
            self.create(c["component"], c["params"]).model for c in children_configs
        ]
        params["children"] = children_instances
        params = resolve_component_params(model_class, params, self._registry)
        model = model_class(**params)
        return RetrieverFactoryResult(model=model)

    def _create_unit(
        self,
        model_class,
        params,
        persistence: DensePersistence | SparsePersistence | None = None,
    ) -> RetrieverFactoryResult:
        """Build a unit (leaf) retriever with schema validation and injection.

        Args:
            model_class: The :class:`UnitRetriever` subclass to instantiate.
            params: Configuration parameters validated against the
                model's schema.
            persistence: A :class:`DensePersistence` or
                :class:`SparsePersistence` instance matching the
                retriever type.

        Returns:
            A :class:`RetrieverFactoryResult` wrapping the new unit retriever.

        Raises:
            RAGRetrieverMissingParameterError: If the required persistence
                type is not provided for the retriever class.
            RAGRetrieverError: If the model class is neither a dense nor
                sparse retriever.
        """
        validated = model_class.SCHEMA.model_validate(params)
        resolved = fill_objects(validated, self._registry)
        model = model_class(**resolved)

        if issubclass(model_class, DenseRetriever):
            if not isinstance(persistence, DensePersistence):
                raise RAGRetrieverMissingParameterError(
                    "A DensePersistence is required for dense retrievers "
                    "but none was provided."
                )
            model.inject_infra(self._RAG_path, self._chunks, persistence)
        elif issubclass(model_class, SparseRetriever):
            if not isinstance(persistence, SparsePersistence):
                raise RAGRetrieverMissingParameterError(
                    "A SparsePersistence is required for sparse retrievers "
                    "but none was provided."
                )
            model.inject_infra(self._RAG_path, self._chunks, persistence)
        else:
            raise RAGRetrieverError(
                f"Unsupported unit retriever: {model_class.__name__}"
            )

        return RetrieverFactoryResult(model=model)
