# Future Work

This document outlines planned improvements and known gaps in the current RAG
implementation. These are not limitations per se, but rather opportunities for
expansion.

## Retrieval Paradigms

The current pipeline follows a straightforward sequential flow: chunk → retrieve → generate. It does not support more complex retrieval strategies such as:

- **Iterative retrieval** — alternating between retrieval and generation steps, using intermediate LLM outputs to refine subsequent queries.
- **Generate-then-retrieve** — generating a preliminary answer and using it to retrieve supporting evidence.
- **Corrective RAG** — evaluating retrieved chunks for relevance and triggering re-retrieval when no chunk is relevant.
- **HyDE (Hypothetical Document Embeddings)** — generating a hypothetical ideal document from the query and retrieving by its embedding rather than the raw query.

## Query Transformation

The pipeline currently passes the user's raw query directly to the retriever. No query transformation phase exists. Future work could add:

- **Query expansion** — expanding short queries with synonyms or related terms.
- **Query decomposition** — splitting a complex question into sub-queries routed to different retrievers.
- **Rewriting / compression** — rephrasing ambiguous queries or compressing long chat histories into a single standalone query.

## PDF Parsing

The extractor system is implemented and documented in
[`06-document-processing.md`](./06-document-processing.md). Remaining parsing
work:

- OCR for scanned PDFs (`EasyOCRExtractor` exists but needs heavy dependencies).
- Table extraction and layout-aware parsing.
- LLM-based preprocessing for structured extraction (tables, headers, figures).
- Extractor recommendation based on document characteristics.

## Documents library

Currently, the `Documents` library is a simple table of documents, with a column
for metadata that is not used. Future work could include:

- Metadata-based filtering: allowing users to filter documents by metadata fields (e.g., author, date, tags).
- Document versioning: supporting multiple versions of the same document and allowing retrieval from a specific version.
- Document similarity search: enabling users to find documents similar to a given document based on content or metadata.
- Import/export functionality: allowing users to import/export documents and their metadata in various formats (e.g., JSON, CSV, XML), including support for BibTeX and Mendeley references.

## Tree-Based Retrieval

Only flat (sparse + dense) and composite (sequential / parallel / MMR /
cross-encoder) retrievers are implemented. Cross-encoder re-rankers
(`SentenceTransformerCrossEncoderRetriever` with 17 SBERT models) act as
second-stage re-rankers over a child ranker. There is no tree-based indexing
or hierarchical retrieval.

## Document Subset Filtering at Message Level

When chatting, the user might want a given response to use only a specific subset of their uploaded documents (e.g., "use only the documents I referenced in my previous message"). Currently the retriever always searches across all documents assigned to the session. A document-level filter per message would enable more fine-grained control.

## FastTextEmbedding Registration

`FastTextEmbedding` exists in the codebase at
`models/RAG/embeddings/dense/fasttext_embedding.py` but is not exposed through
the `embeddings/dense/__init__.py` public API. It needs to be added to
`__all__` and registered in `get_initial_components()`.

## Frontend Setup Refactor

The `components/generative/RAG/setup/` directory contains empty `sections/`,
`components/`, and `advanced/` subdirectories. These are placeholders for a
planned refactor that would move setup-related components out of
`pages/generative/RAGSession/` into reusable modules under `components/`.

## Multi-Modal Document Support

Currently only text-based documents are supported (txt, pdf, md, rst, tex, csv). A major challenge is extending the pipeline to handle other modalities:

- **Graph documents** — knowledge graphs, property graphs, RDF data.
- **Datasets** — structured tabular data as found in the rest of DashAI (e.g., CSV datasets used for ML training).
- **Images** — both extracting text from images (OCR) and, more ambitiously, retrieving chunks based on visual similarity.
- **Audio / video** — transcription and retrieval from spoken content.
