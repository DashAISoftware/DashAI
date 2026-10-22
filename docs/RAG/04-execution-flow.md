# End-to-End Execution Flow

## Step-by-Step

### 1. Session Creation

The user gives the session a name and picks an LLM (`RAGCreatePage`). Nothing
else is asked: chunking, retrieval and the prompt come from backend defaults,
and documents are attached once it exists.

Frontend calls `POST /api/v1/generative-session/`. The endpoint delegates to
`SessionValidationService`:

1. **Model & task validation** — the endpoint checks `model_name` and
   `task_name` exist in the component registry.
2. **Parameter normalization** — `normalize_payload()` transforms frontend-style
   property wrappers.
3. **Backend defaults** — `build_default_parameters()` fills `chunking_model`,
   `retriever_model` and `prompt` for the keys the caller omitted (an explicit
   `prompt_id` suppresses the default prompt). Anything sent explicitly wins.
4. **Prompt resolution** — if `prompt_id` is provided, it is resolved to a
   `{component, params}` ref **before** structural validation.
5. **Model-key structure validation** — with defaults applied, every model key
   (`prompt`, `chunking_model`, `retriever_model`, `generation_model`) must be a
   `{component, params}` mapping.
6. **Query transformation validation** — the optional `query_transformation`
   key is validated next. Absent, the stage stays disabled and is not stored. An
   explicit `None` disables it and is preserved, so a later `PUT` can turn an
   existing transformation off. A `{component, params}` dict enables the stage
   and must name a registered `BaseQueryTransformation` whose nested `prompt`
   (a `QueryTransformationPrompt` family member, checked against the
   transformer's `TRANSFORMATION_PROMPT_BASE`) and `llm_model` (a
   `TextToTextGenerationTaskModel`) refs are present and correctly typed. A
   caller-supplied nested prompt template is validated here; default
   transformation prompts may omit or blank theirs.
7. **Component existence** — `validate_component_refs()` recursively checks all
   components exist in the registry.
8. **Model defaults** — the picked generation model's omitted parameters are
   resolved from its schema, and the same happens for the transformation stage
   when enabled: the transformer's own placeholders plus its nested prompt's and
   nested LLM's. The nested LLM's `context_window` defaults to `2048`
   (`transformation_llm_overrides()`), sitting under any caller-sent value: a
   transformation call carries only the technique prompt and the stage history,
   never retrieved chunks.
9. **Recursive schema validation** — every `{component, params}` ref (including
   nested sub-components like `BM25Vectorizer` inside `BM25Retriever`) is
   validated against its own `SCHEMA`. If any fails → HTTP 400. On this pass the
   default generation pair (`DefaultRAGGenerationPrompt`,
   `DefaultQARAGGenerationPrompt`) and the transformation trio
   (`DefaultQueryRewritingPrompt`, `DefaultQueryExpansionPrompt`,
   `DefaultQueryDecompositionPrompt`) auto-inject `template` from a
   language-based `TEMPLATES` dict before being validated, so an absent or blank
   default template is never persisted. No other component auto-fills missing
   parameters.
10. **Documents** — a non-empty list is rejected; `documents` is set to `[]`.
    There is no session id to attach documents to yet.
11. **Prompt template validation** — validates the template against the
    component's declared required placeholders (for the generation prompt,
    `{input}` and `{chunks}`).

On success, a `GenerativeSession` record is persisted with:

- `task_name` — Set to `"RAGTask"` for RAG sessions.
- `model_name` — Set to `"RAGPipeline"`.
- `parameters` — The validated configuration dict, with `documents: []`.

### 2. Adding Documents

Documents belong to the Data module, so the session attaches them rather than
owning them. `RAGDocumentUpload` creates the document through
`POST /api/v1/documents/` and enqueues its parse with `POST /api/v1/job/`
(`DocumentJob`); `AddFromDataDialog` picks documents that have already been
parsed. Either path attaches the selection through
`POST /api/v1/rag/sessions/{session_id}/documents`, which inserts the
`rag_session_document` links, discards the session's indexes, and rebuilds
`parameters["documents"]` with a history entry, so the pipeline, the chunk-set
signature and the index status all see the change. Detaching (`DELETE` on the
same route) removes only the link; the Data document stays.

The user may also adjust the configuration at any point, through
`PUT /api/v1/generative-session/{id}/parameters`. Only the keys present in the
payload are validated and merged over the stored parameters (partial update);
sending `query_transformation: null` turns an existing transformation stage off.
`CleanupService.cleanup_orphaned_resources` then drops whatever the previous
configuration had fitted.

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
   `_RAG_PARAM_KEYS` decides what reaches the pipeline (the required model keys
   plus the optional `query_transformation`), which is why
   `parameters["documents"]` has to be kept in step with the foreign key.
