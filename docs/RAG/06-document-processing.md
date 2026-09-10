# Document Processing

This document describes how documents are uploaded, stored, and converted to
text in the RAG module — the _Document Loading_ stage of the pipeline. It covers
supported file types, the extractor system, the storage model, extraction
caching, invalidation, the REST API, and the frontend document manager.

## Supported File Types

`DocumentFileType` (`models/RAG/documents/file_type.py`) is the single source of
truth for file-type strings, shared across models, services, and the API:

| Enum member | Extension |
| ----------- | --------- |
| `TXT`       | `txt`     |
| `PDF`       | `pdf`     |
| `MD`        | `md`      |
| `RST`       | `rst`     |
| `TEX`       | `tex`     |
| `CSV`       | `csv`     |

At hydration time (`DocumentService.load()`) each file type maps to a document
class: `PDF` → `PDFDocument`, everything else → `TxtDocument` (read as plain
text). CSV files are therefore treated as free text, not structured data — a
known limitation (see [`05-known-limitations.md`](./05-known-limitations.md)).

## Extractors

Extractors are `ConfigObject` components that subclass `BaseExtractor`
(`models/RAG/extractors/base_extractor.py`). Each extractor declares:

- `TYPE = "Extractor"` — registry category.
- `SCHEMA` — a `BaseSchema` of parameters rendered as a form on the frontend.
- `SUPPORTED_FILE_TYPES` — the file types it can process.
- `extract(file_path: str) -> str` — the actual text extraction.

Four concrete extractors are registered in `get_initial_components()`:

| Extractor            | File types             | Library            | Parameters                             |
| -------------------- | ---------------------- | ------------------ | -------------------------------------- |
| `PlainTextExtractor` | txt, md, rst, tex, csv | stdlib (`open`)    | `encoding` (default `utf-8`)           |
| `PypdfExtractor`     | pdf                    | `pypdf`            | `strict` (default `True`)              |
| `PyMuPDFExtractor`   | pdf                    | `fitz` (pymupdf)   | `password` (default `""`)              |
| `EasyOCRExtractor`   | pdf                    | `easyocr` + `fitz` | `languages` (`["en"]`), `gpu` (`True`) |

`BaseExtractor.get_metadata()` exposes `supported_file_types`, which the
frontend uses to filter the extractor selector per document type.

## Default Extractor Resolution

`DocumentService._DEFAULT_EXTRACTORS` maps a file type to a default extractor:

| File type                | Default extractor    |
| ------------------------ | -------------------- |
| `pdf`                    | `PyMuPDFExtractor`   |
| `txt, md, rst, tex, csv` | `PlainTextExtractor` |

The default is used when a document has no explicit extractor record. On upload
the default extractor is materialized as a `rag_extractor` row, so the
`extractor_id` on `document` is always set.

## Storage Model

- **`rag_extractor`** — canonical extractor configuration: `id`,
  `component_name` (NOT NULL), `params` (JSON, nullable). Multiple documents can
  reference the same configuration via a foreign key.
- **`document.extractor_id`** — FK → `rag_extractor.id`, NOT NULL, with
  `ondelete=RESTRICT`. Assigned at upload, never ambiguous.
- **`processed_document_content`** — a 1:1 cache of extracted text (one row per
  document, enforced by a unique constraint on `document_id`): `content`,
  `signature`, `char_count`.

## Upload

`DocumentService.upload()`:

1. Computes a SHA-256 content hash of the file bytes (`hash_function`).
2. Deduplicates by hash:
   - Duplicate and `force=False` → returns the existing document plus its
     related sessions (the endpoint surfaces this as `409 Conflict`).
   - `force=True` → overwrites the file, invalidates RAG artifacts, and
     re-extracts.
3. Writes the file to the configured `DOCUMENTS_PATH`.
4. Creates the default `rag_extractor` record for the file type and assigns it.
5. Commits, then pre-extracts (warms the cache) when a component registry is
   available. Extraction failures are raised as `RAGDocumentExtractionError`.

