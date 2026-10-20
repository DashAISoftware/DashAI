# RAG Module Overview

## What is RAG in DashAI

Retrieval-Augmented Generation (RAG) lets users upload documents and have
conversations with them. The pipeline retrieves relevant document chunks for
each user query and feeds them to an LLM as context, producing grounded
answers that cite the source material.

## Pipeline Stages

Four fixed stages plus an optional pre-retrieval query transformation stage:

```
User query
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│        0. Query Transformation (optional)                 │
│   Turn the message and the last `history_window` prior   │
│   messages into one or more search queries:              │
│     • LLMQueryRewriter     — 1-to-1 rewriting            │
│     • LLMQueryExpander     — 1-to-n expansion            │
│     • LLMQueryDecomposer   — 1-to-n decomposition        │
│   When disabled, the message itself is the only query.   │
└──────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│                  1. Document Loading                      │
│   Load the parsed Data-module documents (txt, pdf, md,   │
│   csv, rst, tex) and build in-memory RAGDocument objects │
│   that keep the Text items and map offsets back to pages. │
└──────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│                  2. Chunking                              │
│   Split each document into smaller pieces using one of:  │
│     • CharacterChunkModel    — fixed-size char windows   │
│     • TokenChunkModel        — token-aware splitting     │
│     • RecursiveCharacterChunk — separator-priority split │
│   Chunks are persisted to the DB and cached by SHA-256   │
│   signature for reuse within the session.                │
└──────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│                  3. Retrieval                             │
│   Retrieve every query independently, then merge the     │
│   ranked lists round-robin and de-duplicate by           │
│   (document_id, document_position):                      │
│     • Sparse retrievers    — TF-IDF, BM25                │
│     • Dense retrievers     — embedding-based similarity  │
│     • Composite retrievers — Sequential, Parallel, MMR   │
│   (Composite pattern: leaf + composite nodes)            │
│   Every retriever returns (chunks, trace).               │
└──────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│                  4. Generation                            │
│   Inject chunks (and, when the transformation stage      │
│   ran, the queries) into a prompt template and generate  │
│   a response via an LLM. Supports multi-language prompts │
│   (en/es/pt) and custom templates.                       │
└──────────────────────────────────────────────────────────┘
     │
     ▼
   Five typed output rows: Queries, Dict (chunks), Trace, Timings, str (answer)
```

## Code Location

| Layer                           | Path                                                                                                                                                                                             |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Services                        | `DashAI/back/services/RAG/`                                                                                                                                                                      |
| Pipeline                        | `DashAI/back/models/RAG/RAG_pipeline.py`                                                                                                                                                         |
| Factory                         | `DashAI/back/models/RAG/RAG_models_factory.py`                                                                                                                                                   |
| Sub-factories                   | `DashAI/back/models/RAG/llm_factory.py`, `prompts/prompt_factory.py`, `chunking_models/chunking_model_factory.py`, `retrievers/retriever_factory.py`, `transformation/transformation_factory.py` |
| Query transformation            | `DashAI/back/models/RAG/transformation/`                                                                                                                                                         |
| Transformation prompts          | `DashAI/back/models/RAG/prompts/transformation/`                                                                                                                                                 |
| Query transformation validation | `DashAI/back/services/RAG/query_transformation_validation.py`                                                                                                                                    |
| Constants                       | `DashAI/back/models/RAG/RAG_constants.py`                                                                                                                                                        |
| Utilities                       | `DashAI/back/models/RAG/utils.py`                                                                                                                                                                |
| Exceptions                      | `DashAI/back/models/RAG/exceptions/`                                                                                                                                                             |
| Retrievers                      | `DashAI/back/models/RAG/retrievers/` (subdirs: `dense/`, `sparse/`, `composite/`, `cross_encoder/`)                                                                                              |
| Chunking                        | `DashAI/back/models/RAG/chunking_models/`                                                                                                                                                        |
| Prompts                         | `DashAI/back/models/RAG/prompts/` (subdirs: `generation/`, `augmentation/`, `transformation/`)                                                                                                   |
| Documents                       | `DashAI/back/models/RAG/documents/`                                                                                                                                                              |
| Embeddings                      | `DashAI/back/models/RAG/embeddings/` (subdirs: `dense/`, `sparse/`)                                                                                                                              |
| Jobs                            | `DashAI/back/job/RAG_job.py`                                                                                                                                                                     |
| Task                            | `DashAI/back/tasks/RAG_task.py`                                                                                                                                                                  |
| Core                            | `DashAI/back/core/component_validation.py`                                                                                                                                                       |
| Frontend pages                  | `DashAI/front/src/pages/generative/RAG/` (entry point, creation) and `pages/generative/RAGSession/` (the session view)                                                                           |
| Frontend components             | `DashAI/front/src/components/generative/RAG/`                                                                                                                                                    |

