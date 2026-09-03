# End-to-End Execution Flow

## Step-by-Step

### 1. Session Creation

The user gives the session a name and picks an LLM (`RAGCreatePage`). Nothing
else is asked: chunking, retrieval and the prompt come from backend defaults,
and documents are uploaded into the session once it exists.

Frontend calls `POST /api/v1/generative-session/`. The endpoint delegates to
`RAGSessionValidationService`:

1. **Model & task validation** — checks `model_name` and `task_name` exist in
   the component registry.
2. **Documents** — forced to `[]`. A non-empty list is rejected: there is no
   session id to attach documents to yet.
3. **Parameter normalization** — `normalize_payload()` transforms frontend-style
   property wrappers.
4. **Prompt resolution** — if `prompt_id` is provided, it is resolved to a
   `{component, params}` ref **before** structural validation.
5. **Recursive schema validation** — every `{component, params}` ref (including
   nested sub-components like `BM25Vectorizer` inside `BM25Retriever`) is
   validated against its own `SCHEMA`. If any fails → HTTP 400.
6. **Default prompt template injection** — `DefaultRAGGenerationPrompt` and
   `DefaultQARAGenerationPrompt` auto-inject `template` from a language-based
   `TEMPLATES` dict. No other component auto-fills missing parameters.
7. **Component ref validation** — `validate_component_refs()` recursively
   checks all components exist in the registry.
8. **Prompt template validation** — if an explicit template is given, validates
   that it contains the required placeholders (`{input}`, `{chunks}`).

On success, a `GenerativeSession` record is persisted with:

- `task_name` — Set to `"RAGTask"` for RAG sessions.
- `model_name` — Set to `"RAGPipeline"`.
- `parameters` — The validated configuration dict, with `documents: []`.

### 2. Adding Documents

The user uploads documents into the session from its left panel, which calls
`POST /api/v1/document/session/{session_id}`. Each upload appends the new id to
the session's `parameters["documents"]` and historizes the change, so the
pipeline, the chunk-set signature and the index status all see it.

The user may also adjust the configuration at any point, through
`PUT /api/v1/generative-session/{id}/parameters`. That replaces every
parameter at once, and `CleanupService.cleanup_orphaned_resources` drops
whatever the previous configuration had fitted.

### 3. Process Creation

When the user sends a message, the frontend calls
`POST /api/v1/generative-process/` with the input text. The endpoint refuses a
RAG session that still has no documents — otherwise the job would fail deep
inside the retriever, fitting an index over no text. Otherwise this creates a
`GenerativeProcess` row, and the frontend then dispatches a job through
`POST /api/v1/job/`.

### 4. Job Execution

Huey picks up the job. `GenerativeJob` sees the session uses `RAGTask` and
delegates to `RAGJob`, which:

1. Builds a `RAGPipelineConfig` from `session.parameters` alone — the filter
   `_RAG_PARAM_KEYS` decides what reaches the pipeline, which is why
   `parameters["documents"]` has to be kept in step with the foreign key.
2. Calls `SetupService.build_pipeline()`: documents → chunk set → chunking →
   retriever → LLM → prompt. Chunk sets and fitted retrievers are reused when
   their signature already exists, so only a changed configuration pays to
   re-index.
3. Runs `RAGPipeline.generate()` and hands the output to
   `RAGTask.process_output()`, which serializes the answer and its chunk
   references.

### 5. Displaying the Answer

The frontend polls `GET /api/v1/jobs/{job_id}`. When the job is delivered, the
chat renders the message plus its `referenceOutput`, and `SourcesDisplay` /
`DocumentReferencesModal` show which passages were retrieved.

`GET /api/v1/rag/sessions/{id}/index-status` reports whether the documents are
indexed for the *current* configuration, distinguishing `no_documents`,
`not_indexed`, `stale` (indexed before, under a different configuration) and
`indexed`. The message it returns is already localized.
