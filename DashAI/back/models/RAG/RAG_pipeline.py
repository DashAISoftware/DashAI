"""RAG pipeline orchestration.

RAGPipeline receives its dependencies injected (config, factories,
repository, loader) rather than constructing them from raw kwargs.
Orchestrates: document loading → chunk-set creation → chunking →
retrieval → prompt formatting → LLM generation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    int_field,
    list_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.base_generative_model import BaseGenerativeModel
from DashAI.back.models.RAG.documents import BaseDocument, Chunk
from DashAI.back.models.RAG.exceptions import (
    RAGPipelineConfigError,
    RAGPipelineInputError,
    RAGPipelineRuntimeError,
)
from DashAI.back.models.RAG.RAG_constants import (
    RAG_INFRA_KEYS,
    RAG_MODEL_KEYS,
    RAG_PARAM_KEYS,
    RAG_PARAM_KEYS_ALL,
)
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from DashAI.back.models.RAG.chunking_models.base_chunking_model import (
        BaseChunkingModel,
    )
    from DashAI.back.models.RAG.prompts import Prompt
    from DashAI.back.models.RAG.retrievers.retriever_model import RetrieverModel


@dataclass(frozen=True)
class ModelRef:
    """Parsed reference to a component model.

    Represents a ``{component: str, params: dict}`` entry from the
    pipeline parameter payload.
    """

    component: str
    params: Dict[str, Any]


@dataclass(frozen=True)
class ChunkReference:
    """A single chunk with its document metadata."""

    document_id: int
    document_name: str
    document_position: int
    text: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return {
            "document_id": self.document_id,
            "document_name": self.document_name,
            "document_position": self.document_position,
            "text": self.text,
        }


@dataclass(frozen=True)
class RAGGenerationOutput:
    """Typed output from RAGPipeline.generate()."""

    message: str
    chunks: Dict[str, "ChunkReference"]


@dataclass(frozen=True)
class RAGPipelineConfig:
    """Structured, validated representation of pipeline initialisation kwargs.

    Parses the raw kwargs dict once and provides typed field access,
    eliminating magic strings in the pipeline's __init__.
    """

    session_id: int
    db: Session
    component_registry: ComponentRegistry
    env_RAG_path: str  # noqa: N815
    documents: List[int]
    prompt: ModelRef
    chunking_model: ModelRef
    retriever_model: ModelRef
    generation_model: ModelRef

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> "RAGPipelineConfig":
        """Parse and validate raw kwargs into a RAGPipelineConfig.

        Args:
            **kwargs: Raw pipeline parameter dict containing infrastructure
                keys (session_id, db, component_registry, env_RAG_path),
                model keys (prompt, chunking_model, retriever_model,
                generation_model), and the documents list.

        Returns:
            A validated RAGPipelineConfig instance.

        Raises:
            RAGPipelineConfigError: If required keys are missing, model
                refs are not dicts, model refs lack component/params, or
                unknown keys are present.
        """
        missing: List[str] = []
        for key in RAG_INFRA_KEYS:
            if key not in kwargs:
                missing.append(key)
        for key in RAG_PARAM_KEYS:
            if key not in kwargs:
                missing.append(key)
        if missing:
            raise RAGPipelineConfigError(
                f"Missing required parameters: {sorted(missing)}"
            )

        model_refs: Dict[str, ModelRef] = {}
        for key in RAG_MODEL_KEYS:
            raw = kwargs[key]
            if not isinstance(raw, dict):
                raise RAGPipelineConfigError(
                    f"'{key}' must be a dict, got {type(raw).__name__}"
                )
            if "component" not in raw:
                raise RAGPipelineConfigError(f"Missing 'component' in '{key}'")
            if "params" not in raw:
                raise RAGPipelineConfigError(f"Missing 'params' in '{key}'")
            model_refs[key] = ModelRef(
                component=raw["component"],
                params=raw["params"],
            )

        extra: set[str] = set(kwargs) - RAG_PARAM_KEYS_ALL
        if extra:
            log.warning(
                "Unknown parameters passed to RAGPipelineConfig.from_kwargs(): %s. "
                "These keys are not recognized and will cause the pipeline to fail. "
                "Check if session parameters contain extra metadata keys.",
                sorted(extra),
            )
            raise RAGPipelineConfigError(
                f"Unknown parameters: {sorted(extra)}. "
                "These keys are not recognized pipeline configuration parameters."
            )

        return cls(
            session_id=kwargs["session_id"],
            db=kwargs["db"],
            component_registry=kwargs["component_registry"],
            env_RAG_path=kwargs["env_RAG_path"],
            documents=kwargs["documents"],
            prompt=model_refs["prompt"],
            chunking_model=model_refs["chunking_model"],
            retriever_model=model_refs["retriever_model"],
            generation_model=model_refs["generation_model"],
        )


class RAGPipelineSchema(BaseSchema):
    """Schema for RAG pipeline configuration parameters.

    Defines the five configurable fields: documents, prompt,
    chunking_model, retriever_model, and generation_model. Each
    model field accepts a ``{"component": str, "params": dict}``
    structure resolved by the ComponentRegistry.
    """

    documents: schema_field(
        list_field(int_field(gt=0)),
        placeholder=None,
        description=MultilingualString(
            en="List of document IDs to use in the RAG pipeline.",
            es="Lista de IDs de documentos a usar en el pipeline RAG.",
            pt="Lista de IDs de documentos a usar no pipeline RAG.",
            de="Liste der Dokument-IDs, die im RAG-Pipeline verwendet werden sollen.",
            zh="要在 RAG 流水线中使用的文档 ID 列表。",
        ),
    )  # type: ignore

    prompt: schema_field(
        component_field(parent="Prompt"),
        placeholder={"component": "DefaultRAGGenerationPrompt", "params": {}},
        description=MultilingualString(
            en="Prompt template used in the RAG pipeline.",
            es="Plantilla de prompt usada en el pipeline RAG.",
            pt="Modelo de prompt usado no pipeline RAG.",
            de="Prompt-Vorlage, die im RAG-Pipeline verwendet wird.",
            zh="用于 RAG 流水线的提示词模板。",
        ),
    )  # type: ignore

    chunking_model: schema_field(
        component_field(parent="BaseChunkingModel"),
        description=MultilingualString(
            en="Chunking model used to split documents into smaller pieces.",
            es="Modelo de fragmentación para dividir documentos en piezas.",
            pt=(
                "Modelo de fragmentação usado para dividir documentos em"
                " fragmentos menores."
            ),
            de="Chunking-Modell zum Aufteilen von Dokumenten in kleinere Stücke.",
            zh="用于将文档拆分为更小块的切分模型。",
        ),
        placeholder={"component": "CharacterChunkModel", "params": {}},
    )  # type: ignore

    retriever_model: schema_field(
        component_field(parent="RetrieverModel"),
        placeholder={"component": "BM25Retriever", "params": {}},
        description=MultilingualString(
            en="Retriever component used in the RAG pipeline.",
            es="Componente recuperador usado en el pipeline RAG.",
            pt="Componente recuperador usado no pipeline RAG.",
            de="Retriever-Komponente, die im RAG-Pipeline verwendet wird.",
            zh="用于 RAG 流水线的检索器组件。",
        ),
    )  # type: ignore

    generation_model: schema_field(
        component_field(parent="TextToTextGenerationTaskModel"),
        placeholder={"component": "", "params": {}},
        description=MultilingualString(
            en="Text generation model used in the RAG pipeline.",
            es="Modelo de generación de texto usado en el pipeline RAG.",
            pt="Modelo de geração de texto usado no pipeline RAG.",
            de="Textgenerierungsmodell, das im RAG-Pipeline verwendet wird.",
            zh="用于 RAG 流水线的文本生成模型。",
        ),
    )  # type: ignore


class RAGPipeline(BaseGenerativeModel):
    """Retrieval-Augmented Generation pipeline.

    Receives dependencies injected — does not construct factories,
    repositories, or loaders. The caller (RAGJob) builds them from
    the current DB session and passes them in.

    Orchestrates: document loading → chunk-set creation → chunking →
    retrieval → prompt formatting → LLM generation.
    """

    COMPATIBLE_COMPONENTS: List[str] = ["RAGTask"]
    SCHEMA: type[BaseSchema] = RAGPipelineSchema

    session_id: int
    pipeline_id: int
    chunking_model_id: int
    documents_ids: List[int]
    documents: Dict[int, BaseDocument]
    prompt_model: Prompt
    chunking_model: BaseChunkingModel
    chunks: Dict[int, Dict[int, Chunk]]
    retriever: RetrieverModel
    llm_model: TextToTextGenerationTaskModel

    DISPLAY_NAME: str = MultilingualString(
        en="RAG Pipeline",
        es="Flujo de RAG",
        pt="Pipeline RAG",
        de="RAG-Pipeline",
        zh="RAG 流水线",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "Pipeline for Retrieval-Augmented Generation (RAG) tasks,"
            " orchestrating document loading, chunking, retrieval,"
            " prompt formatting, and LLM generation."
        ),
        es=(
            "Pipeline para tareas de Generación Aumentada por"
            " Recuperación (RAG), orquestando la carga de documentos,"
            " chunking, recuperación, formateo de prompts y generación"
            " con LLM."
        ),
        pt=(
            "Pipeline para tarefas de Geração Aumentada por Recuperação"
            " (RAG), orquestrando carregamento de documentos, chunking,"
            " recuperação, formatação de prompts e geração com LLM."
        ),
        de=(
            "Pipeline für Aufgaben der Retrieval-Augmented Generation (RAG),"
            " die das Laden von Dokumenten, Chunking, Abruf,"
            " Prompt-Formatierung und LLM-Generierung orchestriert."
        ),
        zh=(
            "面向检索增强生成（RAG）任务的流水线，负责编排文档加载、分块、"
            "检索、提示词格式化和 LLM 生成。"
        ),
    )
    COLOR: str = "#e12885"
    ICON: str = "Grading"
    MODEL_NAME: str = "RAGPipeline"

    def __init__(
        self,
        config: RAGPipelineConfig,
        pipeline_id: int,
        chunking_model_id: int,
        documents: Dict[int, BaseDocument],
        chunks: Dict[int, Dict[int, Chunk]],
        prompt_model: Prompt,
        chunking_model: BaseChunkingModel,
        retriever: RetrieverModel,
        llm_model: TextToTextGenerationTaskModel,
    ) -> None:
        """Initialise the RAG pipeline with fully constructed dependencies.

        Args:
            config: Validated pipeline configuration.
            pipeline_id: Database ID for the pipeline run.
            chunking_model_id: Database ID for the chunking model.
            documents: Mapping of document IDs to BaseDocument instances.
            chunks: Mapping of document IDs to their chunk dicts.
            prompt_model: The prompt template model.
            chunking_model: The chunking model instance.
            retriever: The retriever model instance.
            llm_model: The text generation (LLM) model instance.
        """
        self.session_id = config.session_id
        self.pipeline_id = pipeline_id
        self.chunking_model_id = chunking_model_id
        self.documents_ids = config.documents
        self.documents = documents
        self.prompt_model = prompt_model
        self.chunking_model = chunking_model
        self.chunks = chunks
        self.retriever = retriever
        self.llm_model = llm_model

    def single_interaction(
        self,
        query: str,
    ) -> List[Chunk]:
        """Retrieve the top-K chunks for a single query.

        Args:
            query: The search query string.

        Returns:
            Ranked list of retrieved chunks.

        Raises:
            RAGPipelineRuntimeError: If the retriever fails.
        """
        try:
            return self.retriever.retrieve(query)
        except Exception as e:
            raise RAGPipelineRuntimeError(f"Document retrieval failed: {str(e)}") from e

    def _build_chunk_references(
        self,
        chunks: List[Chunk],
    ) -> Tuple[str, Dict[str, ChunkReference]]:
        """Build a text block and reference map from retrieved chunks.

        Args:
            chunks: Chunks returned by the retriever.

        Returns:
            Joined chunk texts and a mapping from chunk key to
            ChunkReference.
        """
        chunks_texts: List[str] = []
        chunk_dict: Dict[str, ChunkReference] = {}
        for retrieved_chunk in chunks:
            document_id: int = retrieved_chunk.document_id
            document: BaseDocument | None = self.documents.get(document_id)
            if document is None:
                raise RAGPipelineRuntimeError(
                    f"Document with ID {document_id} not found in pipeline documents."
                )
            chunk_position: int = retrieved_chunk.document_position
            chunk_text: str = retrieved_chunk.text
            chunk_ref: str = f"{document_id}_{chunk_position}"
            chunk_dict[chunk_ref] = ChunkReference(
                document_id=document_id,
                document_name=document.file_name,
                document_position=chunk_position,
                text=chunk_text,
            )
            chunks_texts.append(
                f"Document {document.file_name}, "
                f"chunk nº {chunk_position}, text:\n {chunk_text}"
            )
        return "\n\n".join(chunks_texts), chunk_dict

    def generate(
        self,
        input_data: Tuple[Dict[str, str], ...],
    ) -> RAGGenerationOutput:
        """Run the full RAG pipeline: retrieve, format, and generate.

        Args:
            input_data: Chat-format input with history as earlier entries
                and the current user message as the last entry.

        Returns:
            The generated message and the chunks used for retrieval.

        Raises:
            RAGPipelineInputError: If input_data is empty or malformed.
            RAGPipelineRuntimeError: If any pipeline stage fails.
        """
        if not input_data:
            raise RAGPipelineInputError("input_data must not be empty.")
        try:
            input_dict: Dict[str, str] = input_data[-1]
            input_message: str = input_dict["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise RAGPipelineInputError(
                f"Malformed input_data: expected Tuple[Dict[str, str], ...] "
                f"with a 'content' key in the last entry, got {type(input_data)}: {e}"
            ) from e
        history: Tuple[Dict[str, str], ...] = input_data[:-1]
        try:
            chunks: List[Chunk] = self.single_interaction(input_message)
        except Exception as e:
            raise RAGPipelineRuntimeError(f"Failed during retrieval: {str(e)}") from e
        try:
            chunks_text: str
            chunk_dict: Dict[str, ChunkReference]
            chunks_text, chunk_dict = self._build_chunk_references(chunks)
            prompt: str = self.prompt_model.format(
                input=input_message,
                chunks=chunks_text,
            )
        except Exception as e:
            raise RAGPipelineRuntimeError(
                f"Failed during prompt formatting: {str(e)}"
            ) from e
        try:
            model_input: List[Dict[str, str]] = list(history) + [
                {"role": "user", "content": prompt}
            ]
            # NOTE: Output is not streamed — the user waits for the full response.
            output: List[Any] = self.llm_model.generate(model_input)
            if not output:
                raise RAGPipelineRuntimeError("LLM model returned empty output list.")
            raw_message = output[0]
            if not isinstance(raw_message, str):
                raise RAGPipelineRuntimeError(
                    f"LLM output is not a string, got {type(raw_message).__name__}"
                )
            return RAGGenerationOutput(message=raw_message, chunks=chunk_dict)
        except RAGPipelineRuntimeError:
            raise
        except Exception as e:
            raise RAGPipelineRuntimeError(
                f"Failed during LLM generation: {str(e)}"
            ) from e
