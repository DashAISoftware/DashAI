# Document Processing

This document describes how documents are uploaded, stored, and converted to
text in the RAG module — the _Document Loading_ stage of the pipeline. It covers
supported file types, the extractor system, the storage model, extraction
caching, invalidation, the REST API, and the frontend document manager.

## Ownership

**A document belongs to exactly one RAG session.** `document.session_id` is a
NOT NULL foreign key to `generative_session`, and `UNIQUE(session_id,
file_hash)` replaces what used to be a global `UNIQUE(file_hash)`. Uploading the
same file into two sessions therefore creates two documents, each free to pick
its own extractor without disturbing the other.

Documents used to be a global library, with membership expressed by the JSON
list `GenerativeSession.parameters["documents"]`. That list is still what the
pipeline, the chunk-set signature and the parameter history read, so it is kept
in step with the foreign key — but only by the document endpoints. Clients
cannot set it: session creation always starts empty, and both
`POST /generative-session/` and `PUT /generative-session/{id}/parameters`
reject the key rather than silently dropping it.

Two consequences worth knowing:

- **Chunk sets are no longer shared between sessions.** `RAGChunkSet.signature`
  hashes the document ids, which now always differ, so two sessions with
  identical configurations each chunk and fit their own retriever. That costs
  CPU and disk in exchange for isolation.
- **Deleting a session deletes its documents**, their files and their fitted
  artifacts. SQLite foreign keys are not enforced in this application (there is
  no `PRAGMA foreign_keys=ON`), so this comes from the ORM cascade on
  `GenerativeSession.documents` plus `DocumentService.delete_by_session`, not
  from the `ondelete` clauses.

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

- **`document.session_id`** — FK → `generative_session.id`, NOT NULL. The owning
  session, unique together with `file_hash`.
- **`rag_extractor`** — canonical extractor configuration: `id`,
  `component_name` (NOT NULL), `params` (JSON). Rows are immutable value objects
  and are reused: `_get_or_create_extractor_row` looks one up by
  `(component_name, params)` before inserting, and an unreferenced row is
  dropped once the last document stops pointing at it.
- **`document.extractor_id`** — FK → `rag_extractor.id`, NOT NULL. Assigned at
  upload, never ambiguous.
- **`processed_document_content`** — a 1:1 cache of extracted text (one row per
  document, enforced by a unique constraint on `document_id`): `content`,
  `signature`, `char_count`.

### Files on disk

Files are stored **content-addressed** at
`<DOCUMENTS_PATH>/blobs/<file_hash>`. Naming them after `file_name` alone meant
two different files called `report.pdf` hashed differently — so both got a
document row — but resolved to the same path, and the second upload overwrote
the first one's bytes. Per-session copies would have made that collision
routine.

One consequence: sessions holding identical files share one file on disk, so
deletion is reference-counted. `DocumentService._unlink_if_unreferenced` removes
the blob only when no other row points at it. Documents migrated from the old
global library may also share a path, which is the other reason the guard is
required.

## Upload

`DocumentService.upload(..., session_id)`:

1. Validates that the session exists and is a RAG session, before writing
   anything.
2. Computes a SHA-256 content hash of the file bytes (`hash_function`).
3. Deduplicates **within the session**: the same bytes already present is
   reported as a duplicate (the endpoint surfaces `409 Conflict`) and nothing is
   modified. The same bytes in another session is a new document.
4. Writes the blob, if it is not already there.
5. Reuses or creates the default `rag_extractor` record for the file type.
6. Appends the new id to the session's `documents` list, with a parameter
   history entry, in the same transaction as the insert.
7. Commits, then pre-extracts (warms the cache) when a component registry is
   available. Extraction failures are raised as `RAGDocumentExtractionError`.

## Text Extraction & Caching

`DocumentService.extract_text()` implements on-demand extraction with a 1:1
cache:

1. Resolves the extractor **and how it is configured** in one place,
   `_resolve_extractor_ref`: explicit `{component, params}` ref → stored record →
   file-type default. Deriving the two separately is what made the signature
   disagree with itself (see below).
2. Validates `SUPPORTED_FILE_TYPES` compatibility; incompatible extractors raise
   an error.
3. Builds a cache signature:
   `SHA-256("{file_hash}:{component_name}:{json.dumps(params, sort_keys=True)}")`.
4. `persist=False` (preview mode) → extracts without persisting or invalidating.
5. Cache hit (matching signature) → returns the stored text with `cached=True`.
6. Cache miss → extracts, then overwrites the single row in place (or creates
   it). When an existing row is replaced, the artifacts fitted over the old text
   are invalidated. A *first* extraction invalidates nothing, because chunking
   needs extracted text and so there is nothing to invalidate yet.

