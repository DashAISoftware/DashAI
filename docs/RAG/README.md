# RAG Module Documentation

DashAI includes a **Retrieval-Augmented Generation (RAG)** module for chatting
with your documents. The pipeline has four stages — Document Loading, Chunking,
Retrieval, and Generation — plus an optional pre-retrieval query transformation
stage (rewriting, expansion, or decomposition).

## Documentation Index

- **[01-overview.md](./01-overview.md)** — High-level overview, architecture
  diagram, pipeline stages, component types, component catalog, and code
  location.
- **[02-backend-architecture.md](./02-backend-architecture.md)** — Detailed
  backend architecture: pipeline orchestration, factory pattern, retriever
  hierarchy, persistence, typed return values.
- **[03-frontend-architecture.md](./03-frontend-architecture.md)** — Frontend
  routes, component tree, API endpoints, and key features.
- **[04-execution-flow.md](./04-execution-flow.md)** — End-to-end execution
  flow: session creation → job dispatch → pipeline construction → generation
  → frontend polling.
- **[05-known-limitations.md](./05-known-limitations.md)** — Current
  constraints, performance notes, concurrency caveats, and maintenance
  guidance.
- **[06-document-processing.md](./06-document-processing.md)** — How documents
  are processed: document data loaders, storage, upload and parsing, the RAG
  loading stage, session attach/detach, API endpoints, and the frontend
  document manager.
- **[07-future-work.md](./07-future-work.md)** — Planned improvements:
  retrieval paradigms, PDF parsing, tree-based retrieval, message-level
  document filtering, and multi-modal support.
