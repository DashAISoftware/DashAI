# Known Limitations and Operational Notes

## Performance

- **Chunk similarity matrices are held in RAM.** Works for low hundreds of
  documents but will not scale to millions. No out-of-core or approximate
  indexing.

- **Chunk sets are not shared between sessions.** Documents belong to the Data
  module, but `RAGChunkSet.signature` includes the owning session id alongside
  the document ids, so it always differs. Two sessions configured identically
  over the same Data documents each chunk them and fit their own retriever.
  This is the accepted cost of session isolation; the parsed document folder on
  disk is shared, since it belongs to the Data document.

- **No streaming.** The frontend waits for the full LLM response before
  displaying it. Streaming support is not implemented.

- **No FAISS or HNSW indexing.** Dense retrieval performs O(n*dim) brute-force
  similarity search per query. Large document collections will be slow.

- **Cross-encoder retrievers** perform O(n) pair scoring per query over
  candidate chunks from the child retriever. With large candidate sets
  (controlled by the child's own `top_k`), this can be slow on CPU.

- **Generation occupies the single Huey worker.** `RAGJob` holds no database
  session while the LLM runs — it loads and builds in one session and saves the
  output in a second — but the model load and inference are synchronous and
  take the worker's only slot, so other queued jobs wait for the whole turn.

- **The optional query-transformation stage adds an LLM call per turn.** When
  enabled, one model call — and possibly a distinct model instance — runs
  before any retrieval, ahead of the generation call itself.

- **`n` transformed queries mean `n` retriever calls per turn.** Retrieval runs
  once per query and merges the ranked lists round-robin, de-duplicating by
  `(document_id, document_position)`; there is no score fusion or re-ranking
  beyond that interleave. The stored trace also carries one node per query, so
  the process output grows with the query count.

- **LLM stages are not resident simultaneously, but a nested retriever can
  exceed one model.** Each top-level stage's model is a lazy proxy: it loads
  when its stage starts and is closed as soon as the stage ends, so peak memory
  is the largest **top-level** stage — the generation model, the retriever LLM
  and the transformer are never resident at the same time. A **nested**
  LLM-evaluated retriever can keep its parent and child evaluation LLMs live
  simultaneously, so peak can exceed one model in that configuration. The
  trade-off is reloading weights per turn/stage whenever the same checkpoint is
  used more than once. `context_window` still dominates the KV-cache footprint —
  a Phi-4-mini at a 20k-token window already spends ≈ 2.5 GiB — so a single
  large GGUF can still fail to fit. The GGUF loader raises an actionable error
  naming the model, device and context window and suggesting CPU, a lower
  `context_window` or a smaller checkpoint; llama.cpp's free-memory report in
  that error is best-effort. HuggingFace download/network failures are reported
  as download failures, not as insufficient memory, and a missing or partial
  GGUF file raises a file-specific "missing/incomplete, re-download" error.
  `is_downloaded` likewise requires a matching GGUF file on disk.

- **The pure factory path still builds nested LLMs eagerly.** Calling
  `RAGModelsFactory.create_retriever()` directly — or using `RetrieverFactory`
  on its own — resolves nested LLMs when the retriever is constructed instead of
  deferring them. The production path goes through `RetrieverSetupService`,
  which wraps each LLM stage in the lazy resolver, so use the setup service for
  VRAM-constrained deployments.

- **Lazy plugin LLMs must expose function-calling support on the class.** The
  lazy wrappers capture the capability from the component class, not from an
  instance, so a plugin LLM used lazily has to implement
  `supports_function_calling()` as a classmethod or set
  `SUPPORTS_FUNCTION_CALLING` on the class. An instance-only implementation is
  invisible to the wrapper.

- **GPU embedding models and cross-encoders are not released by the retriever
  close hooks.** The lazy lifecycle covers the stage LLMs; a dense embedding
  model or a GPU cross-encoder stays on the device for the life of the
  retriever. On a small GPU prefer the CPU variants for those components.

- **Nested LLM parameters are validated during assembly.** Deferring
  construction does not defer validation: a transformer's or retriever's nested
  LLM is checked against its `SCHEMA` while the pipeline is assembled, so bad
  parameters fail before any weights load.

## Concurrency

- **`get_or_create_chunk_set()`** uses a SELECT-then-INSERT pattern without a
  lock or upsert. `RAGChunkSet.signature` is UNIQUE, so a concurrent race
  cannot persist duplicate chunk sets; the losing request instead surfaces a
  database error (wrapped as `RuntimeError`).

- **SQLite foreign keys are not enforced.** The engine is created without
  `PRAGMA foreign_keys=ON` and nothing sets it per connection
  (`dependencies/database/sqlite_database.py`), so every `ondelete` clause in
  the models is documentation rather than behaviour. Cascading deletes have to
  come from SQLAlchemy relationships — which is why, for example,
  `GenerativeSession.document_links` carries `cascade="all, delete-orphan"`.

- **Huey consumer runs in-process.** In dev mode it spawns as a subprocess; in
  PyInstaller bundles it runs as a daemon thread. Both models limit
  parallelism.

- **`RAGJob` cleans up on every failure path.** Setup, generation and output
  persistence failures all release the pipeline models and clear the process
  progress before the job is marked errored, so a failed turn leaves neither
  loaded weights nor a stale progress payload behind.

## Unused Components

- **`DefaultAugmentationPrompt`** and **`CustomAugmentationPrompt`** are
  registered in `get_initial_components()` but are not referenced by any
  pipeline or validation code. The augmentation prompt family (query expansion
  / HyDE-style) is not yet wired into the pipeline.

- The query-transformation prompts (`Default`/`Custom` `QueryRewriting`,
  `QueryExpansion`, `QueryDecomposition`) and the `LLMQueryRewriter`,
  `LLMQueryExpander`, `LLMQueryDecomposer` components **are** wired: they are
  registered, validated by
  `services/RAG/query_transformation_validation.py`, and run by the pipeline.

## Query Transformation

- **Function-calling versus text route.** The stage uses constrained function
  calling only when the configured LLM reports support
  (`SUPPORTS_FUNCTION_CALLING`, true for the local GGUF text-generation base);
  every other model falls back to a tolerant text parser over the model's raw
  output. Output shape therefore depends on the model, not just the prompt.

- **A transformation failure fails the turn.** There is no silent fallback to
  the raw user message: if the model produces unparseable output, calls the
  wrong function, or the backend raises, the pipeline raises and the chat turn
  errors out.

- **The nested transformation LLM defaults to a 2048-token context window.**
  The server-side default (`RAG_TRANSFORMATION_LLM_CONTEXT_WINDOW`) covers the
  technique prompt plus the stage's history block, never retrieved chunks. A
  caller-supplied `context_window` wins.

- **`prompt` and `llm_model` refs are mandatory.** A transformer is built only
  from an explicit prompt component and an explicit text-to-text model
  reference; neither has an implicit default.

## Maintenance

- **After RAG model schema changes**, delete `sqlite.db` and the
  `~/.DashAI/rag/` directory to rebuild the database and chunk cache from
  scratch.

- **Tokenizer downloads on first use.** `TokenChunkModel` downloads the
  tokenizer from HuggingFace Hub lazily (on first `chunk_text()` call), but
  this still requires network access. Pre-download tokenizers for offline use.

- **Embedding models downloaded on first use.** Each `DenseEmbedding` subclass
  downloads its model from HuggingFace Hub on first instantiation. Pre-download
  for offline environments.

## Code Duplication

- **`RAGJob` reimplements `GenerativeJob`'s status helpers.**
  `set_status_as_delivered()`, `set_status_as_error()`, and `get_job_name()`
  are near-duplicates that have already diverged: the RAG job clears
  `progress` on error and prefixes its job name with `RAG:`. `RAGJob` is a
  standalone `BaseJob` subclass (not a subclass of `GenerativeJob`), so the
  logic is copied rather than inherited. This is accepted technical debt; a
  future refactor should extract a shared mixin or base class.

- **`FastTextEmbedding`** is defined in
  `models/RAG/embeddings/dense/fasttext_embedding.py` but is **not exposed**
  through `embeddings/dense/__init__.py`. It must be explicitly imported and
  registered if needed.

## Deprecated Patterns

- The old `notebooks/`, `images/`, `explanations/` directories listed in the
  runtime data layout are no longer actively used by the RAG module.

## Document Loaders

- **`PypdfDocumentDataLoader`** defaults to `strict=True`, rejecting malformed
  PDFs (xref errors). Use `strict=False` for broken PDFs. Parsing runs in
  `DocumentJob`, so a failure surfaces as an `ERROR` row (with its partial
  folder deleted) rather than a half-parsed document in the library.

## Validation

- **Parameters hash** only covers `rag_prompt` and `rag_generation_model`.
  `rag_chunking_model`, `rag_embedding_model`, and retriever tables still
  compare JSON columns directly — fragile to key ordering in SQLite.
- **Orphaned `rag_prompt` rows are not cleaned up.**
  `CleanupService.cleanup_orphaned_resources` handles retrievers and chunking
  models only. Rows are deduplicated by `parameters_hash` and the only writer
  is `get_or_create`, so orphans are bounded and harmless — but they do
  accumulate.
- **`RAGPrompt.pipelines` no longer cascades**, because a hash-deduplicated row
  is shared: deleting one prompt would have deleted other sessions'
  `rag_pipeline` rows. There is no DELETE endpoint for prompts; do not add one
  without re-auditing that.

## Empty sessions

A RAG session is created with no documents, so several things have to cope with
an empty `documents` list:

- `IndexStatusService` reports a `no_documents` status, rather than promising an
  indexing run that cannot happen.
- `POST /generative-process/` refuses a chat turn on an empty RAG session. That
  guard is load-bearing: without it `SetupService.build_pipeline` would create a
  chunk set over zero documents and fit a retriever on nothing, failing opaquely
  inside the vectorizer.
