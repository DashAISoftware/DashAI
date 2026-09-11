import logging
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from sqlalchemy.orm import Session

from DashAI.back.dependencies.database.models import RAGPipeline as PipelineDBModel
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.RAG.chunking_models.base_chunking_model import (
    BaseChunkingModel,
)
from DashAI.back.models.RAG.chunking_models.chunking_model_factory import (
    ChunkingFactoryResult,
)
from DashAI.back.models.RAG.documents import BaseDocument, Chunk
from DashAI.back.models.RAG.prompts.prompt import Prompt
from DashAI.back.models.RAG.RAG_models_factory import RAGModelsFactory
from DashAI.back.models.RAG.RAG_pipeline import RAGPipeline, RAGPipelineConfig
from DashAI.back.models.RAG.retrievers.retriever_model import RetrieverModel
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)
from DashAI.back.services.RAG.chunking_service import ChunkingService
from DashAI.back.services.RAG.document_service import DocumentService
from DashAI.back.services.RAG.llm_service import LLMService
from DashAI.back.services.RAG.prompt_service import PromptService
from DashAI.back.services.RAG.retriever_setup_service import (
    RetrieverSetupResult,
    RetrieverSetupService,
)

log = logging.getLogger(__name__)

#: Called at each indexing checkpoint with ``(fraction, message)``. ``fraction``
#: is 0-1, or None when the remaining work is unknown.
ProgressFn = Callable[[Optional[float], Optional[str]], None]


@dataclass(frozen=True)
class IndexResult:
    """Everything the indexing half of the pipeline produces.

    Deliberately holds no generation model: an indexing run must not load LLM
    weights, so this is the widest result a caller can get without one.
    """

    pipeline_id: int
    chunk_set_id: int
    documents: Dict[int, BaseDocument]
    chunking_model_id: int
    chunking: ChunkingFactoryResult
    retriever: RetrieverSetupResult
    total_chunks: int


