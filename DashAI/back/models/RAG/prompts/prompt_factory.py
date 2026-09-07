"""Pure factory for prompt models. Phase 1 only — no DB."""

from dataclasses import dataclass
from typing import Any

from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.exceptions import RAGComponentNotFoundError
from DashAI.back.models.RAG.prompts import Prompt


@dataclass(frozen=True)
class PromptFactoryResult:
    """Result of prompt instantiation via PromptFactory."""

    model: Prompt


class PromptFactory:
    """Creates Prompt instances from the component registry."""

    def __init__(self, registry: ComponentRegistry):
        """Initialize the factory with a component registry.

        Args:
            registry: The component registry to resolve prompt components.
        """
        self._registry = registry

    def create(
        self, component_name: str, params: dict[str, Any]
    ) -> PromptFactoryResult:
        """Build a Prompt instance from a registered component.

        Args:
            component_name: Name of the registered prompt component.
            params: Parameters to pass to the prompt constructor.

        Returns:
            Contains only the instantiated Prompt model.

        Raises:
            RAGComponentNotFoundError: If the component_name is not found
                in the registry.
        """
        try:
            prompt_class = self._registry[component_name]["class"]
        except KeyError as err:
            raise RAGComponentNotFoundError(
                f"Prompt component '{component_name}' not found in registry"
            ) from err

        if hasattr(prompt_class, "SCHEMA") and prompt_class.SCHEMA is not None:
            prompt_class.SCHEMA(**params)

        model = prompt_class(**params)
        return PromptFactoryResult(model=model)
