# Backend Architecture

## Overview

The RAG backend follows a **layered architecture** with clear separation of
concerns after the service-layer refactor:

```
Endpoints (api/api_v1/endpoints/)
  │
  ├── POST  /api/v1/generative-session/         → delegates to validator
  ├── PUT   /api/v1/generative-session/{id}/parameters → delegates to validator
  ├── GET   /api/v1/generative-session/...
  └── DELETE ...
       │
       ▼
RAGSessionValidationService (services/RAG/)
  ├── prepare_RAG_params()       — POST validation (strict, recursive)
  └── validate_update_payload()  — PUT validation (partial, recursive)
       │
       ▼
Services (services/RAG/)
  │
  ├── SetupService              — pipeline assembly (build_pipeline)
  ├── DocumentService           — document CRUD, file I/O, extractors, hydration
  ├── ChunkingService           — chunk set identity (SHA-256), chunking lifecycle
  ├── PromptService             — prompt CRUD, get_or_create via parameters_hash
  ├── LLMService                — LLM lookup-or-create via parameters_hash
  ├── RetrieverDBService        — all retriever DB operations
  ├── EmbeddingStorageService   — .npy matrix persistence on disk + DB
  ├── RetrieverSetupService     — full retriever lifecycle
  └── CleanupService            — cascade deletion on session delete/update
       │
       ▼
Models (models/RAG/) — pure domain definitions
  ├── Factories (no DB, no FS)
  │     ├── PromptFactory        — resolve registry → instantiate
  │     ├── ChunkingModelFactory — instantiate → chunk documents
  │     ├── RetrieverFactory     — resolve registry → validate → inject infra → init
  │     └── LLMFactory           — resolve registry → instantiate
  ├── RAGPipeline                — inference orchestration
  ├── extractors/                — 4 extractor types (PlainText, Pypdf, PyMuPDF,
  │                                 EasyOCR) with schema-driven params
  └── documents/, chunking_models/, retrievers/, prompts/ — pure domain models

Core (core/)
  └── component_validation.py — generic recursive component ref validation

### Supporting Modules

| Module                                      | Purpose                                                       |
|---------------------------------------------|---------------------------------------------------------------|
| `RAG_constants.py`                          | Canonical parameter key constants, shared across all layers   |
| `services/RAG/utils.py`                     | normalize_params(), build_parameters_hash() (SHA-256)         |
| `models/RAG/utils.py`                       | Utility functions (`hash_function` for SHA-256 hashing)       |
| `exceptions/`                               | Unified exception hierarchy (RAGWorkflowError + 8 sub-trees)  |
| `retrievers/enums.py`                       | `MergeStrategy` enum for parallel retriever merge behavior    |
| `retrievers/persistence.py`                 | `SparsePersistence` / `DensePersistence` dataclasses          |
```

## Service Layer

Each service receives a `db: Session` in its constructor. Services are NOT
registered in the DI container — they are instantiated per request/job.

### RAGSessionValidationService

Centralized validation for RAG session creation (POST) and parameter updates
(PUT). Two public methods with shared private helpers:

- `prepare_RAG_params()` — POST validation. All model keys (`prompt`/`prompt_id`,
  `chunking_model`, `retriever_model`, `generation_model`) and `documents` are
  required. Resolves `prompt_id` → `prompt` **before** structural validation.
- `validate_update_payload()` — PUT validation. Only validates keys present in
  the partial payload; documents are optional.

Both methods use `_validate_component_params()` which **recursively** validates
every `{component, params}` reference (including nested sub-components like
`BM25Vectorizer` inside `BM25Retriever`) against its own `SCHEMA`. If any fails
→ HTTP 400. The only exception: `DefaultRAGGenerationPrompt` and
`DefaultQARAGenerationPrompt` auto-inject `template` from a language-based
`TEMPLATES` dict. No other component auto-fills missing parameters.

### SetupService

(Formerly `RAGSetupService`.) Single responsibility: `build_pipeline()`.
Assembles the complete RAG pipeline returning a `RAGPipeline` instance.
Sequence: documents → chunk set → chunking → retriever → LLM → prompt.
No validation logic — that lives in `RAGSessionValidationService`.

### DocumentService

CRUD for documents + file storage + document hydration (replaces `DocumentLoader`).

Key methods: `upload()`, `load()`, `validate_exist()`, `get_by_session()`.

File type mapping uses `DocumentFileType` enum from
`models/RAG/documents/file_type.py` for single-source-of-truth strings.

### ChunkingService

Chunk set identity via SHA-256 signature (migrated from `chunk_set_utils.py`)