## Quick Architecture

```
Browser / PyWebView
  → React (port 3000)
    → POST /api/v1/generative-session/   (create session)
      → Validate payload, components, documents, prompt, optional transformer
    → POST /api/v1/generative-process/   (create process)
    → POST /api/v1/job/                  (enqueue job)
      → Huey Job Queue
        → RAGJob.run()
          → SetupService.build_pipeline()
            → DocumentService → ChunkingService → RetrieverSetupService
            → LLMService → PromptService → TransformationFactory (optional)
            → RAGPipeline.generate()
              → [query transformation] → per-query retrieval → round-robin merge
              → prompt (optional {queries}) → LLM generation
          → RAGTask.process_output() → Queries, Dict, Trace, Timings, str rows
        → Frontend polls the process:
          GET /api/v1/generative-process/session/{id}
```

## Component Types

- **Chunking models** — Character, Token, Recursive character (all implement
  `BaseChunkingModel`)
- **Retrievers** — `BaseRetriever` base; Sparse (TF-IDF, BM25), Dense (via
  `DenseEmbedding` subclasses), Cross-Encoder (SentenceTransformer re-rankers),
  Composite (Sequential, Parallel, MMR Reranker, LLM-evaluated depth and
  ensemble)
- **Query transformations** — `BaseQueryTransformation` base; LLM-backed
  transformers (`LLMQueryRewriter`, `LLMQueryExpander`, `LLMQueryDecomposer`)
  that turn the user message into one or more search queries before retrieval
- **Prompts** — Generation prompts (Default, Custom, QA) in en/es/pt;
  query transformation prompts (Rewriting, Expansion, Decomposition, each
  Default + Custom); augmentation prompts (Default, Custom) are registered but
  not wired into the pipeline
- **LLMs** — GGUF chat checkpoints (Llama, Mistral, Mixtral, Qwen, SmolLM,
  Phi-4) plus any other `TextToTextGenerationTaskModel` registered in the
  component registry
- **Embeddings** — Registered `DenseEmbedding` subclasses: BERT, DistilBERT,
  E5, Instructor, LaBSE, RoBERTa, SentenceTransformer. `HuggingFaceEmbedding` is
  the abstract base, and `FastTextEmbedding` exists but is not registered.

## Available Models

### Chunking Models

| Class                          | Model names                            | File                                                                        |
| ------------------------------ | -------------------------------------- | --------------------------------------------------------------------------- |
| `CharacterChunkModel`          | — (fixed character count chunking)     | `DashAI/back/models/RAG/chunking_models/character_chunk_model.py`           |
| `RecursiveCharacterChunkModel` | — (recursive separator-based chunking) | `DashAI/back/models/RAG/chunking_models/recursive_character_chunk_model.py` |
| `TokenChunkModel`              | — (fixed token count chunking)         | `DashAI/back/models/RAG/chunking_models/token_chunk_model.py`               |

### Embedding Models