> **Fixed:** the signature used to be built from empty params while the
> extractor was instantiated with the stored ones, so for any non-default
> configuration it never matched itself. Every empty-body `POST /extract` was a
> cache miss *and* destroyed the chunk set — a preview silently un-indexed the
> session.

## Changing the Extractor

`DocumentService.update_extractor()` is one transaction, and the extraction runs
before anything is mutated:

1. Validates the extractor exists in the registry and is compatible with the
   document's file type.
2. Returns early when nothing changed — the same component, the same params and
   a matching cache signature. With invalidation now unconditional, saving an
   unchanged choice would otherwise throw away a perfectly good index.
3. Extracts the text. This can fail, and nothing has been touched yet.
4. Reuses or creates the `rag_extractor` record, reassigns `extractor_id`,
   invalidates artifacts, writes the new content, and drops the previous
   extractor record if it is now unreferenced — then commits **once**.

There is no `force` parameter. It existed to make the user confirm a destructive
re-index, but it asked `RAGDocumentPipelineSessionLink` which sessions were
affected — a table nothing ever wrote to — so the confirmation was unreachable
and the invalidation it guarded never ran. A document now belongs to one
session, so there is nobody else to warn.

Committing the reassignment first was also how a failed extraction left a
document pointing at an extractor that had never produced its text, still
serving the previous extractor's chunks. A failure now returns `422` and changes
nothing.

## Invalidation

Changing an extractor, or deleting a document or its session, calls
`CleanupService.invalidate_document_artifacts(document_id)`, which deletes the
document's chunks, retrievers, embedding matrices, and related disk artifacts.
Nothing is eagerly recomputed — the next pipeline run re-chunks and rebuilds
retrieval automatically.

The method takes two flags so a caller can make it part of a larger unit of
work: `commit=False` hands the transaction back, and `defer_paths` collects the
on-disk paths instead of removing them, since `rmtree` cannot be rolled back.
The caller deletes them after its commit succeeds.

Note that it deletes the **whole chunk set**, including the chunks of sibling
documents in it. With documents owned by one session, a chunk set is too, so
re-chunking the set is exactly what has to happen.

## API

All endpoints live in `DashAI/back/api/api_v1/endpoints/documents.py` under the
`/api/v1/document` prefix:

| Method | Path                                          | Purpose                                       |
| ------ | --------------------------------------------- | --------------------------------------------- |
| POST   | `/api/v1/document/session/{session_id}`       | Upload into a session (multipart + metadata)  |
| GET    | `/api/v1/document/session/{session_id}`       | Documents of a RAG session                    |
| GET    | `/api/v1/document/{id}`                       | Document metadata                             |
| GET    | `/api/v1/document/{id}/download`              | Download the file                             |
| GET    | `/api/v1/document/{id}/view`                  | Inline preview                                |
| DELETE | `/api/v1/document/{id}`                       | Delete document, artifacts and file           |
| PUT    | `/api/v1/document/{id}`                       | Update metadata                               |
| POST   | `/api/v1/document/{id}/extract`               | On-demand extraction (`extractor`, `persist`) |
| PUT    | `/api/v1/document/{id}/extractor`             | Commit extractor choice (`extractor`)         |

`GET /api/v1/document/` and `GET /api/v1/document/related-sessions/{id}` are
gone: there is no global document list any more, and the latter read the dead
link table, so it always answered `[]`.

## Frontend

Documents are managed from inside the session, in its left panel. There is no
standalone documents page: `/app/generative/rag/documents` redirects to the RAG
home.

Under `components/generative/RAG/`:

- `DocumentsBar` — the session's document panel: the list, upload, per-row
  inspect and delete.
- `DocumentList` / `DocumentListItem` — presentational list and row; the row
  reveals its actions on hover.
- `DocumentInspectorModal` — the old extractor modal, now the document
  inspector: the original file beside its extracted text, an extractor selector
  filtered by `supported_file_types`, and a schema-driven params form. It
  extracts on open. A modal rather than a panel because the left panel is too
  narrow to read extracted text in, and the centre column stays with the chat.
- `DocumentPreviewModal` — the plain "show me the file" view, on row click.

The API client (`api/rag.ts`) exposes `getSessionDocuments()`, `addDocument()`
(session-scoped), `deleteDocument()`, `getExtractorOptions()`,
`extractDocumentText()` and `updateDocumentExtractor()`.

## Related Docs

- [`01-overview.md`](./01-overview.md) — module overview and component types.
- [`02-backend-architecture.md`](./02-backend-architecture.md) — service layer,
  chunking, and pipeline architecture.
- [`05-known-limitations.md`](./05-known-limitations.md) — extractor caveats and
  performance notes.
