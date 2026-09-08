"""Pure factory for text-to-text generation models (LLMs).

Resolves a component name + parameters into an instantiated model
via the component registry, without any database access.
DB concerns are handled by LLMService.
"""

from dataclasses import dataclass
from typing import Any

from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.exceptions import RAGComponentNotFoundError
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)


@dataclass(frozen=True)
class LLMFactoryResult:
    """Result of LLM instantiation via LLMFactory."""

    model: TextToTextGenerationTaskModel


class LLMFactory:
    """Creates LLM instances from the component registry."""

    def __init__(self, component_registry: ComponentRegistry):
        """Initialize the factory with a component registry.

        Args:
            component_registry: The component registry to resolve LLM
                components.
        """
        self._registry = component_registry

    def create(self, component_name: str, params: dict[str, Any]) -> LLMFactoryResult:
        """Build an LLM instance from a registered component.

        Args:
            component_name: Name of the registered LLM component.
            params: Parameters to pass to the model constructor.

        Returns:
            Contains only the instantiated model.

        Raises:
            RAGComponentNotFoundError: If the component_name is not found
                in the registry.
        """
        try:
            model_class = self._registry[component_name]["class"]
        except KeyError as err:
            raise RAGComponentNotFoundError(
                f"Component '{component_name}' not found in registry"
            ) from err

        if hasattr(model_class, "SCHEMA") and model_class.SCHEMA is not None:
            model_class.SCHEMA(**params)

        model = model_class(**params)
        return LLMFactoryResult(model=model)
