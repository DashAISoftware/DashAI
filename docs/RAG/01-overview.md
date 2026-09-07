| Utilities | `DashAI/back/models/RAG/utils.py` |
| Exceptions | `DashAI/back/models/RAG/exceptions/` |
| Retrievers | `DashAI/back/models/RAG/retrievers/` (subdirs: `dense/`, `sparse/`, `composite/`) |
| Chunking | `DashAI/back/models/RAG/chunking_models/` |
| Prompts | `DashAI/back/models/RAG/prompts/` (subdirs: `generation/`, `augmentation/`) |
| Documents | `DashAI/back/models/RAG/documents/` |
| Embeddings | `DashAI/back/models/RAG/embeddings/` (subdirs: `dense/`, `sparse/`) |
| Jobs | `DashAI/back/job/RAG_job.py` |
| Task | `DashAI/back/tasks/RAG_task.py` |
| Core | `DashAI/back/core/component_validation.py` |
| Frontend | `DashAI/front/src/pages/generative/RAGSession/` |
| Frontend components | `DashAI/front/src/components/generative/RAG/` |

## Quick Architecture

```
Browser / PyWebView
  → React (port 3000)
    → POST /api/v1/generative-session/   (create session)
      → Validate payload, components, documents, prompt
    → POST /api/v1/generative-process/   (create process)
    → POST /api/v1/job/                  (enqueue job)
      → Huey Job Queue
        → RAGJob.run()
          → RAGSetupService.build_pipeline()
            → DocumentService → ChunkingService → RetrieverSetupService → LLMService
            → RAGPipeline.generate()
          → RAGTask.process_output() (serialize)
        → Frontend polls GET /api/v1/jobs/{id}
```

## Component Types

- **Chunking models** — Character, Token, Recursive character (all implement
  `BaseChunkingModel`)
- **Retrievers** — `RetrieverModel` base; Sparse (TF-IDF, BM25), Dense (via
  `DenseEmbedding` subclasses), Cross-Encoder (SentenceTransformer re-rankers),
  Composite (Sequential, Parallel, MMR Reranker)
- **Prompts** — Generation prompts (Default, Custom, QA) in en/es/pt +
  augmentation prompts (Default, Custom) for future query expansion
- **LLMs** — Any `TextToTextGenerationTaskModel` registered in the component
  registry (OpenAI-compatible APIs, HuggingFace models)
- **Embeddings** — `DenseEmbedding` subclasses: BERT, DistilBERT, E5, Gemma,
  HuggingFace, Instructor, LaBSE, OpenAI, RoBERTa, SentenceTransformer,
  FastText

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
| `GemmaEmbedding`               | `google/embeddinggemma-300m` (1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | `DashAI/back/models/RAG/embeddings/dense/gemma_embedding.py`                |
| `InstructorEmbedding`          | `hkunlp/instructor-base`, `hkunlp/instructor-large`, `hkunlp/instructor-xl` (3)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | `DashAI/back/models/RAG/embeddings/dense/instructor_embedding.py`           |
| `LaBSEmbedding`                | `sentence-transformers/LaBSE` (1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | `DashAI/back/models/RAG/embeddings/dense/labse_embedding.py`                |
| `OpenAIEmbedding`              | `text-embedding-ada-002`, `text-embedding-3-small`, `text-embedding-3-large` (3)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | `DashAI/back/models/RAG/embeddings/dense/openai_embedding.py`               |
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
| `SentenceTransformerCrossEncoderRetriever` | 17 cross-encoder models from `cross-encoder/*` (see table below) | `DashAI/back/models/RAG/retrievers/cross_encoder/sentence_transformer_cross_encoder.py` |

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
| **Gemma Embedding**                                           |                                |                                                                                      |
| `google/embeddinggemma-300m`                                  | Bi-encoder                     | https://huggingface.co/google/embeddinggemma-300m                                    |
| **Instructor family**                                         |                                |                                                                                      |
| `hkunlp/instructor-base`                                      | Bi-encoder (instruction-tuned) | https://huggingface.co/hkunlp/instructor-base                                        |
| `hkunlp/instructor-large`                                     | Bi-encoder (instruction-tuned) | https://huggingface.co/hkunlp/instructor-large                                       |
| `hkunlp/instructor-xl`                                        | Bi-encoder (instruction-tuned) | https://huggingface.co/hkunlp/instructor-xl                                          |
| **LaBSE**                                                     |                                |                                                                                      |
| `sentence-transformers/LaBSE`                                 | Bi-encoder                     | https://huggingface.co/sentence-transformers/LaBSE                                   |
| **OpenAI Embeddings**                                         |                                |                                                                                      |
| `text-embedding-ada-002`                                      | Bi-encoder (API)               | https://platform.openai.com/docs/guides/embeddings                                   |
| `text-embedding-3-small`                                      | Bi-encoder (API)               | https://platform.openai.com/docs/guides/embeddings                                   |
| `text-embedding-3-large`                                      | Bi-encoder (API)               | https://platform.openai.com/docs/guides/embeddings                                   |
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
| **FastText (not registered in UI)**                           |                                |                                                                                      |
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
| **Dense Retriever**                                           |                                |                                                                                      |
| `DenseEmbeddingRetriever`                                     | Bi-encoder + search index      | Uses any `DenseEmbedding` from above                                                 |

### LLM Models (Text-to-Text Generation)

| Class                               | Model names                                                  | File                                                                         |
| ----------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| `LlamaModel`                        | — (e.g. `meta-llama/Llama-3.2-3B-Instruct` via llama.cpp)    | `DashAI/back/models/hugging_face/llama_model.py`                             |
| `MistralModel`                      | — (e.g. `mistralai/Mistral-7B-Instruct` via llama.cpp)       | `DashAI/back/models/hugging_face/mistral_model.py`                           |
| `MixtralModel`                      | — (e.g. `mistralai/Mixtral-8x7B-Instruct` via llama.cpp)     | `DashAI/back/models/hugging_face/mixtral_model.py`                           |
| `QwenModel`                         | — (e.g. `Qwen/Qwen2.5-7B-Instruct` via llama.cpp)            | `DashAI/back/models/hugging_face/qwen_model.py`                              |
| `SmolLMModel`                       | — (e.g. `HuggingFaceTB/SmolLM2-1.7B-Instruct` via llama.cpp) | `DashAI/back/models/hugging_face/smol_lm_model.py`                           |
| `Phi4MiniInstructModel`             | — (e.g. `microsoft/Phi-4-mini-instruct` via llama.cpp)       | `DashAI/back/models/hugging_face/phi_4_mini_instruct_model.py`               |
| `DeepSeekTextToTextGenerationModel` | — (OpenAI-compatible API, e.g. `deepseek-chat`)              | `DashAI/back/models/remote_models/deepseek_text_to_text_generation_model.py` |
| `OpenAITextToTextGenerationModel`   | — (OpenAI API, e.g. `gpt-4o`, `gpt-4o-mini`)                 | `DashAI/back/models/remote_models/openai_text_to_text_generation_model.py`   |