## Text Extraction & Caching

`DocumentService.extract_text()` implements on-demand extraction with a 1:1
cache:

1. Resolves the extractor: explicit `{component, params}` ref → stored record →
   file-type default.
2. Validates `SUPPORTED_FILE_TYPES` compatibility; incompatible extractors raise
   an error.
3. Builds a cache signature:
   `SHA-256("{file_hash}:{component_name}:{json.dumps(params, sort_keys=True)}")`.
4. `persist=False` (preview mode) → extracts without persisting or invalidating.
5. Cache hit (matching signature) → returns the stored text with `cached=True`.
6. Cache miss → extracts, then overwrites the single row in place (or creates
   it). When the content changes because a different extractor/params produced a
   new signature, RAG artifacts of the related sessions are invalidated.

## Changing the Extractor

`DocumentService.update_extractor()`:

1. Validates the extractor exists in the registry and is compatible with the
   document's file type.
2. If the document is linked to RAG pipelines and `force=False`, refuses and
   reports the affected sessions (the endpoint surfaces this as `409 Conflict`).
3. Creates a new `rag_extractor` record, reassigns `extractor_id`, and — with
   `force=True` — invalidates artifacts.
4. Re-extracts with the new extractor to keep the 1:1 `processed_document_content`
   invariant.

## Invalidation

Changing an extractor (or force re-uploading a document) calls
`CleanupService.invalidate_document_artifacts(document_id)`, which deletes the
document's chunks, retrievers, embedding matrices, and related disk artifacts.
Nothing is eagerly recomputed — the next pipeline run for an affected session
re-chunks and rebuilds retrieval automatically.

## API

All endpoints live in `DashAI/back/api/api_v1/endpoints/documents.py` under the
`/api/v1/document` prefix:

| Method | Path                                     | Purpose                                        |
| ------ | ---------------------------------------- | ---------------------------------------------- |
| GET    | `/api/v1/document/`                      | List all documents                             |
| POST   | `/api/v1/document/`                      | Upload (multipart file + metadata JSON)        |
| GET    | `/api/v1/document/{id}`                  | Document metadata                              |
| GET    | `/api/v1/document/{id}/download`         | Download the file                              |
| GET    | `/api/v1/document/{id}/view`             | Inline preview                                 |
| GET    | `/api/v1/document/session/{session_id}`  | Documents of a RAG session                     |
| GET    | `/api/v1/document/related-sessions/{id}` | Session IDs linked to a document               |
| DELETE | `/api/v1/document/{id}`                  | Delete document + file                         |
| PUT    | `/api/v1/document/{id}`                  | Update metadata                                |
| POST   | `/api/v1/document/{id}/extract`          | On-demand extraction (`extractor`, `persist`)  |
| PUT    | `/api/v1/document/{id}/extractor`        | Commit extractor choice (`extractor`, `force`) |

## Frontend

The document manager lives under `components/generative/RAG/`:

- `RAGDocumentsPage` — document library page with `DocumentTable` and a detail
  panel.
- `DocumentDetailPanel` — document info, an extractor selector filtered by
  `supported_file_types`, and on-demand content display.
- `DocumentExtractorModal` — schema-driven extractor configuration.
- `DocumentPreviewModal` — inline preview.
- `DuplicateDocumentDialog` — confirmation when re-uploading an existing file.
- `DocumentSelector`, `DocumentList`, `DocumentListItem`, `DocumentsBar`,
  `RAGDocumentsPanel` — selection and list UIs for session setup.

The API client (`api/rag.ts`) exposes `getExtractorOptions()`,
`extractDocumentText()`, and `updateDocumentExtractor()`.

## Related Docs

- [`01-overview.md`](./01-overview.md) — module overview and component types.
- [`02-backend-architecture.md`](./02-backend-architecture.md) — service layer,
  chunking, and pipeline architecture.
- [`05-known-limitations.md`](./05-known-limitations.md) — extractor caveats and
  performance notes.