- lookup-or-create chunking model + chunk persistence (migrated DB logic from
  `ChunkingModelFactory`).

### PromptService

Prompt CRUD + get_or_create via deterministic `parameters_hash` (SHA-256 of
`json.dumps(params, sort_keys=True)`). Uses `services/RAG/utils.py` shared
helpers. Template validation (`validate_template()`) checks for required
placeholders (`{input}`, `{chunks}`). Session-scoped prompt copies.

### LLMService

Lookup-or-create of LLM records in `rag_generation_model` table via
`parameters_hash` (same deterministic hash as PromptService). Replaces the
DB logic that was in `LLMFactory`.

### RetrieverDBService

All retriever SQL operations (migrated from `RetrieverRepository`).
Covers bridge records, sparse/dense details, composite children,
embedding models, and embedding matrices.

### EmbeddingStorageService

Coordinated .npy persistence on disk + DB records for embedding matrices.
Uses `RetrieverDBService` for DB operations and `numpy` for files.

### RetrieverSetupService

Full retriever lifecycle: DB lookup → factory invocation → embedding computation
→ persistence. Handles unit (dense/sparse) and composite retrievers with
recursive child setup.

### CleanupService

Cascade deletion of RAG resources when a session is deleted or parameters
change. Retriever cleanup BEFORE chunking cleanup (critical ordering).

## Pure Factories (no DB or FS)

After the refactor, all four sub-factories are **pure** — they only construct
domain objects.

### PromptFactory

```python
class PromptFactory:
    def __init__(self, registry: ComponentRegistry): ...
    def create(self, component_name, params) -> PromptFactoryResult:
        prompt_class = self._registry[component_name]["class"]
        model = prompt_class(**params)
        return PromptFactoryResult(model=model)
```

### LLMFactory

Same pattern — resolves registry, instantiates, returns.

### ChunkingModelFactory

```python
class ChunkingModelFactory:
    def __init__(self, registry, documents, chunk_set_id): ...
    def create(self, component_name, params) -> ChunkingFactoryResult:
        model_class = self._registry[component_name]["class"]
        params["documents"] = self._documents
        model = model_class(**params)
        return ChunkingFactoryResult(model=model, chunks=model.get_chunks())
```

### RetrieverFactory

```python
class RetrieverFactory:
    def __init__(self, registry, rag_path, chunks, chunk_set_id): ...
    def create(self, component_name, params, persistence=None) -> RetrieverFactoryResult:
        # Normalize, validate schema, fill objects, instantiate, inject infra, init
```

Accepts an optional `persistence` parameter for pre-built DensePersistence or
SparsePersistence objects.

## Validation

Validation is centralized in `RAGSessionValidationService` — endpoints are thin
delegators. The backend follows a **strict validation contract**: every
`{component, params}` reference is recursively validated against its own
`SCHEMA`. Any failure → HTTP 400. The backend never fills missing defaults
(except for default prompt templates).

### Generic Component Validation (`core/component_validation.py`)

Two functions that work for ANY parameter structure, not just RAG:

- `find_component_refs(data)` — Recursively walks dicts/lists finding all
  `{"component": "...", "params": {...}}` patterns. Returns list of
  `(json_path, component_name, params)` tuples.
- `validate_component_refs(data, registry)` — Validates that all found
  components exist in the registry. Returns list of error messages.

### RAG Session Creation Validation (POST)

Delegated to `RAGSessionValidationService.prepare_RAG_params()`:

1. Model and task are checked against the component registry.
2. Documents must be non-empty and all IDs must exist in the DB.
3. Parameters are normalized via `normalize_payload()`.
4. If `prompt_id` is present, resolved to a `prompt` component ref **before**
   structural validation.
5. **Recursive schema validation** — every `{component, params}` ref (including
   nested sub-components like `BM25Vectorizer` inside `BM25Retriever`) is
   validated against its own `SCHEMA`. If any fails → HTTP 400.
6. **Default prompt exception** — `DefaultRAGGenerationPrompt` and
   `DefaultQARAGenerationPrompt` auto-inject `template` from language-based
   `TEMPLATES` dict. No other component auto-fills missing parameters.
7. Component refs checked against the registry.
8. Prompt template placeholders validated when explicit template is provided.

### RAG Parameter Update Validation (PUT)

Delegated entirely to `RAGSessionValidationService.validate_update_payload()`:

1. Normalize via `normalize_payload()`.
2. Resolve `prompt_id` → `prompt` (step 0, before validation — mirrors POST).
3. Validate structure of each sent component ref (`component` + `params` keys).
4. **Recursive schema validation** of every present component ref.
5. `validate_component_refs()` — validate all components exist in registry.
6. Validate documents (if sent): must be non-empty + all IDs exist in DB.
7. Returns validated dict. Then the endpoint merges with old params and
   calls `CleanupService.cleanup_orphaned_resources()`.

## RAGPipeline

### Simplified `__init__`

```python
class RAGPipeline(BaseGenerativeModel):
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
    ):
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
```

No DB access, no factory calls, no wiring — purely assigns attributes.

### Generation Flow (unchanged)

`generate(input_data)`:

1. Extract query + history from the last entry in the input tuple.
2. `single_interaction(query)` → delegates to `retriever.retrieve(query)` → top-k chunks.
3. `_build_chunk_references(chunks)` → format chunks into text + dict.
4. `prompt_model.format(input, chunks)` → render prompt.
5. `llm_model.generate(history + [{"role": "user", "content": prompt}])` → response.
6. Return `RAGGenerationOutput(message, chunks)`.

## RAGJob

Uses `SetupService.build_pipeline()` instead of manual wiring:

```python
setup_service = SetupService(db, component_registry, config["RAG_PATH"])
model = setup_service.build_pipeline(pipeline_config)
```

## RAGPipelineConfig (unchanged)

Validated parameter dataclass. Used by `RAGSetupService` and `RAGJob`.
Parses raw kwargs dict and provides typed field access. Reads parameter
keys from `RAG_constants.py` (`RAG_PARAM_KEYS`, `RAG_MODEL_KEYS`,
`RAG_INFRA_KEYS`).

## DocumentFileType Enum

```python
class DocumentFileType(str, Enum):
    TXT = "txt"
    PDF = "pdf"
    MD = "md"
    RST = "rst"
    TEX = "tex"
    CSV = "csv"
```

Single source of truth for file extension strings across all layers.

## Retriever Architecture

### Class Hierarchy

```
RetrieverModel (ABC, DashAI Component)
  ├── UnitRetriever (ABC, leaf node)
  │     ├── SparseRetriever (ABC)
  │     │     ├── TFIDFRetriever
  │     │     └── BM25Retriever
  │     └── DenseRetriever (ABC)
  │           └── DenseEmbeddingRetriever
  │                 └── HuggingFaceDenseRetriever (HF-specific retrieval)
  └── CompositeRetriever (ABC, composite node)
        ├── SequentialRetriever
        ├── ParallelRetriever
        ├── MMRRerankerRetriever
        └── CrossEncoderRetriever (ABC)       ← re-ranker over child retriever
              └── SentenceTransformerCrossEncoderRetriever (17 SBERT models)
```

Files are organized in subdirectories (`dense/`, `sparse/`, `composite/`,
`cross_encoder/`) within the `retrievers/` package. Utilities include
`retrievers/enums.py` for the `MergeStrategy` enum (ROUND_ROBIN, INTERLEAVE for
parallel retriever merging) and `retrievers/persistence.py` for
`SparsePersistence` / `DensePersistence` dataclasses.

- **Unit retrievers** are leaf nodes — they perform actual retrieval against
  their index.
- **Composite retrievers** wrap one or more child retrievers and combine their
  results via a strategy (sequential cascade, parallel merge, MMR re-ranking).
- **Cross-encoder retrievers** are re-rankers: a first-stage child retriever
  (ranker) retrieves candidates using its own `top_k`, and the cross-encoder
  (reranker) scores each (query, chunk) pair and returns the top `k` re-ranked
  results. The child's `top_k` controls the candidate set size (no separate
  `retrieval_factor` parameter).

### Dense Retriever Two-Layer Design

The dense retriever separates concerns into two layers:

1. **Embedding layer** (`DenseEmbedding` subclasses) — Handle model loading,
   tokenization, pooling, and vector generation. These are DashAI Components
   registered in the component registry. Available: `BERTEmbedding`,
   `DistilBERTEmbedding`, `E5Embedding`, `FastTextEmbedding`, `GemmaEmbedding`,
   `HuggingFaceEmbedding`, `InstructorEmbedding`, `LaBSEmbedding`,
   `OpenAIEmbedding`, `RoBERTaEmbedding`, `SentenceTransformerEmbedding`.
2. **Retriever layer** (shared `DenseEmbeddingRetriever` class) — Accepts any
   `DenseEmbedding` via a `component_field` schema parameter. The embedding
   family is selected at configuration time.
   - `DenseRetriever` (in `dense/dense_retriever.py`) is the abstract base.
   - `DenseEmbeddingRetriever` (in `dense/dense_embedding_retriever.py`) is the
     generic implementation.
   - `HuggingFaceDenseRetriever` (in `dense/huggingface_dense_retriever.py`)
     adds HF-specific utilities via `_hf_language_utils.py` and
     `_hf_metadata_utils.py`.