| Class                          | Model names                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | File                                                                        |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `BERTEmbedding`                | `google-bert/bert-base-cased`, `google-bert/bert-base-uncased`, `google-bert/bert-large-cased`, `google-bert/bert-large-uncased`, `google-bert/bert-base-multilingual-cased`, `google-bert/bert-base-multilingual-uncased` (6)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | `DashAI/back/models/RAG/embeddings/dense/bert_embedding.py`                 |
| `DistilBERTEmbedding`          | `distilbert/distilbert-base-cased`, `distilbert/distilbert-base-uncased`, `distilbert/distilbert-base-multilingual-cased`, `distilbert/distilbert-roberta-base` (4)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | `DashAI/back/models/RAG/embeddings/dense/distilbert_embedding.py`           |
| `E5Embedding`                  | `intfloat/e5-small-v2`, `intfloat/e5-large-v2`, `intfloat/multilingual-e5-large`, `intfloat/multilingual-e5-base`, `intfloat/multilingual-e5-small`, `intfloat/e5-mistral-7b-instruct` (6)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `DashAI/back/models/RAG/embeddings/dense/e5_embedding.py`                   |
| `InstructorEmbedding`          | `hkunlp/instructor-base`, `hkunlp/instructor-large`, `hkunlp/instructor-xl` (3)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | `DashAI/back/models/RAG/embeddings/dense/instructor_embedding.py`           |
| `LaBSEmbedding`                | `sentence-transformers/LaBSE` (1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | `DashAI/back/models/RAG/embeddings/dense/labse_embedding.py`                |
| `RoBERTaEmbedding`             | `FacebookAI/roberta-base`, `FacebookAI/roberta-large`, `FacebookAI/xlm-roberta-base`, `FacebookAI/xlm-roberta-large` (4)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | `DashAI/back/models/RAG/embeddings/dense/roberta_embedding.py`              |
| `SentenceTransformerEmbedding` | `microsoft/harrier-oss-v1-270m`, `microsoft/harrier-oss-v1-0.6b`, `microsoft/harrier-oss-v1-27b`, `Qwen/Qwen3-Embedding-0.6B`, `Qwen/Qwen3-Embedding-4B`, `Qwen/Qwen3-Embedding-8B`, `sentence-transformers/all-MiniLM-L6-v2`, `sentence-transformers/all-MiniLM-L12-v2`, `sentence-transformers/all-mpnet-base-v2`, `sentence-transformers/all-distilroberta-v1`, `sentence-transformers/multi-qa-mpnet-base-dot-v1`, `sentence-transformers/multi-qa-mpnet-base-cos-v1`, `sentence-transformers/multi-qa-distilbert-dot-v1`, `sentence-transformers/multi-qa-distilbert-cos-v1`, `sentence-transformers/multi-qa-MiniLM-L6-dot-v1`, `sentence-transformers/multi-qa-MiniLM-L6-cos-v1`, `sentence-transformers/msmarco-bert-base-dot-v5`, `sentence-transformers/msmarco-distilbert-dot-v5`, `sentence-transformers/msmarco-distilbert-base-tas-b`, `sentence-transformers/msmarco-distilbert-cos-v5`, `sentence-transformers/msmarco-MiniLM-L12-cos-v5`, `sentence-transformers/msmarco-MiniLM-L6-cos-v5`, `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`, `sentence-transformers/distiluse-base-multilingual-cased-v2`, `sentence-transformers/distiluse-base-multilingual-cased-v1`, `sentence-transformers/allenai-specter` (27) | `DashAI/back/models/RAG/embeddings/dense/sentence_transformer_embedding.py` |

### Retriever Models

| Class                                      | Model names                                                      | File                                                                                    |
| ------------------------------------------ | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `BM25Retriever`                            | — (BM25 algorithm)                                               | `DashAI/back/models/RAG/retrievers/sparse/bm25_retriever.py`                            |
| `TFIDFRetriever`                           | — (TF-IDF algorithm)                                             | `DashAI/back/models/RAG/retrievers/sparse/tfidf_retriever.py`                           |
| `DenseEmbeddingRetriever`                  | Uses any `DenseEmbedding` configured via `ComponentField`        | `DashAI/back/models/RAG/retrievers/dense/dense_embedding_retriever.py`                  |
| `MMRRerankerRetriever`                     | — (MMR reranker over nested retrievers)                          | `DashAI/back/models/RAG/retrievers/composite/mmr_reranker_retriever.py`                 |
| `SequentialRetriever`                      | — (executes retrievers sequentially)                             | `DashAI/back/models/RAG/retrievers/composite/sequential_retriever.py`                   |
| `ParallelRetriever`                        | — (executes retrievers in parallel and merges)                   | `DashAI/back/models/RAG/retrievers/composite/parallel_retriever.py`                     |
| `LLMEvaluatedDepthRetriever`               | — (LLM-judged adaptive depth over one child)                     | `DashAI/back/models/RAG/retrievers/composite/llm_evaluated_depth_retriever.py`          |
| `LLMEvaluatedEnsembleRetriever`            | — (LLM-chosen children across rounds)                            | `DashAI/back/models/RAG/retrievers/composite/llm_evaluated_ensemble_retriever.py`       |
| `SentenceTransformerCrossEncoderRetriever` | 17 cross-encoder models from `cross-encoder/*` (see table below) | `DashAI/back/models/RAG/retrievers/cross_encoder/sentence_transformer_cross_encoder.py` |

Both sparse retrievers take a nested vectorizer component
(`BM25VectorizerModel` / `TFIDFVectorizerModel`) selected in their params.

The two `LLMEvaluated*` retrievers ask their configured model for a structured
sufficiency verdict: the depth retriever evaluates after every round except the
final one, while the ensemble retriever also makes a planning call before the
first round. When the model supports function calling, the verdict is obtained
through `generate_function_call` using the retriever's function schema
(constrained by the backend); otherwise the prompt is answered as text and
parsed by the tolerant text parser. Both routes validate the same strict
contract, so an unparseable verdict always raises. The next-step field (`top_k`
for depth, `children` for ensemble) stays optional in the function schema; the
runtime validator requires it whenever `sufficient` is false. llama.cpp's GBNF
converter enforces `type`, `required` and `minItems` but not numeric `minimum`,
so the runtime validator remains the authoritative guard for `top_k >= 1` and
child indices `>= 0`.

### Model Type Classification

**Bi-encoders** encode queries and documents independently into dense vectors, then
compare via cosine or dot-product similarity. **Cross-encoders** process
query-document pairs jointly through a single transformer forward pass, producing a
relevance score directly — they are used as _re-rankers_ on top of a fast first-stage
retriever. **Sparse retrievers** (BM25, TF-IDF) use statistical frequency-based
scoring.

**Ranker vs. reranker configuration.** In a two-stage retrieval setup the
first-stage retriever (the _ranker_) decides how many candidates are
fetched — this is configured on the child retriever itself via its own
`top_k`. The re-ranker (e.g. `SentenceTransformerCrossEncoderRetriever`
or `MMRRerankerRetriever`) then re-scores those candidates and returns
the top `top_k` of them. Re-rankers expose `top_k` plus their own model
parameters (e.g. `model_name` for the SentenceTransformer cross-encoder);
they have no `retrieval_factor`.

| Model Name                                                    | Type                           | Reference                                                                            |
| ------------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------ |
| **BERT family**                                               |                                |                                                                                      |
| `google-bert/bert-base-cased`                                 | Bi-encoder                     | https://huggingface.co/google-bert/bert-base-cased                                   |
| `google-bert/bert-base-uncased`                               | Bi-encoder                     | https://huggingface.co/google-bert/bert-base-uncased                                 |
| `google-bert/bert-large-cased`                                | Bi-encoder                     | https://huggingface.co/google-bert/bert-large-cased                                  |
| `google-bert/bert-large-uncased`                              | Bi-encoder                     | https://huggingface.co/google-bert/bert-large-uncased                                |
| `google-bert/bert-base-multilingual-cased`                    | Bi-encoder                     | https://huggingface.co/google-bert/bert-base-multilingual-cased                      |
| `google-bert/bert-base-multilingual-uncased`                  | Bi-encoder                     | https://huggingface.co/google-bert/bert-base-multilingual-uncased                    |
| **DistilBERT family**                                         |                                |                                                                                      |
| `distilbert/distilbert-base-cased`                            | Bi-encoder                     | https://huggingface.co/distilbert/distilbert-base-cased                              |
| `distilbert/distilbert-base-uncased`                          | Bi-encoder                     | https://huggingface.co/distilbert/distilbert-base-uncased                            |
| `distilbert/distilbert-base-multilingual-cased`               | Bi-encoder                     | https://huggingface.co/distilbert/distilbert-base-multilingual-cased                 |
| `distilbert/distilbert-roberta-base`                          | Bi-encoder                     | https://huggingface.co/distilbert/distilbert-roberta-base                            |
| **RoBERTa family**                                            |                                |                                                                                      |
| `FacebookAI/roberta-base`                                     | Bi-encoder                     | https://huggingface.co/FacebookAI/roberta-base                                       |
| `FacebookAI/roberta-large`                                    | Bi-encoder                     | https://huggingface.co/FacebookAI/roberta-large                                      |
| `FacebookAI/xlm-roberta-base`                                 | Bi-encoder                     | https://huggingface.co/FacebookAI/xlm-roberta-base                                   |
| `FacebookAI/xlm-roberta-large`                                | Bi-encoder                     | https://huggingface.co/FacebookAI/xlm-roberta-large                                  |
| **E5 family**                                                 |                                |                                                                                      |
| `intfloat/e5-small-v2`                                        | Bi-encoder                     | https://huggingface.co/intfloat/e5-small-v2                                          |
| `intfloat/e5-large-v2`                                        | Bi-encoder                     | https://huggingface.co/intfloat/e5-large-v2                                          |
| `intfloat/multilingual-e5-large`                              | Bi-encoder                     | https://huggingface.co/intfloat/multilingual-e5-large                                |
| `intfloat/multilingual-e5-base`                               | Bi-encoder                     | https://huggingface.co/intfloat/multilingual-e5-base                                 |
| `intfloat/multilingual-e5-small`                              | Bi-encoder                     | https://huggingface.co/intfloat/multilingual-e5-small                                |
| `intfloat/e5-mistral-7b-instruct`                             | Bi-encoder (decoder-based)     | https://huggingface.co/intfloat/e5-mistral-7b-instruct                               |
| **Instructor family**                                         |                                |                                                                                      |
| `hkunlp/instructor-base`                                      | Bi-encoder (instruction-tuned) | https://huggingface.co/hkunlp/instructor-base                                        |
| `hkunlp/instructor-large`                                     | Bi-encoder (instruction-tuned) | https://huggingface.co/hkunlp/instructor-large                                       |
| `hkunlp/instructor-xl`                                        | Bi-encoder (instruction-tuned) | https://huggingface.co/hkunlp/instructor-xl                                          |
| **LaBSE**                                                     |                                |                                                                                      |
| `sentence-transformers/LaBSE`                                 | Bi-encoder                     | https://huggingface.co/sentence-transformers/LaBSE                                   |
| **Microsoft Harrier**                                         |                                |                                                                                      |
| `microsoft/harrier-oss-v1-270m`                               | Bi-encoder                     | https://huggingface.co/microsoft/harrier-oss-v1-270m                                 |
| `microsoft/harrier-oss-v1-0.6b`                               | Bi-encoder                     | https://huggingface.co/microsoft/harrier-oss-v1-0.6b                                 |
| `microsoft/harrier-oss-v1-27b`                                | Bi-encoder                     | https://huggingface.co/microsoft/harrier-oss-v1-27b                                  |
| **Qwen3 Embedding**                                           |                                |                                                                                      |
| `Qwen/Qwen3-Embedding-0.6B`                                   | Bi-encoder                     | https://huggingface.co/Qwen/Qwen3-Embedding-0.6B                                     |
| `Qwen/Qwen3-Embedding-4B`                                     | Bi-encoder                     | https://huggingface.co/Qwen/Qwen3-Embedding-4B                                       |
| `Qwen/Qwen3-Embedding-8B`                                     | Bi-encoder                     | https://huggingface.co/Qwen/Qwen3-Embedding-8B                                       |
| **Sentence-Transformers (general)**                           |                                |                                                                                      |
| `sentence-transformers/all-MiniLM-L6-v2`                      | Bi-encoder                     | https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2                        |
| `sentence-transformers/all-MiniLM-L12-v2`                     | Bi-encoder                     | https://huggingface.co/sentence-transformers/all-MiniLM-L12-v2                       |
| `sentence-transformers/all-mpnet-base-v2`                     | Bi-encoder                     | https://huggingface.co/sentence-transformers/all-mpnet-base-v2                       |
| `sentence-transformers/all-distilroberta-v1`                  | Bi-encoder                     | https://huggingface.co/sentence-transformers/all-distilroberta-v1                    |
| **Sentence-Transformers (multi-qa)**                          |                                |                                                                                      |
| `sentence-transformers/multi-qa-mpnet-base-dot-v1`            | Bi-encoder                     | https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-dot-v1              |
| `sentence-transformers/multi-qa-mpnet-base-cos-v1`            | Bi-encoder                     | https://huggingface.co/sentence-transformers/multi-qa-mpnet-base-cos-v1              |
| `sentence-transformers/multi-qa-distilbert-dot-v1`            | Bi-encoder                     | https://huggingface.co/sentence-transformers/multi-qa-distilbert-dot-v1              |
| `sentence-transformers/multi-qa-distilbert-cos-v1`            | Bi-encoder                     | https://huggingface.co/sentence-transformers/multi-qa-distilbert-cos-v1              |
| `sentence-transformers/multi-qa-MiniLM-L6-dot-v1`             | Bi-encoder                     | https://huggingface.co/sentence-transformers/multi-qa-MiniLM-L6-dot-v1               |
| `sentence-transformers/multi-qa-MiniLM-L6-cos-v1`             | Bi-encoder                     | https://huggingface.co/sentence-transformers/multi-qa-MiniLM-L6-cos-v1               |
| **Sentence-Transformers (MS MARCO)**                          |                                |                                                                                      |
| `sentence-transformers/msmarco-bert-base-dot-v5`              | Bi-encoder                     | https://huggingface.co/sentence-transformers/msmarco-bert-base-dot-v5                |
| `sentence-transformers/msmarco-distilbert-dot-v5`             | Bi-encoder                     | https://huggingface.co/sentence-transformers/msmarco-distilbert-dot-v5               |
| `sentence-transformers/msmarco-distilbert-base-tas-b`         | Bi-encoder                     | https://huggingface.co/sentence-transformers/msmarco-distilbert-base-tas-b           |
| `sentence-transformers/msmarco-distilbert-cos-v5`             | Bi-encoder                     | https://huggingface.co/sentence-transformers/msmarco-distilbert-cos-v5               |
| `sentence-transformers/msmarco-MiniLM-L12-cos-v5`             | Bi-encoder                     | https://huggingface.co/sentence-transformers/msmarco-MiniLM-L12-cos-v5               |
| `sentence-transformers/msmarco-MiniLM-L6-cos-v5`              | Bi-encoder                     | https://huggingface.co/sentence-transformers/msmarco-MiniLM-L6-cos-v5                |
| **Sentence-Transformers (multilingual)**                      |                                |                                                                                      |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Bi-encoder                     | https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2   |
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | Bi-encoder                     | https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2   |
| `sentence-transformers/distiluse-base-multilingual-cased-v2`  | Bi-encoder                     | https://huggingface.co/sentence-transformers/distiluse-base-multilingual-cased-v2    |
| `sentence-transformers/distiluse-base-multilingual-cased-v1`  | Bi-encoder                     | https://huggingface.co/sentence-transformers/distiluse-base-multilingual-cased-v1    |
| **Sentence-Transformers (other)**                             |                                |                                                                                      |
| `sentence-transformers/allenai-specter`                       | Bi-encoder                     | https://huggingface.co/sentence-transformers/allenai-specter                         |
| **FastText (exists but not registered)**                      |                                |                                                                                      |
| `facebook/fasttext-en-vectors`                                | Static embedding               | https://huggingface.co/facebook/fasttext-en-vectors                                  |
| `facebook/fasttext-es-vectors`                                | Static embedding               | https://huggingface.co/facebook/fasttext-es-vectors                                  |
| **SentenceTransformers Cross-Encoders (re-rankers)**          |                                |                                                                                      |
| `cross-encoder/ms-marco-MiniLM-L-6-v2`                        | Cross-encoder                  | https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2                          |
| `cross-encoder/ms-marco-MiniLM-L-12-v2`                       | Cross-encoder                  | https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-12-v2                         |
| `cross-encoder/ms-marco-MiniLM-L-4-v2`                        | Cross-encoder                  | https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-4-v2                          |
| `cross-encoder/ms-marco-TinyBERT-L-2-v2`                      | Cross-encoder                  | https://huggingface.co/cross-encoder/ms-marco-TinyBERT-L-2-v2                        |
| `cross-encoder/ms-marco-electra-base`                         | Cross-encoder                  | https://huggingface.co/cross-encoder/ms-marco-electra-base                           |
| `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`                  | Cross-encoder (multilingual)   | https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1                    |
| `cross-encoder/stsb-roberta-base`                             | Cross-encoder                  | https://huggingface.co/cross-encoder/stsb-roberta-base                               |
| `cross-encoder/stsb-distilroberta-base`                       | Cross-encoder                  | https://huggingface.co/cross-encoder/stsb-distilroberta-base                         |
| `cross-encoder/stsb-TinyBERT-L-4`                             | Cross-encoder                  | https://huggingface.co/cross-encoder/stsb-TinyBERT-L-4                               |
| `cross-encoder/stsb-roberta-large`                            | Cross-encoder                  | https://huggingface.co/cross-encoder/stsb-roberta-large                              |
| `cross-encoder/quora-distilroberta-base`                      | Cross-encoder                  | https://huggingface.co/cross-encoder/quora-distilroberta-base                        |
| `cross-encoder/quora-roberta-base`                            | Cross-encoder                  | https://huggingface.co/cross-encoder/quora-roberta-base                              |
| `cross-encoder/nli-distilroberta-base`                        | Cross-encoder                  | https://huggingface.co/cross-encoder/nli-distilroberta-base                          |
| `cross-encoder/nli-roberta-base`                              | Cross-encoder                  | https://huggingface.co/cross-encoder/nli-roberta-base                                |
| `cross-encoder/nli-deberta-v3-base`                           | Cross-encoder                  | https://huggingface.co/cross-encoder/nli-deberta-v3-base                             |
| `cross-encoder/nli-MiniLM2-L6-H768`                           | Cross-encoder                  | https://huggingface.co/cross-encoder/nli-MiniLM2-L6-H768                             |
| `cross-encoder/nli-deberta-v3-xsmall`                         | Cross-encoder                  | https://huggingface.co/cross-encoder/nli-deberta-v3-xsmall                           |
| `SentenceTransformerCrossEncoderRetriever`                    | Re-ranker (composite)          | Uses any cross-encoder model above + a child retriever                               |
| **Sparse Retrievers**                                         |                                |                                                                                      |
| `BM25Retriever`                                               | Statistical (sparse)           | https://en.wikipedia.org/wiki/Okapi_BM25                                             |
| `TFIDFRetriever`                                              | Statistical (sparse)           | https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting |
| **Composite Retrievers**                                      |                                |                                                                                      |
| `MMRRerankerRetriever`                                        | Re-ranker (composite)          | https://en.wikipedia.org/wiki/Maximal_marginal_relevance                             |
| `SequentialRetriever`                                         | Pipeline (composite)           | —                                                                                    |
| `ParallelRetriever`                                           | Ensemble (composite)           | —                                                                                    |
| `LLMEvaluatedDepthRetriever`                                  | Adaptive depth (composite)     | Uses any `TextToTextGenerationTaskModel` from above                                  |
| `LLMEvaluatedEnsembleRetriever`                               | Adaptive ensemble (composite)  | Uses any `TextToTextGenerationTaskModel` from above                                  |
| **Dense Retriever**                                           |                                |                                                                                      |
| `DenseEmbeddingRetriever`                                     | Bi-encoder + search index      | Uses any `DenseEmbedding` from above                                                 |

### Query Transformation Models

| Class                | Technique / parameters                                                             | File                                                     |
| -------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `LLMQueryRewriter`   | rewriting (always one query); `prompt`, `llm_model`, `history_window` (default 2)  | `DashAI/back/models/RAG/transformation/rewriting.py`     |
| `LLMQueryExpander`   | expansion (up to `n_queries`, default 3); `prompt`, `llm_model`, `history_window`  | `DashAI/back/models/RAG/transformation/expansion.py`     |
| `LLMQueryDecomposer` | decomposition (`max_subqueries` optional); `prompt`, `llm_model`, `history_window` | `DashAI/back/models/RAG/transformation/decomposition.py` |

All three share the base schema (`prompt`, `llm_model`, `history_window`);
expansion adds `n_queries` and decomposition adds `max_subqueries`. They
route through function calling when the configured model supports it, otherwise
through a tolerant text parser. The base contract
(`BaseQueryTransformation.transform(message, history)`) lives in
`DashAI/back/models/RAG/transformation/base_query_transformation.py` and the
shared LLM implementation in `.../llm_query_transformation.py`.

### Query Transformation Prompts

| Class                             | Technique / placeholders                                                          | File                                                                                  |
| --------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `QueryTransformationPrompt`       | base contract; required `{input}`, `{history}`                                    | `DashAI/back/models/RAG/prompts/transformation/transformation_prompt.py`              |
| `QueryRewritingPrompt`            | rewriting anchor; required `{input}`, `{history}`                                 | `DashAI/back/models/RAG/prompts/transformation/transformation_prompt.py`              |
| `QueryExpansionPrompt`            | expansion anchor; required `{input}`, `{history}`, `{n}`                          | `DashAI/back/models/RAG/prompts/transformation/transformation_prompt.py`              |
| `QueryDecompositionPrompt`        | decomposition anchor; required `{input}`, `{history}`, optional `{n_max}`         | `DashAI/back/models/RAG/prompts/transformation/transformation_prompt.py`              |
| `DefaultQueryRewritingPrompt`     | rewriting default (en/es/pt); required `{input}`, `{history}`                     | `DashAI/back/models/RAG/prompts/transformation/default_query_rewriting_prompt.py`     |
| `CustomQueryRewritingPrompt`      | rewriting custom; required `{input}`, `{history}`                                 | `DashAI/back/models/RAG/prompts/transformation/custom_query_rewriting_prompt.py`      |
| `DefaultQueryExpansionPrompt`     | expansion default (en/es/pt); required `{input}`, `{history}`, `{n}`              | `DashAI/back/models/RAG/prompts/transformation/default_query_expansion_prompt.py`     |
| `CustomQueryExpansionPrompt`      | expansion custom; required `{input}`, `{history}`, `{n}`                          | `DashAI/back/models/RAG/prompts/transformation/custom_query_expansion_prompt.py`      |
| `DefaultQueryDecompositionPrompt` | decomposition default (en/es/pt); required `{input}`, `{history}`, opt. `{n_max}` | `DashAI/back/models/RAG/prompts/transformation/default_query_decomposition_prompt.py` |
| `CustomQueryDecompositionPrompt`  | decomposition custom; required `{input}`, `{history}`, optional `{n_max}`         | `DashAI/back/models/RAG/prompts/transformation/custom_query_decomposition_prompt.py`  |

### Generation Prompts

| Class                          | Placeholders                                                        | File                                                                            |
| ------------------------------ | ------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `RAGGenerationPrompt`          | base contract; required `{input}`, `{chunks}`, optional `{queries}` | `DashAI/back/models/RAG/prompts/generation/RAG_generation_prompt.py`            |
| `DefaultRAGGenerationPrompt`   | default (en/es/pt)                                                  | `DashAI/back/models/RAG/prompts/generation/default_RAG_generation_prompt.py`    |
| `CustomRAGGenerationPrompt`    | user-defined template                                               | `DashAI/back/models/RAG/prompts/generation/custom_RAG_generation_prompt.py`     |
| `DefaultQARAGGenerationPrompt` | QA variant (en/es/pt)                                               | `DashAI/back/models/RAG/prompts/generation/default_QA_RAG_generation_prompt.py` |

The optional `{queries}` placeholder is filled with the queries the retrieval
stage ran over (joined with `"; "`); when the transformation stage is disabled
its whole line is removed from the rendered prompt.

### LLM Models (Text-to-Text Generation)

All registered LLMs are GGUF checkpoints loaded through llama.cpp, with the
repo and quantization fixed per class (except `Phi4MiniInstructModel`, which
takes them as parameters):

| Class                      | Checkpoint (quantization)                                    | File                                                                         |
| -------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| `Llama31_8BInstruct`       | `bartowski/Meta-Llama-3.1-8B-Instruct-GGUF` (Q4_K_M)         | `DashAI/back/models/hugging_face/llama_model.py`                             |
| `Llama32_1BInstruct`       | `bartowski/Llama-3.2-1B-Instruct-GGUF` (Q4_K_M)              | `DashAI/back/models/hugging_face/llama_model.py`                             |
| `Llama32_3BInstruct`       | `bartowski/Llama-3.2-3B-Instruct-GGUF` (Q4_K_M)              | `DashAI/back/models/hugging_face/llama_model.py`                             |
| `Mistral7BInstructV03`     | `bartowski/Mistral-7B-Instruct-v0.3-GGUF` (Q4_K_M)           | `DashAI/back/models/hugging_face/mistral_model.py`                           |
| `MistralNemoInstruct2407`  | `bartowski/Mistral-Nemo-Instruct-2407-GGUF` (Q4_K_M)         | `DashAI/back/models/hugging_face/mistral_model.py`                           |
| `Mixtral8x7BInstructQ4KM`  | `mradermacher/Mixtral-8x7B-Instruct-v0.1-GGUF` (Q4_K_M)      | `DashAI/back/models/hugging_face/mixtral_model.py`                           |
| `Mixtral8x7BInstructQ2K`   | `mradermacher/Mixtral-8x7B-Instruct-v0.1-GGUF` (Q2_K)        | `DashAI/back/models/hugging_face/mixtral_model.py`                           |
| `Qwen25_05BInstruct`       | `Qwen/Qwen2.5-0.5B-Instruct-GGUF` (Q8_0)                     | `DashAI/back/models/hugging_face/qwen_model.py`                              |
| `Qwen25_15BInstruct`       | `Qwen/Qwen2.5-1.5B-Instruct-GGUF` (Q8_0)                     | `DashAI/back/models/hugging_face/qwen_model.py`                              |
| `SmolLM2_360MInstruct`     | `HuggingFaceTB/SmolLM2-360M-Instruct-GGUF` (q8_0)            | `DashAI/back/models/hugging_face/smol_lm_model.py`                           |
| `SmolLM2_17BInstruct`      | `HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF` (q4_k_m)          | `DashAI/back/models/hugging_face/smol_lm_model.py`                           |
| `Phi4MiniInstructModel`    | `unsloth/Phi-4-mini-instruct-GGUF` (Q8_0), both as parameters | `DashAI/back/models/hugging_face/phi_4_mini_instruct_model.py`               |

`DeepSeekModel` (`hugging_face/deep_seek_model.py`) exists but is not registered
in `get_initial_components()`, so it is not offered in the UI.
