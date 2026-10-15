"""RAG pipeline orchestration.

RAGPipeline receives its dependencies injected (config, factories,
repository, loader) rather than constructing them from raw kwargs.
Orchestrates: document loading → chunk-set creation → chunking →
retrieval → prompt formatting → LLM generation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from DashAI.back.core.schema_fields import (
    BaseSchema,
    component_field,
    int_field,
    list_field,
    none_type,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.registry.component_registry import ComponentRegistry
from DashAI.back.models.base_generative_model import BaseGenerativeModel
from DashAI.back.models.RAG.documents import Chunk, RAGDocument
from DashAI.back.models.RAG.exceptions import (
    RAGPipelineConfigError,
    RAGPipelineInputError,
    RAGPipelineRuntimeError,
    RAGRetrieverError,
    RAGTransformationError,
)
from DashAI.back.models.RAG.RAG_constants import (
    RAG_INFRA_KEYS,
    RAG_MODEL_KEYS,
    RAG_PARAM_KEYS,
    RAG_PARAM_KEYS_ALL,
    RAG_PARAM_QUERY_TRANSFORMATION,
)
from DashAI.back.models.RAG.retrievers.trace_utils import chunk_ref
from DashAI.back.models.text_to_text_generation_model import (
    TextToTextGenerationTaskModel,
)

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from DashAI.back.models.RAG.chunking_models.base_chunking_model import (
        BaseChunkingModel,
    )
    from DashAI.back.models.RAG.prompts import BasePrompt
    from DashAI.back.models.RAG.retrievers.base_retriever import BaseRetriever
    from DashAI.back.models.RAG.transformation.base_query_transformation import (
        BaseQueryTransformation,
    )


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
    """A single retrieved chunk with its document metadata.

    Attributes
    ----------
    document_id : int
        The ``data_document`` id.
    document_name : str
        The document name at answer time.
    document_position : int
        Position of the chunk in the document.
    text : str
        The chunk text.
    page : int or None
        Page the chunk starts in, None when the format has no pages.
    """

    document_id: int
    document_name: str
    document_position: int
    text: str
    page: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON serializable dict representation.

        Returns
        -------
        dict
            Every attribute, keyed by name.
        """
        return {
            "document_id": self.document_id,
            "document_name": self.document_name,
            "document_position": self.document_position,
            "text": self.text,
            "page": self.page,
        }


def merge_round_robin(retrieved_lists: List[List[Chunk]]) -> List[Chunk]:
    """Merge per-query retrieval results by round-robin interleave.

    Queries are retrieved independently and their ranked lists are merged
    fairly: the first result of every list, then the second of every list, and
    so on. A chunk already seen is skipped, keyed by
    ``(document_id, document_position)`` — the same identity the rest of the
    pipeline uses. The order of first appearance wins, and empty (or shorter)
    lists are tolerated.

    Parameters
    ----------
    retrieved_lists : List[List[Chunk]]
        One ranked chunk list per query, in query order.

    Returns
    -------
    List[Chunk]
        The merged, de-duplicated chunks in round-robin order.
    """
    seen: set[Tuple[int, int]] = set()
    merged: List[Chunk] = []
    max_length = max((len(chunks) for chunks in retrieved_lists), default=0)
    for index in range(max_length):
        for chunks in retrieved_lists:
            if index >= len(chunks):
                continue
            chunk = chunks[index]
            key = (chunk.document_id, chunk.document_position)
            if key in seen:
                continue
            seen.add(key)
            merged.append(chunk)
    return merged


