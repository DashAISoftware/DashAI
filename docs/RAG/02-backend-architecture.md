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
SessionValidationService (services/RAG/)
  ├── prepare_RAG_params()       — POST validation (strict, recursive)
  ├── validate_update_payload()  — PUT validation (partial, recursive)
  └── QueryTransformationValidationService — optional query_transformation stage
       │
       ▼
Services (services/RAG/)
  │
  ├── SetupService              — indexing (build_index) + pipeline assembly
  ├── IndexStatusService        — read-only view of a session's index state
  ├── index_job_service.py      — functions to resolve / cancel a live indexing job
  ├── DocumentService           — loads parsed Data documents for the pipeline
  ├── SessionDocumentService    — session ↔ Data document links (attach/detach)
  ├── SessionDefaultsService    — server-side defaults for a new session
  ├── SessionConfigurationService — resolved configuration for the panel
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
  │     ├── LLMFactory           — resolve registry → instantiate
  │     └── TransformationFactory — resolve registry → validate → fill objects → instantiate
  ├── RAGPipeline                — inference orchestration
  └── documents/, chunking_models/, retrievers/, prompts/, transformation/ — pure domain models

Core (core/)
  └── component_validation.py — generic recursive component ref validation

### Supporting Modules

| Module                                      | Purpose                                                       |
|---------------------------------------------|---------------------------------------------------------------|
| `RAG_constants.py`                          | Canonical parameter key constants, shared across all layers   |
| `services/RAG/utils.py`                     | normalize_params(), build_parameters_hash() (SHA-256)         |
| `models/RAG/utils.py`                       | Utility functions (`hash_function` for SHA-256 hashing)       |
| `exceptions/`                               | Unified exception hierarchy (RAGWorkflowError + 10 sub-trees) |
| `retrievers/enums.py`                       | `MergeStrategy` enum for parallel retriever merge behavior    |
| `retrievers/persistence.py`                 | `SparsePersistence` / `DensePersistence` dataclasses          |
```

## Service Layer

Each DB-backed service receives a `db: Session` in its constructor. Services
are NOT registered in the DI container — they are instantiated per request/job.

### SessionValidationService

Centralized validation for RAG session creation (POST) and parameter updates
(PUT). Two public methods with shared private helpers:

- `prepare_RAG_params()` — POST validation. Only `generation_model` is
  required; `prompt`, `chunking_model` and `retriever_model` are filled from
  backend defaults when omitted. Resolves `prompt_id` → `prompt` **before**
  structural validation. `documents` always starts empty and a non-empty list
  is *rejected* if sent: there is no session to attach documents to yet, and
  saying so beats silently dropping the list.
- `validate_update_payload()` — PUT validation. Only validates keys present in
  the partial payload, and rejects `documents` outright — the
  `rag_session_document` links are the authority, and the session-document
  endpoints keep the session's list in step with them.

Both methods use `_validate_component_params()` which **recursively** validates
every `{component, params}` reference (including nested sub-components like
`BM25Vectorizer` inside `BM25Retriever`) against its own `SCHEMA`. If any fails
→ HTTP 400. The only tolerated incomplete payloads are the default prompts:
`DefaultRAGGenerationPrompt` / `DefaultQARAGenerationPrompt`, and the
transformation trio `DefaultQueryRewritingPrompt` /
`DefaultQueryExpansionPrompt` / `DefaultQueryDecompositionPrompt`. Each
auto-injects `template` from a language-based `TEMPLATES` dict before
validation. No other component auto-fills missing parameters.

Both POST and PUT additionally delegate the optional `query_transformation`
stage to `QueryTransformationValidationService` (see below), which is wired
into this service's constructor.

### QueryTransformationValidationService

Single-responsibility service for the optional `query_transformation`
parameter, extracted from `SessionValidationService`. It receives the
component registry plus `PromptService.validate_prompt_template` injected as a
callable, so it never reaches into prompt internals.

- `validate(normalized)` — structural and class checks. An **absent** key
  leaves the stage disabled; an explicit `None` is preserved as disabled (a PUT
  can use it to turn an existing stage off); a `dict` enables it and is checked:
  the outer `component` must resolve to a registered
  `BaseQueryTransformation` subclass; `params.prompt` must be present, be a
  `QueryTransformationPrompt`, and belong to the transformer's
  `TRANSFORMATION_PROMPT_BASE` family; `params.llm_model` must be present and
  be a `TextToTextGenerationTaskModel`. A caller-provided template for a
  non-default prompt must be a non-blank string with the required placeholders
  (validated through the injected callable); default transformation prompts may
  omit or blank theirs.
- `apply_defaults(normalized)` — resolves the transformer's own schema
  defaults plus the nested prompt's and LLM's placeholders, sitting under
  whatever the caller sent. The nested LLM's `context_window` is defaulted to
  2048 via `transformation_llm_overrides()` — between the model schema's
  conservative 512 and the generation window — while a caller-sent value always
  wins.

`SessionValidationService` calls `validate()` after model-key structure
validation and `apply_defaults()` alongside the generation-model defaults, on
both the POST (`prepare_RAG_params()`) and PUT (`validate_update_payload()`)
paths.

### SetupService

(Formerly `RAGSetupService`.) Two entry points, one code path:

- `build_index()` — documents → chunk set → chunking → retriever. Everything
  that makes documents retrievable, returned as an `IndexResult`. Takes an
  optional `progress(fraction, message)` callback so a job can report progress
  without this service knowing the job system exists.
- `build_pipeline()` — calls `build_index()`, then adds LLM → prompt, builds
  the optional query transformer via
  `RAGModelsFactory.create_query_transformation(...)` when
  `config.query_transformation` is not `None`, and returns a `RAGPipeline`
  instance.

The split exists so indexing never loads generation weights. It is also LLM-free
in its own right: every RAG LLM is obtained as a
[`LazyLLM`](#lazy-llms-and-per-stage-release) proxy, so the configuration record
is resolved and committed while the backend itself is constructed on first use.
`build_index()` sets up the retriever — an LLM-evaluated retriever's evaluation
model is a proxy too — without loading it; `build_pipeline()` adds the
generation LLM, the prompt and the optional transformer, and still constructs no
LLM model. `build_pipeline` delegates rather than repeating the steps, so the two
paths cannot drift.

No validation logic — that lives in `SessionValidationService`.

### DocumentService

Reads the parsed content of the Data-module documents a pipeline indexes:
`load(document_ids)` resolves each `DataDocument` (a missing row or one whose
status is not `FINISHED` raises `ValueError`), loads its stored parse with
`load_document`, and builds a `RAGDocument` that keeps only the `Text` items
and maps character offsets back to pages. Documents are parsed once by the Data
module and never change afterwards, so RAG never extracts text itself. See
[`06-document-processing.md`](./06-document-processing.md) for the loader
system, storage layout, and the attach/detach rules.

### SessionDocumentService

Owns the `rag_session_document` links between sessions and Data documents:
`attach()` / `detach()` validate the session and the documents, discard the
session's indexes, and rebuild `parameters["documents"]` with a history entry.
Documents belong to the Data module, so detaching (or deleting the session)
removes the link, never the document.

### ChunkingService

Chunk set identity via SHA-256 signature (migrated from `chunk_set_utils.py`)

- lookup-or-create chunking model + chunk persistence (migrated DB logic from
  `ChunkingModelFactory`).

### PromptService

Prompt CRUD + get_or_create via deterministic `parameters_hash` (SHA-256 of
`json.dumps(params, sort_keys=True)`). Uses `services/RAG/utils.py` shared
helpers. Template validation delegates to the component's declared
`required_placeholders` (for generation prompts `{input}` and `{chunks}`; for
transformation prompts `{input}` and `{history}`, plus `{n}` for expansion).
Session-scoped prompt copies.

### LLMService

Lookup-or-create of LLM records in `rag_generation_model` table via
`parameters_hash` (same deterministic hash as PromptService). Replaces the
DB logic that was in `LLMFactory`.

`get_or_create_lazy()` performs the same normalization, lookup/creation,
validation and commit, but returns a `LazyLLM` proxy instead of an instance:
the real backend is constructed on the first `generate` /
`generate_function_call` and released by `close()`. The eager
`get_or_create()` remains for callers that need an instance immediately.
`RetrievalLLMService` inherits the lazy path for LLM-evaluated retrievers,
persisting into its own `rag_retrieval_model` table.

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

`invalidate_session_artifacts()` deletes every chunk set the session owns
together with everything fitted on it. It takes `commit=False` so a caller can
fold the deletion into a larger unit of work; on-disk storage folders are
queued with `remove_after_commit` and removed only after the caller's commit,
since an `rmtree` cannot be rolled back.

`_other_sessions_with_same_config()` is gone, but the protection it was meant
to provide is not — it is just keyed on what is actually shared now. The old
function compared the session's `documents` list, so it blocked cleanup for
two sessions that merely shared a configuration while saying nothing useful
about what was safe to delete. Which rows are actually shared decides the
guard:

- **Per chunk set** — retrievers, embedding matrices, chunks. A chunk set
  belongs to one session now, so nothing else can be using them and they are
  deleted outright.
- **Per configuration** — `rag_chunking_model` and `rag_embedding_model` are
  matched by `(class_name, parameters)` alone, so every session that settled on
  the same components shares one row. A new session takes the backend defaults,
  which makes sharing the ordinary case rather than a corner one. Each is
  deleted only once nothing references it: no other session's `rag_pipeline`
  for the chunking model, and no dense retriever or embedding matrix for the
  embedding model.

## Pure Factories (no DB or FS)

After the refactor, all sub-factories are **pure** — they only construct
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

Same pattern — resolves registry, instantiates, returns. RAG setup paths do not
call it eagerly: they use `LLMService.get_or_create_lazy()` (or `fill_objects`
with `lazy_model_classes`), so assembly resolves configuration without loading
LLM weights.

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

### TransformationFactory

```python
class TransformationFactory:
    def __init__(self, registry: ComponentRegistry): ...
    def create(self, component_name, params) -> TransformationFactoryResult:
        # normalize params → resolve registry → schema validate → fill objects → instantiate