class SetupService:
    """Assembles RAG pipeline components into a ready-to-use RAGPipeline instance.

    Does NOT execute ``generate()`` — only assembly.  Each sub-component
    is built via the corresponding service class so that DB persistence
    and model instantiation are handled consistently.

    This service receives **pre-validated** configuration (use
    :class:`RAGSessionValidationService` for parameter validation).
    """

    def __init__(
        self,
        db: Session,
        registry: ComponentRegistry,
        RAG_path: str,  # noqa: N803
    ):
        """Initialize the setup service with DB and registry.

        Args:
            db: SQLAlchemy session.
            registry: Application component registry.
            RAG_path: Base RAG data directory path.
        """
        self._db = db
        self._registry = registry
        self._RAG_path = RAG_path

        self._documents = DocumentService(db, registry)
        self._chunking = ChunkingService(db, registry)
        self._prompts = PromptService(db, registry)
        self._llm = LLMService(db, registry)

    def build_index(
        self,
        config: RAGPipelineConfig,
        progress: Optional[ProgressFn] = None,
    ) -> IndexResult:
        """Build everything that makes a session's documents retrievable.

        Sequence
        --------
        1. Ensure pipeline DB record exists (get or create)
        2. Load documents from the database
        3. Get or create the chunk set (identity via SHA-256 signature)
        4. Create the chunking model and persist chunks
        5. Setup the retriever (dense embedding / sparse / composite)

        This stops short of the generation model on purpose:
        :meth:`LLMService.get_or_create` *instantiates* the LLM, and indexing
        must never load model weights it will not use.

        Every step is content-addressed, so calling this when nothing changed
        is a cheap no-op that reuses the cached chunk set and retriever.

        Parameters
        ----------
        config : RAGPipelineConfig
            Typed pipeline configuration.
        progress : Optional[ProgressFn]
            Called at each checkpoint with ``(fraction, message)``. Kept as a
            plain callable so this service stays independent of the job system.

        Returns
        -------
        IndexResult
            The persisted index and the in-memory models built along the way.

        Raises
        ------
        ValueError
            If any referenced document, component or parameter is invalid.
        RuntimeError
            If a database error occurs.
        """
        report = progress or (lambda fraction, message: None)

        report(0.02, "Preparing the index")
        pipeline_id = self._ensure_db_record(config.session_id)

        report(0.08, "Loading documents")
        documents = self._documents.load(config.documents)

        chunk_set = self._chunking.get_or_create_chunk_set(
            config.documents,
            {
                "chunking_model": {
                    "component": config.chunking_model.component,
                    "params": config.chunking_model.params,
                }
            },
        )

        report(0.20, "Splitting documents into chunks")
        chunking_record_id, chunking_result = self._chunking.create(
            documents,
            chunk_set.id,
            config.chunking_model.component,
            config.chunking_model.params,
        )

        report(0.45, "Building the retriever")
        retriever_service = RetrieverSetupService(
            self._db,
            self._registry,
            self._RAG_path,
            chunking_result.chunks,
            chunk_set.id,
            pipeline_id,
        )
        retriever_result = retriever_service.setup(
            config.retriever_model.component,
            config.retriever_model.params,
        )

        report(1.0, "Index ready")
        return IndexResult(
            pipeline_id=pipeline_id,
            chunk_set_id=chunk_set.id,
            documents=documents,
            chunking_model_id=chunking_record_id,
            chunking=chunking_result,
            retriever=retriever_result,
            total_chunks=sum(len(c) for c in chunking_result.chunks.values()),
        )

    def build_pipeline(self, config: RAGPipelineConfig) -> RAGPipeline:
        """Assemble a complete RAG pipeline from configuration.

        Sequence
        --------
        1-5. Build the index (delegated to :meth:`build_index`)
        6. Get or create the LLM record
        7. Resolve the prompt component and persist it
        8. Update the pipeline DB record with FK component IDs
        9. Build and return the ``RAGPipeline`` instance

        Parameters
        ----------
        config : RAGPipelineConfig
            Typed pipeline configuration.

        Returns
        -------
        RAGPipeline
            Fully assembled pipeline ready for ``generate()``.

        Raises
        ------
        ValueError
            If any referenced document, component or parameter is invalid.
        RuntimeError
            If a database error occurs.
        """
        index = self.build_index(config)

        llm_result = self._llm.get_or_create(
            config.generation_model.component,
            config.generation_model.params,
        )

        models_factory = RAGModelsFactory(self._registry)
        prompt_result = models_factory.create_prompt(
            config.prompt.component,
            config.prompt.params,
        )
        prompt_model = prompt_result.model
        prompt_response = self._prompts.get_or_create(
            class_name=config.prompt.component,
            name=f"pipeline_{config.session_id}_{config.prompt.component}",
            parameters=config.prompt.params,
        )

        self._update_db_record(
            config.session_id,
            index.chunking_model_id,
            prompt_response.id,
            llm_result.db_record_id,
        )

        pipeline = self._assemble_pipeline_instance(
            config=config,
            pipeline_id=index.pipeline_id,
            documents=index.documents,
            prompt_model=prompt_model,
            chunking_model_id=index.chunking_model_id,
            chunking_model=index.chunking.model,
            chunks=index.chunking.chunks,
            retriever=index.retriever.model,
            llm_model=llm_result.model,
        )
        return pipeline

    # ── Private helpers ───────────────────────────────────────────────

    def _ensure_db_record(self, session_id: int) -> int:
        """Get or create pipeline DB record, return its ID.

        Creates a placeholder row with nullable FK columns; these are
        patched later in ``_update_db_record``.

        Parameters
        ----------
        session_id : int
            Generative session identifier.

        Returns
        -------
        int
            Primary key of the pipeline record.
        """
        existing = (
            self._db.query(PipelineDBModel).filter_by(session_id=session_id).first()
        )
        if existing is not None:
            return existing.id

        record = PipelineDBModel(
            session_id=session_id,
            name="",
            description=None,
            parameters=None,
            chunking_model_id=None,
            prompt_id=None,
            generation_model_id=None,
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record.id

    def _update_db_record(
        self,
        session_id: int,
        chunking_model_id: int,
        prompt_id: int,
        generation_model_id: int,
    ) -> None:
        """Patch FK columns on the pipeline record.

        Parameters
        ----------
        session_id : int
            Generative session identifier.
        chunking_model_id : int
            FK into ``RAG_chunking_model``.
        prompt_id : int
            FK into ``RAG_prompt``.
        generation_model_id : int
            FK into ``RAG_generation_model``.

        Raises
        ------
        ValueError
            If no pipeline record exists for the given session.
        """
        record = (
            self._db.query(PipelineDBModel).filter_by(session_id=session_id).first()
        )
        if record is None:
            raise ValueError(f"No pipeline record for session {session_id}")
        record.chunking_model_id = chunking_model_id
        record.prompt_id = prompt_id
        record.generation_model_id = generation_model_id
        self._db.commit()

    def _assemble_pipeline_instance(
        self,
        config: RAGPipelineConfig,
        pipeline_id: int,
        documents: Dict[int, BaseDocument],
        prompt_model: Prompt,
        chunking_model_id: int,
        chunking_model: BaseChunkingModel,
        chunks: Dict[int, Dict[int, Chunk]],
        retriever: RetrieverModel,
        llm_model: TextToTextGenerationTaskModel,
    ) -> RAGPipeline:
        """Build a ``RAGPipeline`` from pre-assembled components.

        Parameters
        ----------
        config : RAGPipelineConfig
        pipeline_id : int
        documents : Dict[int, BaseDocument]
        prompt_model : Prompt
        chunking_model_id : int
        chunking_model : BaseChunkingModel
        chunks : Dict[int, Dict[int, Chunk]]
        retriever : RetrieverModel
        llm_model : TextToTextGenerationTaskModel

        Returns
        -------
        RAGPipeline
        """
        return RAGPipeline(
            config=config,
            pipeline_id=pipeline_id,
            chunking_model_id=chunking_model_id,
            documents=documents,
            chunks=chunks,
            prompt_model=prompt_model,
            chunking_model=chunking_model,
            retriever=retriever,
            llm_model=llm_model,
        )
