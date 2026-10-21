"""Pure factory for chunking models.

Resolves a component name and parameters into a BaseChunkingModel instance.
"""

from dataclasses import dataclass
from typing import Any

from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.chunking_models.base_chunking_model import (
    BaseChunkingModel,
)
from DashAI.back.models.RAG.documents.chunk import Chunk
from DashAI.back.models.RAG.exceptions import RAGComponentNotFoundError


@dataclass(frozen=True)
class ChunkingFactoryResult:
    """A chunking model and the chunks of one chunk set.

    Attributes
    ----------
    model : BaseChunkingModel
        The instantiated chunking model.
    chunks : dict
        Chunks keyed by document id, then by position.
    """

    model: BaseChunkingModel
    chunks: dict[int, dict[int, Chunk]]


class ChunkingModelFactory:
    """Creates a chunking model from a registered component name."""

    def __init__(self, registry: ComponentRegistry):
        """Store the registry.

        Parameters
        ----------
        registry : ComponentRegistry
            Registry resolving chunking model classes by name.
        """
        self._registry = registry

    def create(self, component_name: str, params: dict[str, Any]) -> BaseChunkingModel:
        """Build a chunking model.

        Parameters
        ----------
        component_name : str
            Registered component name.
        params : dict
            Parameters passed to the model constructor.

        Returns
        -------
        BaseChunkingModel
            The instantiated model.

        Raises
        ------
        RAGComponentNotFoundError
            If the component is not registered.
        """
        try:
            model_class = self._registry[component_name]["class"]
        except KeyError as err:
            raise RAGComponentNotFoundError(
                f"Component '{component_name}' not found in registry"
            ) from err
        return model_class(**params)
