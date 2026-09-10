# Known Limitations and Operational Notes

## Performance

- **Chunk similarity matrices are held in RAM.** Works for low hundreds of
  documents but will not scale to millions. No out-of-core or approximate
  indexing.

- **No streaming.** The frontend waits for the full LLM response before
  displaying it. Streaming support is not implemented.

- **No FAISS or HNSW indexing.** Dense retrieval performs O(n*dim) brute-force
  similarity search per query. Large document collections will be slow.

- **Cross-encoder retrievers** perform O(n) pair scoring per query over
  candidate chunks from the child retriever. With large candidate sets
  (controlled by the child's own `top_k`), this can be slow on CPU.

- **DB session held open during LLM inference.** The same database transaction
  remains open while the LLM generates a response, which risks connection
  timeout on slow LLM calls.

## Concurrency

- **`get_or_create_chunk_set()`** uses a SELECT-then-INSERT pattern without a
  lock or upsert. Safe for single-user usage but could create duplicate chunk
  sets under concurrent requests.

- **Huey consumer runs in-process.** In dev mode it spawns as a subprocess; in
  PyInstaller bundles it runs as a daemon thread. Both models limit
  parallelism.

## Unused Components

- **`DefaultAugmentationPrompt`** is registered in the component registry but
  **commented out** in `get_initial_components()`. The augmentation prompt
  family (query expansion / HyDE-style) is not yet wired into the pipeline.

- **`CustomAugmentationPrompt`** is registered but unused by the pipeline.

## Type System Caveats

- **Prompt `chunks` type:** The pipeline passes a formatted `str` to
  `prompt.format()`, but the abstract `RAGGenerationPrompt.format()` and some
  subclasses declare `chunks: List[str]`. Only `str` works at runtime. The
  abstract base signature should match the concrete usage.

- **`score_chunks()` contract:** The abstract method declares return type
  `List[float]`, but all implementations return `List[Tuple[int, float]]`
  (chunk ID, distance). Consumers destructure tuples, so the abstract
  signature is wrong.

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

- **`GenerativeJob` and `RAGJob` share identical `set_status_as_delivered()`,
  `set_status_as_error()`, and `get_job_name()` methods.** The code is
  duplicated rather than extracted into a shared helper. `RAGJob` is a
  standalone `BaseJob` subclass (not a subclass of `GenerativeJob`), so the
  common status-update logic is copied rather than inherited. This is accepted
  technical debt; a future refactor should extract a shared mixin or base class.

- **`FastTextEmbedding`** is defined in
  `models/RAG/embeddings/dense/fasttext_embedding.py` but is **not exposed**
  through `embeddings/dense/__init__.py`. It must be explicitly imported and
  registered if needed.

## Deprecated Patterns

- The old `notebooks/`, `images/`, `explanations/` directories listed in the
  runtime data layout are no longer actively used by the RAG module.

## Extractors

- **PypdfExtractor** default `strict=True` rejects malformed PDFs (xref
  errors). Use `strict=False` for broken PDFs.
- **EasyOCRExtractor** requires the `easyocr` dependency (heavy, downloads
  models on first use).

## Validation

- **Strict validation** requires ALL sub-component params to be complete at
  session creation. The frontend must send full configs; the backend never
  fills defaults (except prompt templates for default prompts).
- **Parameters hash** only covers `rag_prompt` and `rag_generation_model`.
  `rag_chunking_model`, `rag_embedding_model`, and retriever tables still
  compare JSON columns directly — fragile to key ordering in SQLite.