2. Calls `SetupService.build_pipeline()`: documents → chunk set → chunking →
   retriever → LLM → prompt, then the optional transformer only when
   `query_transformation` is configured
   (`RAGModelsFactory.create_query_transformation`). The indexing half
   (`build_index`) stops before the generation LLM, and every LLM is a lazy
   proxy — the generation model, the transformation model and an
   LLM-evaluated retriever's evaluation model are configured but not loaded, so
   assembly never loads LLM weights (retriever embedding models may still be built or loaded during indexing). Their parameters are still schema-validated
   during assembly, so a bad nested configuration fails there. Chunk sets and
   fitted retrievers are reused when their signature already exists, so only a
   changed configuration pays to re-index.
3. Runs `RAGPipeline.generate()` with a progress reporter that persists each
   stage payload on the process's `progress` column (best-effort: a failed write
   is logged and swallowed, never failing the turn), then hands the output to
   `RAGTask.process_output()`. `generate()` first reports `transforming` and
   runs `_resolve_queries` when a transformer is configured — otherwise
   `_resolve_queries` returns the one-element `[message]`; a transformation
   failure or an empty query list aborts with `RAGPipelineRuntimeError`. It then
   reports `retrieving` with the resolved queries, retrieves once per query and
   merges the ranked lists round-robin, de-duplicating by
   `(document_id, document_position)`, builds the prompt (the optional
   `{queries}` placeholder receives the joined queries, or no transformed
   queries when the stage is off), reports `generating`, and calls the LLM.
   LLM-backed stages may decorate these payloads with an LLM-authored
   `message` and `justification`. The transformer can emit a `transforming`
   update, the pipeline forwards that narrative in the initial `retrieving`
   payload, and LLM-evaluated retrievers emit further `retrieving` updates
   after each valid verdict. Those retriever updates omit `queries`; they are
   status updates, not a new query list. When the model supplies no narrative,
   the stage-only payloads are unchanged. On the function-calling route, a
   malformed or unusable function call — including arguments that cannot be
   parsed — is retried up to `function_call_max_trials` total attempts
   (default 3, capped at 10, counting the first) before the stage fails.
   Configuration errors such as `NotImplementedError` are not retried, and the
   text fallback route is never retried.
   **LLM lifecycle.** Every stage LLM is a lazy proxy that loads on stage
   entry and is closed on stage exit:

   - the transformer's model loads during `_resolve_queries` and is closed as
     soon as the transformation timing is taken;
   - the retriever's evaluation LLM loads on the first query of the retrieval
     stage and is closed when retrieval ends (composite retrievers close every
     child, including nested LLM-evaluated ones);
   - the generation LLM loads after the prompt is built and is closed right
     after generation.

   An outer `finally` releases all three again as a safety net, so an early
   failure cannot leak a model, and cleanup errors never replace the stage
   error. Peak memory is the largest **top-level** stage model rather than the
   sum of the stages — the generation model, the retriever LLM and the
   transformer are never resident at the same time. Stage timings include the
   first-use model construction inside that stage and exclude that stage's
   teardown; `total_ms` includes all teardowns. A nested LLM-evaluated retriever
   can still keep its parent and child evaluation models live together; see
   [known limitations](./05-known-limitations.md). The proxies survive the turn,
   so the next turn reloads whichever models it needs.

   `process_output()` serializes five typed rows in pipeline-chronological order
   — the `Queries` list, the chunk map (`Dict`), the retrieval `Trace` (per-query
   retriever node trees whose chunk refs join the `Dict` keys), the `Timings`
   object (per-stage wall-clock milliseconds), and the answer (`str`). The
   `progress` column is cleared when the turn finishes or errors.

### 5. Displaying the Answer

The frontend polls the process while the turn runs. `RAGChatProgress` renders
the current stage from `process.progress`: `transforming` (query rewriting),
`retrieving` with the resolved queries (which are shown in the status line), or
`generating`. When the payload carries an LLM-authored `message`, it replaces
the localized stage line, and `justification` renders as a smaller secondary
line. A justification-only retriever update (which omits `queries`) renders the
justification itself. A null or unrecognized payload with no narrative falls
back to the generic waiting bubble. When the job is delivered, the chat renders the answer plus its
`referenceOutput` (the chunk map) and `traceOutput` (the retrieval trace), and
`SourcesDisplay` shows the referenced-document count with **Chunks** and
**Pipeline** toggles. They expand an inline `TraceChunksPanel`: the Chunks view
lists the user message and the final chunks grouped by document with their
per-query provenance, and the Pipeline view shows the per-query selector, the
retriever trace trees, the selected chunk and the candidates discarded before
the answer. Clicking a trace chunk highlights it when it reached the answer, or
warns when it did not.

`GET /api/v1/rag/sessions/{id}/index-status` reports whether the documents are
indexed for the *current* configuration, distinguishing `no_documents`,
`not_indexed`, `stale` (indexed before, under a different configuration),
`indexing` (an indexing job is running now) and `indexed`. The message it
returns is already localized.