```

`create()` normalizes the params, resolves the component name in the registry,
asserts the class is a `BaseQueryTransformation`, validates params against the
class `SCHEMA`, fills nested component objects via `fill_objects`, and
instantiates the transformer. An unknown name raises
`RAGComponentNotFoundError`; a registered class that is not a transformer
raises `RAGTransformationConfigError`.

The nested `prompt` is instantiated eagerly, but `fill_objects` is called with
`lazy_model_classes=(TextToTextGenerationTaskModel,)`, so the nested
`llm_model` becomes a `LazyLLM`. Its backend is constructed on the first
`transform()` and released when the transformation stage closes.

The unified `RAGModelsFactory` exposes it as
`create_query_transformation(component, params)`, which is what
`SetupService.build_pipeline()` calls. The LLM-backed family lives in
`models/RAG/transformation/`: `BaseQueryTransformation` defines the contract
(`transform(message, history) -> QueryTransformationResult`),
`LLMQueryTransformation` owns the shared prompt/LLM/parse pipeline, and the
concrete techniques are `LLMQueryRewriter` (1 query), `LLMQueryExpander`
(up to `n_queries`) and `LLMQueryDecomposer` (model-decided sub-queries).
`llm_output_parser.py` parses the tolerant function-call output contract.

## Validation

Validation is centralized in `SessionValidationService` — endpoints are thin
delegators. The backend follows a **strict validation contract**: every
`{component, params}` reference is recursively validated against its own
`SCHEMA`. Any failure → HTTP 400. The backend only fills schema placeholders
(the default prompt templates, the picked generation model's omitted params,
and the optional transformation stage's defaults); it never guesses component
identity.

### Generic Component Validation (`core/component_validation.py`)

Two functions that work for ANY parameter structure, not just RAG:

- `find_component_refs(data)` — Recursively walks dicts/lists finding all
  `{"component": "...", "params": {...}}` patterns. Returns list of
  `(json_path, component_name, params)` tuples.
- `validate_component_refs(data, registry)` — Validates that all found
  components exist in the registry. Returns list of error messages.

### RAG Session Creation Validation (POST)

Delegated to `SessionValidationService.prepare_RAG_params()` (the model/task
check happens first, in the endpoint):

1. Model and task are checked against the component registry.
2. Parameters are normalized via `normalize_payload()`.
3. Backend defaults fill `chunking_model`, `retriever_model` and `prompt` for
   the keys the caller omitted (an explicit `prompt_id` suppresses the default
   prompt). Explicitly sent values win.
4. If `prompt_id` is present, resolved to a `prompt` component ref **before**
   structural validation.
5. Model-key structure validation — with defaults applied, every model key must
   be a `{component, params}` mapping.
6. The optional `query_transformation` stage is checked by
   `QueryTransformationValidationService` (structure plus class checks).
7. Component refs checked against the registry (`validate_component_refs()`).
8. Generation-model and transformation defaults — omitted parameters are
   resolved from the picked classes' schemas (the transformation LLM's
   `context_window` defaults to 2048).
9. **Recursive schema validation** — every `{component, params}` ref (including
   nested sub-components like `BM25Vectorizer` inside `BM25Retriever`) is
   validated against its own `SCHEMA`. If any fails → HTTP 400. On this pass the
   default generation and transformation prompts auto-inject `template` from a
   language-based `TEMPLATES` dict, so an absent or blank default template is
   never persisted. No other component auto-fills missing parameters.
10. `documents` is forced to `[]`; sending a non-empty list is an error.
11. Prompt template placeholders validated when an explicit template is
    provided.

### RAG Parameter Update Validation (PUT)

Delegated entirely to `SessionValidationService.validate_update_payload()`:

1. Normalize via `normalize_payload()`.
2. Resolve `prompt_id` → `prompt` (step 0, before validation — mirrors POST).
3. Validate structure of each sent component ref (`component` + `params` keys).
4. The optional `query_transformation` stage is checked by
   `QueryTransformationValidationService` (structure plus class checks).
5. `validate_component_refs()` — validate all components exist in registry.
6. Generation-model and transformation defaults, then **recursive schema
   validation** of every present component ref.
7. Reject `documents` if sent (managed by the session-document endpoints).
8. Returns validated dict. Then the endpoint merges with old params and
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
        documents: Dict[int, RAGDocument],
        chunks: Dict[int, Dict[int, Chunk]],
        prompt_model: BasePrompt,
        chunking_model: BaseChunkingModel,
        retriever: BaseRetriever,
        llm_model: TextToTextGenerationTaskModel,
        query_transformation: Optional[BaseQueryTransformation] = None,
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
        self.query_transformation = query_transformation
```

