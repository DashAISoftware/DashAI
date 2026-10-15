"""Pure factory for query transformer instances.

Resolves a component name and parameters into an instantiated transformer via
the component registry. Phase 1 only -- no I/O, no DB.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from DashAI.back.core.schema_fields.utils import fill_objects, normalize_payload
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.exceptions import (
    RAGComponentNotFoundError,
    RAGTransformationConfigError,
)
from DashAI.back.models.RAG.transformation.base_query_transformation import (
    BaseQueryTransformation,
)


@dataclass(frozen=True)
class TransformationFactoryResult:
    """Result of query transformer instantiation.

    Attributes
    ----------
    model : BaseQueryTransformation
        The fully constructed transformer instance.
    """

    model: BaseQueryTransformation


class TransformationFactory:
    """Creates query transformer instances from the component registry."""

    def __init__(self, registry: ComponentRegistry) -> None:
        """Initialize the factory with a component registry.

        Parameters
        ----------
        registry : ComponentRegistry
            The registry used to resolve prompt and LLM components.
        """
        self._registry = registry

    def create(
        self,
        component_name: str,
        params: dict[str, Any],
    ) -> TransformationFactoryResult:
        """Build a transformer instance from a registered component.

        Parameters
        ----------
        component_name : str
            Name of the registered transformer component.
        params : dict[str, Any]
            Transformer parameters, including the nested ``prompt`` and
            ``llm_model`` component references.

        Returns
        -------
        TransformationFactoryResult
            Wraps the constructed transformer.

        Raises
        ------
        RAGComponentNotFoundError
            If ``component_name`` is not registered.
        RAGTransformationConfigError
            If the resolved class is not a :class:`BaseQueryTransformation`.
        """
        params = normalize_payload(params)
        try:
            model_class = self._registry[component_name]["class"]
        except KeyError as err:
            raise RAGComponentNotFoundError(
                f"Query transformation component '{component_name}' not found "
                "in registry"
            ) from err

        if not issubclass(model_class, BaseQueryTransformation):
            raise RAGTransformationConfigError(
                f"Component '{component_name}' is not a query transformation."
            )

        validated = model_class.SCHEMA.model_validate(params)
        resolved = fill_objects(validated, self._registry)
        model = model_class(**resolved)
        return TransformationFactoryResult(model=model)