@dataclass(frozen=True)
class RAGGenerationOutput:
    """Typed output from RAGPipeline.generate().

    Attributes
    ----------
    message : str
        The generated answer.
    chunks : Dict[str, ChunkReference]
        The retrieved chunks keyed by ``"<document_id>_<position>"``.
    queries : List[str]
        The queries used for retrieval (always a list; one element when the
        query transformation stage is disabled or when rewriting produces a
        single query).
    trace : List[Dict[str, Any]]
        One trace node per query, in query order. Each entry is
        ``{"query": <query>, "retriever": <retriever trace node>}``. The
        retriever nodes reference chunks by ``"<document_id>_<position>"`` —
        the same keys as ``chunks`` — so the frontend joins them without
        duplicating chunk payloads. Always a list.
    """

    message: str
    chunks: Dict[str, "ChunkReference"]
    queries: List[str]
    trace: List[Dict[str, Any]]


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
    query_transformation: Optional[ModelRef] = None

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> "RAGPipelineConfig":
        """Parse and validate raw kwargs into a RAGPipelineConfig.

        Args:
            **kwargs: Raw pipeline parameter dict containing infrastructure
                keys (session_id, db, component_registry, env_RAG_path),
                model keys (prompt, chunking_model, retriever_model,
                generation_model), the optional query_transformation model key,
                and the documents list.

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

        query_transformation_ref: Optional[ModelRef] = None
        raw_transformation = kwargs.get(RAG_PARAM_QUERY_TRANSFORMATION)
        if raw_transformation is not None:
            if not isinstance(raw_transformation, dict):
                raise RAGPipelineConfigError(
                    f"'{RAG_PARAM_QUERY_TRANSFORMATION}' must be a dict, got "
                    f"{type(raw_transformation).__name__}"
                )
            if "component" not in raw_transformation:
                raise RAGPipelineConfigError(
                    f"Missing 'component' in '{RAG_PARAM_QUERY_TRANSFORMATION}'"
                )
            if "params" not in raw_transformation:
                raise RAGPipelineConfigError(
                    f"Missing 'params' in '{RAG_PARAM_QUERY_TRANSFORMATION}'"
                )
            query_transformation_ref = ModelRef(
                component=raw_transformation["component"],
                params=raw_transformation["params"],
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
            query_transformation=query_transformation_ref,
        )


class RAGPipelineSchema(BaseSchema):
    """Schema for RAG pipeline configuration parameters.

    Defines the six configurable fields: documents, prompt,
    chunking_model, retriever_model, generation_model, and the optional
    query_transformation stage. Each model field accepts a
    ``{"component": str, "params": dict}`` structure resolved by the
    ComponentRegistry.
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
        component_field(parent="BasePrompt"),
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
        component_field(parent="BaseRetriever"),
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

    query_transformation: schema_field(
        none_type(component_field(parent="BaseQueryTransformation")),
        placeholder=None,
        description=MultilingualString(
            en="Optional query transformation stage that turns the user message"
            " into one or more search queries before retrieval.",
            es="Etapa opcional de transformación de consulta que convierte el"
            " mensaje del usuario en una o varias consultas de búsqueda antes"
            " de la recuperación.",
            pt="Etapa opcional de transformação de consulta que converte a"
            " mensagem do usuário em uma ou mais consultas de busca antes da"
            " recuperação.",
            de="Optionale Abfrage-Transformationsstufe, die die Benutzernachricht"
            " vor dem Abruf in eine oder mehrere Suchanfragen umwandelt.",
            zh="可选的查询转换阶段，在检索前将用户消息转换为一个或多个搜索查询。",
        ),
    ) = None  # type: ignore


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
    documents: Dict[int, RAGDocument]
    prompt_model: BasePrompt
    chunking_model: BaseChunkingModel
    chunks: Dict[int, Dict[int, Chunk]]
    retriever: BaseRetriever
    llm_model: TextToTextGenerationTaskModel
    query_transformation: Optional[BaseQueryTransformation]

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
        documents: Dict[int, RAGDocument],
        chunks: Dict[int, Dict[int, Chunk]],
        prompt_model: BasePrompt,
        chunking_model: BaseChunkingModel,
        retriever: BaseRetriever,
        llm_model: TextToTextGenerationTaskModel,
        query_transformation: Optional[BaseQueryTransformation] = None,
    ) -> None:
        """Initialise the RAG pipeline with fully constructed dependencies.

        Args:
            config: Validated pipeline configuration.
            pipeline_id: Database ID for the pipeline run.
            chunking_model_id: Database ID for the chunking model.
            documents: Mapping of document IDs to RAGDocument instances.
            chunks: Mapping of document IDs to their chunk dicts.
            prompt_model: The prompt template model.
            chunking_model: The chunking model instance.
            retriever: The retriever model instance.
            llm_model: The text generation (LLM) model instance.
            query_transformation: Optional query transformation stage. When
                None, the current message is used directly as the search query.
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
        self.query_transformation = query_transformation

    def multi_query_retrieval(
        self, queries: List[str]
    ) -> Tuple[List[Chunk], List[Dict[str, Any]]]:
        """Retrieve for every query and merge the results fairly.

        This is the pipeline's ONLY retrieval path: a plain one-element query
        list (the raw message when the transformation stage is disabled, or a
        single rewrite) goes through the same per-query retrieve plus merge as
        an n-element list. Merging a single list is effectively a no-op —
        ``merge_round_robin`` preserves its content and order — while an
        n-element list is interleaved round-robin and de-duplicated by
        ``(document_id, document_position)``.

        Each query is retrieved independently. A failure on any query aborts
        the whole retrieval with a wrapped error, so callers see one consistent
        failure mode.

        Parameters
        ----------
        queries : List[str]
            The search queries, in priority order. Always non-empty.

        Returns
        -------
        Tuple[List[Chunk], List[Dict[str, Any]]]
            The round-robin merged, de-duplicated chunks and one trace entry
            per query — ``{"query": <query>, "retriever": <trace node>}`` — in
            query order.

        Raises
        ------
        RAGPipelineRuntimeError
            If any underlying retrieval fails.
        """
        retrieved_lists: List[List[Chunk]] = []
        trace: List[Dict[str, Any]] = []
        for query in queries:
            try:
                result = self.retriever.retrieve(query)
                # A legacy or plugin retriever returning a bare list instead
                # of the (chunks, trace) tuple must fail loudly instead of
                # silently mis-unpacking chunk data as the trace node.
                if (
                    not isinstance(result, tuple)
                    or len(result) != 2
                    or not isinstance(result[1], dict)
                ):
                    raise RAGRetrieverError(
                        "retrieve() must return a (List[Chunk], Dict) tuple, "
                        f"got {type(result).__name__}."
                    )
                query_chunks, query_node = result
            except Exception as e:
                raise RAGPipelineRuntimeError(
                    f"Document retrieval failed: {str(e)}"
                ) from e
            retrieved_lists.append(query_chunks)
            trace.append({"query": query, "retriever": query_node})
        return merge_round_robin(retrieved_lists), trace

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
            document: RAGDocument | None = self.documents.get(document_id)
            if document is None:
                raise RAGPipelineRuntimeError(
                    f"Document with ID {document_id} not found in pipeline documents."
                )
            chunk_position: int = retrieved_chunk.document_position
            chunk_text: str = retrieved_chunk.text
            page = retrieved_chunk.page
            ref: str = chunk_ref(retrieved_chunk)
            chunk_dict[ref] = ChunkReference(
                document_id=document_id,
                document_name=document.file_name,
                document_position=chunk_position,
                text=chunk_text,
                page=page,
            )
            location = f", page {page}" if page is not None else ""
            chunks_texts.append(
                f"Document {document.file_name}{location}, "
                f"chunk nº {chunk_position}, text:\n {chunk_text}"
            )
        return "\n\n".join(chunks_texts), chunk_dict

    def _extract_input(
        self,
        input_data: Tuple[Dict[str, str], ...],
    ) -> Tuple[str, Tuple[Dict[str, str], ...]]:
        """Validate the chat input and split message from history.

        Parameters
        ----------
        input_data : Tuple[Dict[str, str], ...]
            Chat-format input with history as earlier entries and the current
            user message as the last entry.

        Returns
        -------
        Tuple[str, Tuple[Dict[str, str], ...]]
            The current user message and the preceding history entries.

        Raises
        ------
        RAGPipelineInputError
            If input_data is empty or malformed.
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
        return input_message, tuple(input_data[:-1])

    def _resolve_queries(
        self,
        input_message: str,
        history: Tuple[Dict[str, str], ...],
    ) -> Tuple[List[str], Optional[List[str]]]:
        """Resolve the retrieval queries from the optional transformation stage.

        Parameters
        ----------
        input_message : str
            The current user message.
        history : Tuple[Dict[str, str], ...]
            Prior conversation entries, forwarded to the transformer.

        Returns
        -------
        Tuple[List[str], Optional[List[str]]]
            ``(queries, transformed_queries)``. ``queries`` is always a
            non-empty list — the transformed queries when the stage ran, or the
            one-element ``[input_message]`` when it is disabled.
            ``transformed_queries`` is ``None`` when no transformation ran.

        Raises
        ------
        RAGPipelineRuntimeError
            If the transformation fails or returns no queries.
        """
        if self.query_transformation is None:
            return [input_message], None
        try:
            transformation_result = self.query_transformation.transform(
                message=input_message, history=list(history)
            )
        except RAGTransformationError as e:
            raise RAGPipelineRuntimeError(
                f"Query transformation failed: {str(e)}"
            ) from e
        transformed_queries = list(transformation_result.queries)
        if not transformed_queries:
            raise RAGPipelineRuntimeError("Query transformation returned no queries.")
        return transformed_queries, transformed_queries

    def _retrieve(self, queries: List[str]) -> Tuple[List[Chunk], List[Dict[str, Any]]]:
        """Retrieve chunks through the pipeline's single retrieval path.

        Parameters
        ----------
        queries : List[str]
            The non-empty query list to retrieve for.

        Returns
        -------
        Tuple[List[Chunk], List[Dict[str, Any]]]
            Merged, de-duplicated chunks and the per-query trace entries.

        Raises
        ------
        RAGPipelineRuntimeError
            If retrieval fails.
        """
        try:
            return self.multi_query_retrieval(queries)
        except RAGPipelineRuntimeError:
            # Already the retriever's wrapped failure; re-wrapping it would
            # stack two prefixes ("Failed during retrieval: Document
            # retrieval failed: ...") over the same root cause.
            raise
        except Exception as e:
            raise RAGPipelineRuntimeError(f"Failed during retrieval: {str(e)}") from e

    def _build_prompt(
        self,
        input_message: str,
        chunks: List[Chunk],
        transformed_queries: Optional[List[str]],
    ) -> Tuple[str, Dict[str, ChunkReference]]:
        """Build chunk references and render the prompt.

        Parameters
        ----------
        input_message : str
            The current user message.
        chunks : List[Chunk]
            The retrieved chunks.
        transformed_queries : List[str] or None
            The transformed queries, or None when no transformation ran. The
            prompt's optional ``{queries}`` placeholder receives their joined
            form, or None so an untransformed run sends no transformed queries.

        Returns
        -------
        Tuple[str, Dict[str, ChunkReference]]
            The rendered prompt and the chunk reference map.

        Raises
        ------
        RAGPipelineRuntimeError
            If chunk rendering or prompt formatting fails.
        """
        try:
            chunks_text: str
            chunk_dict: Dict[str, ChunkReference]
            chunks_text, chunk_dict = self._build_chunk_references(chunks)
            if transformed_queries is not None:
                queries_value: Optional[str] = "; ".join(transformed_queries)
            else:
                queries_value = None
            prompt: str = self.prompt_model.format(
                input=input_message,
                chunks=chunks_text,
                queries=queries_value,
            )
            return prompt, chunk_dict
        except Exception as e:
            raise RAGPipelineRuntimeError(
                f"Failed during prompt formatting: {str(e)}"
            ) from e

    def _generate_answer(
        self,
        history: Tuple[Dict[str, str], ...],
        prompt: str,
    ) -> str:
        """Call the LLM and return its first output message.

        Parameters
        ----------
        history : Tuple[Dict[str, str], ...]
            Prior conversation entries.
        prompt : str
            The rendered RAG prompt to send as the current user message.

        Returns
        -------
        str
            The generated answer.

        Raises
        ------
        RAGPipelineRuntimeError
            If the LLM fails or returns an unexpected payload.
        """
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
            return raw_message
        except RAGPipelineRuntimeError:
            raise
        except Exception as e:
            raise RAGPipelineRuntimeError(
                f"Failed during LLM generation: {str(e)}"
            ) from e

    def generate(
        self,
        input_data: Tuple[Dict[str, str], ...],
    ) -> RAGGenerationOutput:
        """Run the full RAG pipeline: retrieve, format, and generate.

        The retrieval path is uniform: a one-element query list (the raw
        message when the transformation stage is disabled, or a single rewrite)
        goes through the same per-query retrieval and merge as an n-element
        list.

        Args:
            input_data: Chat-format input with history as earlier entries
                and the current user message as the last entry.

        Returns:
            The generated message, the chunks used for retrieval, the queries
            the retrieval ran over (always a list), and the per-query trace
            entries.

        Raises:
            RAGPipelineInputError: If input_data is empty or malformed.
            RAGPipelineRuntimeError: If any pipeline stage fails.
        """
        input_message, history = self._extract_input(input_data)
        queries, transformed_queries = self._resolve_queries(input_message, history)
        chunks, trace = self._retrieve(queries)
        prompt, chunk_dict = self._build_prompt(
            input_message, chunks, transformed_queries
        )
        raw_message = self._generate_answer(history, prompt)
        return RAGGenerationOutput(
            message=raw_message, chunks=chunk_dict, queries=queries, trace=trace
        )
