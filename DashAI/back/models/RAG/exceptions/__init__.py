"""Unified RAG exception hierarchy.

All RAG-related exceptions live here.  Every layer — models, services,
factories, API endpoints, jobs — must import from this package when
raising or catching RAG exceptions so that callers can rely on a single
source of truth.

Exception tree (simplified)::

    RAGWorkflowError
    ├── RAGDocumentError
    │   ├── RAGDocumentParsingError
    │   ├── RAGDocumentNotFoundError
    │   ├── RAGDocumentFileTypeError
    │   └── RAGDocumentExtractionError
    ├── RAGChunkingError
    │   └── RAGChunkingOverlapError
    ├── RAGRetrieverError
    │   ├── RAGRetrieverMissingParameterError
    │   ├── RAGRetrieverCompositeValidationError
    │   └── RAGRetrieverEmptyChildrenError
    ├── RAGPromptError
    │   ├── RAGPromptValidationError
    │   └── RAGPromptTemplateError
    ├── RAGGenerationError
    │   └── RAGGenerationModelError
    ├── RAGPipelineError
    │   ├── RAGPipelineConfigError
    │   ├── RAGPipelineInitializationError
    │   ├── RAGPipelineRuntimeError
    │   ├── RAGPipelineInputError
    │   └── RAGDatabaseError
    ├── RAGEmbeddingError
    │   ├── RAGEmbeddingLoadError
    │   └── RAGEmbeddingEmptyInputError
    ├── RAGFactoryError
    │   └── RAGComponentNotFoundError
    └── RAGTaskError
        └── RAGTaskInputError
"""

from DashAI.back.models.RAG.exceptions.base import RAGWorkflowError
from DashAI.back.models.RAG.exceptions.chunking import (
    RAGChunkingError,
    RAGChunkingOverlapError,
)
from DashAI.back.models.RAG.exceptions.document import (
    RAGDocumentError,
    RAGDocumentExtractionError,
    RAGDocumentFileTypeError,
    RAGDocumentNotFoundError,
    RAGDocumentParsingError,
)
from DashAI.back.models.RAG.exceptions.embedding import (
    RAGEmbeddingEmptyInputError,
    RAGEmbeddingError,
    RAGEmbeddingLoadError,
)
from DashAI.back.models.RAG.exceptions.factory import (
    RAGComponentNotFoundError,
    RAGFactoryError,
)
from DashAI.back.models.RAG.exceptions.generation import (
    RAGGenerationError,
    RAGGenerationModelError,
)
from DashAI.back.models.RAG.exceptions.pipeline import (
    RAGDatabaseError,
    RAGPipelineConfigError,
    RAGPipelineError,
    RAGPipelineInitializationError,
    RAGPipelineInputError,
    RAGPipelineRuntimeError,
)
from DashAI.back.models.RAG.exceptions.prompt import (
    RAGPromptError,
    RAGPromptTemplateError,
    RAGPromptValidationError,
)
from DashAI.back.models.RAG.exceptions.retriever import (
    RAGRetrieverCompositeValidationError,
    RAGRetrieverEmptyChildrenError,
    RAGRetrieverError,
    RAGRetrieverMissingParameterError,
)
from DashAI.back.models.RAG.exceptions.task import (
    RAGTaskError,
    RAGTaskInputError,
)

__all__ = [
    # Base
    "RAGWorkflowError",
    # Document
    "RAGDocumentError",
    "RAGDocumentParsingError",
    "RAGDocumentNotFoundError",
    "RAGDocumentFileTypeError",
    "RAGDocumentExtractionError",
    # Chunking
    "RAGChunkingError",
    "RAGChunkingOverlapError",
    # Retriever
    "RAGRetrieverError",
    "RAGRetrieverMissingParameterError",
    "RAGRetrieverCompositeValidationError",
    "RAGRetrieverEmptyChildrenError",
    # Prompt
    "RAGPromptError",
    "RAGPromptValidationError",
    "RAGPromptTemplateError",
    # Generation
    "RAGGenerationError",
    "RAGGenerationModelError",
    # Pipeline
    "RAGPipelineError",
    "RAGPipelineConfigError",
    "RAGPipelineInitializationError",
    "RAGPipelineRuntimeError",
    "RAGPipelineInputError",
    "RAGDatabaseError",
    # Embedding
    "RAGEmbeddingError",
    "RAGEmbeddingLoadError",
    "RAGEmbeddingEmptyInputError",
    # Factory
    "RAGFactoryError",
    "RAGComponentNotFoundError",
    # Task
    "RAGTaskError",
    "RAGTaskInputError",
]