No DB access, no factory calls, no wiring — purely assigns attributes.

### Lazy LLMs and per-stage release

All three stage LLMs are `LazyLLM` proxies: the query-transformation model, the
retriever's evaluation model and the generation model. Their configuration is
resolved and validated during assembly — the component `SCHEMA` is checked with
the effective parameters, without loading any weights — but the real backend is
constructed on first use and released when its stage ends:

- **Transformation** — `_resolve_queries` loads the transformer's LLM if it
  needs it; `query_transformation.close()` runs once `transformation_ms` has
  been taken.
- **Retrieval** — the retriever's evaluation LLM loads on its first query;
  `retriever.close()` runs once `retrieval_ms` has been taken. Composite
  retrievers close every child, and LLM-evaluated retrievers close their own
  evaluation LLM before delegating to the base.
- **Generation** — the generation LLM loads on `_generate_answer` and is closed
  once `generation_ms` (and `total_ms`) have been taken.

An outer `finally` releases all three again as a safety net, so an early failure
cannot leak a loaded model. Releases are idempotent and suppress cleanup
errors, so teardown never masks the stage failure. The proxies survive the call:
closing drops the real backend, and the next stage or turn reconstructs it.
These are the **top-level** stage LLMs, so the generation model, the retriever's
evaluation model and the transformer are never resident simultaneously; peak
memory is the largest top-level model, not the sum of all three. Stage timings
include the first-use model construction inside that stage and exclude that
stage's teardown; `total_ms` includes all teardowns.

