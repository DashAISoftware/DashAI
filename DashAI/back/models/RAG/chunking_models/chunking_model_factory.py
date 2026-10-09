"""Pure factory for chunking models.

Resolves a component name + parameters into a BaseChunkingModel instance
and chunks the provided documents. Phase 1 only — no DB access.
"""

from dataclasses import dataclass
from typing import Any

from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.chunking_models.base_chunking_model import (
    BaseChunkingModel,
)
from DashAI.back.models.RAG.documents.base_document import BaseDocument
from DashAI.back.models.RAG.documents.chunk import Chunk
from DashAI.back.models.RAG.exceptions import RAGComponentNotFoundError


@dataclass(frozen=True)
class ChunkingFactoryResult:
    """Result of a chunking model creation via :class:`ChunkingModelFactory`.

    Attributes:
        model: The instantiated chunking model.
        chunks: A dictionary mapping document IDs to their chunk dictionaries.
    """

    model: BaseChunkingModel
    chunks: dict[int, dict[int, Chunk]]


class ChunkingModelFactory:
    """Creates a chunking model and chunks documents. Phase 1 only — no DB."""

    def __init__(
        self,
        registry: ComponentRegistry,
        documents: dict[int, BaseDocument],
    ):
        """Initialize the factory with a component registry and document mapping.

        Args:
            registry: The component registry used to resolve chunking model
                classes by name.
            documents: A dictionary mapping document IDs to BaseDocument
                instances to be chunked.
        """
        self._registry = registry
        self._documents = documents

    def create(
        self,
        component_name: str,
        params: dict[str, Any],
    ) -> ChunkingFactoryResult:
        """Build a chunking model and chunk the documents.

        Parameters
        ----------
        component_name : str
            Registered component name.
        params : dict
            Parameters passed to the model constructor.

        Returns
        -------
        ChunkingFactoryResult
            The instantiated model and its chunk dictionary.
        """
        try:
            model_class = self._registry[component_name]["class"]
        except KeyError as err:
            raise RAGComponentNotFoundError(
                f"Component '{component_name}' not found in registry"
            ) from err

        model_params = {**params, "documents": self._documents}
        model = model_class(**model_params)
        model.compute_chunks()
        return ChunkingFactoryResult(model=model, chunks=model.get_chunks())