### Retriever Persistence

All retriever SQL is isolated in `RetrieverDBService`. It owns every query,
INSERT, and DB-model construction related to retrievers.

The `rag_retriever` table acts as a **bridge** — every retriever (unit,
composite, dense, sparse) gets one canonical identity record here. Sub-tables
(`rag_sparse_retriever`, `rag_dense_retriever`) hold type-specific details.
Composite child links are stored in `rag_retriever_child`.

## Chunk Set Caching

`ChunkingService.get_or_create_chunk_set()` computes a deterministic SHA-256
hash of:

- Sorted document IDs
- Sorted chunking configuration (e.g., chunking model component + params)

If a chunk set with this signature exists, it is reused. This avoids
re-chunking the same documents with the same parameters.

**Note:** Uses SELECT-then-INSERT without a lock. Safe for single-user
operation but could create duplicate chunk sets under concurrent requests.

## Document Extractors

Documents can be assigned an extractor at upload time via
`DocumentService.upload()`. Extractors are ConfigObject components with
schema-driven parameters exposed to the frontend:

| Extractor            | Default for            | Description                                        |
| -------------------- | ---------------------- | -------------------------------------------------- |
| `PlainTextExtractor` | txt, md, rst, tex, csv | Reads file as UTF-8 plain text                     |
| `PypdfExtractor`     | —                      | `pypdf`-based PDF extraction (`strict` mode)       |
| `PyMuPDFExtractor`   | pdf                    | fitz/pymupdf-based extraction (default PDF parser) |
| `EasyOCRExtractor`   | —                      | OCR-based extraction (requires easyocr)            |

Each extractor exposes its parameters via `schema_field()` with `description`
and `default` for UI form auto-generation. The `extractor_id` column on
`document` is `NOT NULL` with `FK RESTRICT` — assigned at upload, never
ambiguous. `PdfDocument._extract_text()` uses the assigned extractor with
a `_default_extract()` fallback.

Endpoints:

- `POST /api/v1/document/{id}/extract` — on-demand extraction (does not persist)
- `PUT /api/v1/document/{id}/extractor` — commit extractor choice (with
  force option to invalidate linked pipeline artifacts)

## Parameters Hash

`RAGPrompt` and `RAGGenerationModel` use a deterministic SHA-256
`parameters_hash` column for deduplication instead of fragile
`(class_name, parameters)` JSON comparisons on SQLite. The hash is computed
via `build_parameters_hash()` in `services/RAG/utils.py`
(`json.dumps(params, sort_keys=True)` → SHA-256).

The old `UniqueConstraint("class_name", "parameters")` has been removed from
both tables. Only prompt and generation model tables use this pattern;
chunking, embedding, and retriever tables still use class_name + parameters
JSON comparison (pending migration).

## Job Layer (`RAG_job.py`, `generative_job.py`)

- **`GenerativeJob`** is the generic job for text generation. At runtime, it
  detects whether the session uses `RAGTask` and delegates to `RAGJob`.
- **`RAGJob`** (`DashAI/back/job/RAG_job.py`) builds the `RAGPipeline` with all
  dependencies and runs generate/save/output in a background Huey task. It is a
  standalone job class (not a subclass of `GenerativeJob`), though it duplicates
  some status-update methods — see
  [known limitations](./05-known-limitations.md#code-duplication) for the
  rationale.

## Task Layer (`RAG_task.py`)

`RAGTask` extends `BaseGenerativeTask` and:

- Prepares input by folding chat history into the message list.
- Processes output by serializing the response and chunk references into
  DB-suitable format.
- Declares `USE_HISTORY = True` to enable history folding in the job layer.

## Typed Return Values

The pipeline uses typed dataclasses instead of raw dicts or lists:

| Dataclass             | Purpose                                          |
| --------------------- | ------------------------------------------------ |
| `RAGPipelineConfig`   | Validated pipeline parameters                    |
| `ModelRef`            | Parsed `{component, params}` reference           |
| `ChunkReference`      | A single retrieved chunk with document info      |
| `RAGGenerationOutput` | Typed pipeline output (message + chunks)         |
| `*FactoryResult`      | Each factory returns a typed result              |
| `SparsePersistence`   | On-disk reference for sparse retrievers          |
| `DensePersistence`    | Embedding matrix references for dense retrievers |