The hooks live on `BaseRetriever` / `CompositeRetriever` /
`LLMEvaluatedRetriever` and `BaseQueryTransformation` /
`LLMQueryTransformation`. Their defaults are no-ops; subclasses holding a model
extend them.

### Generation Flow

`generate(input_data, progress_callback=None)`:

1. Extract the current message + history from the last entry in the input tuple.
2. Resolve the query list (`_resolve_queries`). When the transformation stage is
   disabled (`query_transformation is None`), the queries are the one-element
   `[input_message]` and the transformed-query list is `None`. When enabled, the
   transformer runs (rewriting → 1 query, expansion/decomposition → n queries);
   a `RAGTransformationError` is wrapped in `RAGPipelineRuntimeError`, and an
   empty result also raises `RAGPipelineRuntimeError`. The resolved list is
   always non-empty and is what retrieval runs over. The transformer is closed
   after its timing is taken.
3. Per-query retrieve through the single `multi_query_retrieval` path. Every
   retriever's `retrieve()` returns a `(chunks, trace)` tuple, so this step
   collects one trace node per query (`{"query", "retriever"}`) and merges the
   per-query chunk lists round-robin by `merge_round_robin`, de-duplicating by
   `(document_id, document_position)`; a one-element list is effectively a
   no-op, preserving its content and order. The retriever is closed after its
   timing is taken.
4. `_build_chunk_references(chunks)` → format chunks into text + dict. The
   dict keys come from the shared `trace_utils.chunk_ref` helper, so the trace
   nodes' chunk references and the `Dict` row keys are byte-identical.
5. `prompt_model.format(input, chunks, queries)` → render prompt. The `{queries}`
   placeholder stays optional: it is `None` when no transformation ran, and
   otherwise the transformed queries joined with `"; "`.
6. `llm_model.generate(history + [{"role": "user", "content": prompt}])` → response.
   The generation LLM is closed after its timing is taken.
7. Return `RAGGenerationOutput(message, chunks, queries, trace, timings)`.

The optional `progress_callback` receives one small payload per stage:
`{"stage": "transforming"}` (only when the transformation stage is enabled),
`{"stage": "retrieving", "queries": [...]}` once the queries are resolved, and
`{"stage": "generating"}` just before the LLM call. The pipeline deliberately
does not catch reporter exceptions; the job layer's reporter is the one that
swallows failures (see [RAGJob](#ragjob)).

LLM-backed stages may add two optional, LLM-authored keys to any payload:
`message` (a short user-facing sentence) and `justification` (a short
rationale). `LLMQueryTransformation` emits a `transforming` update when the
model supplies them; the pipeline forwards the transformation narrative in the
initial `retrieving` payload; and the LLM-evaluated retrievers emit additional
`retrieving` updates after each valid verdict. Those retriever updates omit
`queries` because a retriever only knows the single query it is working on.
When the model supplies no narrative, no extra keys or events are emitted, so
the stage-only payloads above remain unchanged.

## RAGJob

Uses `SetupService.build_pipeline()` instead of manual wiring:

```python
setup_service = SetupService(db, component_registry, config["RAG_PATH"])
model = setup_service.build_pipeline(pipeline_config)
```

Since the chunk-set signature makes indexing idempotent, this is a cache hit
for a session that was already indexed — and remains the fallback for one that
was not.

Before building the config the job filters the session's stored parameters down
to a whitelist, `_RAG_PARAM_KEYS = RAG_PARAM_KEYS | RAG_OPTIONAL_MODEL_KEYS`, so
only pipeline-shaped keys (including the optional `query_transformation` stage)
reach `RAGPipelineConfig`.

`run()` deliberately uses **two** database sessions so a connection is never
held open during LLM inference, which may take minutes:

1. **Session 1** loads the process/session, builds the pipeline, prepares the
   input and marks the process started.
2. **No session** — the generation call runs, receiving a best-effort progress
   reporter.
3. **Session 2** re-opens a session to persist the output rows and mark the
   process finished.

The progress reporter (`_make_progress_reporter`) opens a short-lived session
per progress event (pipeline stage or LLM narrative update), stores the payload
on `GenerativeProcess.progress` and commits, so a polling frontend sees the
current stage. Reporting is best-effort: any failure
is logged as a warning and swallowed, because a transient DB error must never
fail the chat turn (the pipeline itself does not catch reporter exceptions).
The process's `progress` is cleared on finish and on error. Cleanup runs on
every failure path too — setup, generation and output persistence all release
the pipeline models and clear the process progress before the job is marked
errored.

## RAGIndexJob

Indexing runs up front rather than as a side effect of the first message, so a
user who has just uploaded a document is not paying for it on their first
question.

```python
POST /api/v1/rag/sessions/{id}/index   → enqueues RAGIndexJob(session_id=...)
GET  /api/v1/rag/sessions/{id}/index-status
```

The endpoint is idempotent and coalescing: no documents, already indexed, and
already indexing all return the current state without enqueueing. Callers
therefore fire it after *any* change rather than deciding for themselves which
settings invalidate the index — the chunk-set signature already owns that rule.

`GenerativeSession.index_job_id` points at the run. It is only a pointer: the
queue's `task_copy` table stays authoritative for whether that job is alive, so
a stale id resolves to nothing and is overwritten by the next request. The
queue's watchdog flips a dead job to `killed` within ~10s, so nothing gets
stuck.

Four write routes cancel a live run *before* mutating, because
`CleanupService` would otherwise delete the very rows the job is writing:
`PUT /generative-session/{id}/parameters`, `DELETE /generative-session/{id}`,
and the session's document attach/detach routes (`POST` / `DELETE`
`/api/v1/rag/sessions/{id}/documents`). Uploading a document into the Data
module does not cancel anything — the session is only touched by the attach
call that follows the parse.

## RAGPipelineConfig

Validated parameter dataclass. Used by `SetupService` and `RAGJob`. Parses the
raw kwargs dict once into typed fields and raises `RAGPipelineConfigError` on
missing required keys, malformed `{component, params}` refs, or unknown keys.
Reads parameter keys from `RAG_constants.py` (`RAG_INFRA_KEYS`,
`RAG_MODEL_KEYS`, `RAG_PARAM_KEYS`, `RAG_PARAM_QUERY_TRANSFORMATION`, and
`RAG_PARAM_KEYS_ALL` for the unknown-key guard).

`query_transformation` is an optional `ModelRef`: `from_kwargs()` parses it when
present, treats an absent key or a `None` value as "stage disabled", and rejects
any other non-dict value. The unknown-keys guard accepts exactly
`RAG_PARAM_KEYS_ALL` (the infra, model and optional-model keys); anything else
raises rather than being silently ignored.

## Retriever Architecture

### Class Hierarchy

```
BaseRetriever (ABC, DashAI Component)
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

Every retriever's `retrieve(query, **kwargs)` returns a
`(chunks, trace)` tuple; there is no optional/parallel API. The trace is a
JSON-serializable node `{"name": <class name>, "chunks": [<refs in retrieval
order>], "children": [<child nodes>], ...}` built by
`retrievers/trace_utils.py::retriever_trace`. Chunk refs use
`trace_utils.chunk_ref` — the single source of the `"<document_id>_<position>"`
format that also keys the pipeline's `Dict` row. `children` is always a list
(even for single-child composites) and is omitted for unit retrievers;
techniques may add extras (the cross-encoder adds `scores` when it re-ranks).
Composites capture their children's nodes while keeping their merge/rerank
mathematics unchanged. The LLM-evaluated retrievers add a `rounds` list; each
entry may carry the verdict's `message`/`justification`. The ensemble's
planning verdict uses `planning_message`/`planning_justification` so a later
post-round verdict cannot overwrite it.

### Dense Retriever Two-Layer Design

The dense retriever separates concerns into two layers:

1. **Embedding layer** (`DenseEmbedding` subclasses) — Handle model loading,
   tokenization, pooling, and vector generation. These are DashAI Components
   registered in the component registry. Registered today:
   `SentenceTransformerEmbedding`, `BERTEmbedding`, `DistilBERTEmbedding`,
   `RoBERTaEmbedding`, `E5Embedding`, `InstructorEmbedding`, `LaBSEmbedding`.
   `HuggingFaceEmbedding` is the abstract base of the HF-backed family, and
   `FastTextEmbedding` exists in the package but is not registered.
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

`ChunkingService.build_chunk_set_signature` computes a deterministic SHA-256
hash of:

- The owning `session_id`
- Sorted document IDs
- Sorted chunking configuration (e.g., chunking model component + params)

The signature is UNIQUE, so a chunk set with the same signature is reused —
re-chunking the same documents with the same parameters is avoided, and two
sessions over the same Data documents still get separate chunk sets.

**Note:** `get_or_create_chunk_set()` uses SELECT-then-INSERT without a lock.
A concurrent race cannot persist duplicate signatures; the losing request
surfaces a database error instead.

## Document Loaders

Documents are uploaded and parsed by the **Data module**, not by RAG. Parsing
is a `DocumentDataLoader` component (`dataloaders/classes/`) selected at
upload time; the four registered loaders are
`PlainTextDocumentDataLoader` (txt, md, rst, tex, csv),
`PypdfDocumentDataLoader`, `PdfPlumberDocumentDataLoader` and
`PdfMinerDocumentDataLoader` (pdf). A loader turns one file into a
`DashAIDocument` — an ordered list of `Text` / `DashAIImage` items with pages —
and RAG keeps only the `Text` items. See
[`06-document-processing.md`](./06-document-processing.md) for the loader
parameters, storage layout, upload flow, and the document endpoints.

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
- Processes output into five typed `ProcessData` rows, in pipeline order:
  `Queries` (JSON list of the queries used for retrieval), `Dict` (JSON map of
  the retrieved chunks), `Trace` (JSON list of per-query retrieval trace nodes),
  `Timings` (JSON object of per-stage wall-clock milliseconds) and `str` (the
  answer message). The `Queries` row is always emitted; without the
  transformation stage it holds the one-element `[input message]` list. The
  `Trace` row references chunks by the same `"<document_id>_<position>"` keys
  as `Dict`, so the frontend can join them without duplicating chunk payloads.
  The `Timings` row serializes `PipelineStageTimings.to_dict()` — exactly the
  keys `transformation_ms`, `retrieval_ms`, `generation_ms` and `total_ms` —
  with `transformation_ms` exactly `0.0` when the transformation stage is
  disabled.
- Declares `USE_HISTORY = True` to enable history folding in the job layer.

## Typed Return Values

The pipeline uses typed dataclasses instead of raw dicts or lists:

| Dataclass             | Purpose                                          |
| --------------------- | ------------------------------------------------ |
| `RAGPipelineConfig`   | Validated pipeline parameters                    |
| `ModelRef`            | Parsed `{component, params}` reference           |
| `ChunkReference`      | A single retrieved chunk with document info      |
| `RAGGenerationOutput` | Typed pipeline output (message + chunks + queries + trace + timings; `queries` feeds the `Queries` output row, `trace` feeds the `Trace` row and `timings` feeds the `Timings` row) |
| `PipelineStageTimings` | Per-stage wall-clock milliseconds (`transformation_ms`, `retrieval_ms`, `generation_ms`, `total_ms`); `to_dict()` serializes them for the `Timings` output row |
| `QueryTransformationResult` | Typed transformer output; `queries` is the list retrieval runs over (one element for rewriting) |
| `*FactoryResult`      | Each factory returns a typed result              |
| `SparsePersistence`   | On-disk reference for sparse retrievers          |
| `DensePersistence`    | Embedding matrix references for dense retrievers |
