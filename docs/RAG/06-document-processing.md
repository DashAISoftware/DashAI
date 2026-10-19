# Document Processing

This document describes how the RAG module obtains the text it indexes — the
_Document Loading_ stage of the pipeline. Documents are owned by the **Data
module** and parsed there once; RAG sessions only reference them. This page
covers the document loaders that turn a file into structured text, the storage
model, the upload and parsing flow, the RAG loading stage, how a session
attaches documents, the REST API, and the frontend document manager.

## Ownership

**A document belongs to the Data module, not to a RAG session.** The
`data_document` row is the document; a session only records that it uses one, by
inserting a row in `rag_session_document` (`session_id`, `data_document_id`,
unique together). Several sessions may use the same document and none may change
it, so detaching — or deleting the session — deletes the link, never the
document. `GenerativeSession.document_links` carries the `all, delete-orphan`
cascade that removes those links when the session goes.

The session's JSON list `parameters["documents"]` still holds the ids the
pipeline, the chunk-set signature, the chat guard and the parameter history read.
`SessionDocumentService.sync_session_documents()` rebuilds it from the links and
appends a `GenerativeSessionParameterHistory` entry whenever it changes: the
links are the authority, the list is derived.

Two consequences worth knowing:

- **Chunk sets are not shared between sessions.**
  `ChunkingService.build_chunk_set_signature` hashes the owning `session_id`, the
  document ids and the chunking configuration, so two sessions over the same Data
  documents each chunk and fit their own retriever. That costs CPU and disk in
  exchange for isolation.
- **A document cannot be deleted while a RAG session uses it.**
  `DELETE /api/v1/documents/{id}` returns `409` and lists the sessions (and the
  notebooks deleted with it). The `data_document_id` foreign key's
  `ondelete="RESTRICT"` encodes the same rule, though SQLite does not enforce it
  in this application.

## Supported File Types

The types a document can have come from the **document data loaders** registered
in `get_initial_components()`. Each loader declares `SUPPORTED_EXTENSIONS` and
parses one file into a `DashAIDocument`:

| Loader                          | Extensions             | Library      |
| ------------------------------- | ---------------------- | ------------ |
| `PlainTextDocumentDataLoader`   | txt, md, rst, tex, csv | stdlib       |
| `PypdfDocumentDataLoader`       | pdf                    | `pypdf`      |
| `PdfPlumberDocumentDataLoader`  | pdf                    | `pdfplumber` |
| `PdfMinerDocumentDataLoader`    | pdf                    | `pdfminer.six` |

A parsed document is not a single string: it is an ordered list of **items**
that are either `Text` or `DashAIImage`, each carrying its page and an element
`kind`. RAG keeps only the `Text` items. CSV files go through the plain-text
loader and are treated as free text, not structured data — a known limitation
(see [`05-known-limitations.md`](./05-known-limitations.md)).

## Document Loaders

Loaders subclass `DocumentDataLoader` (`dataloaders/classes/document_dataloader.py`),
itself a `DataLoader` with `DATA_KIND = "document"`, and implement
`load_document(file_path: str, params) -> DashAIDocument`. `resolve_params` fills
omitted fields from the schema placeholders, so a payload that omits a field
validates exactly as the submitted form would. The `SCHEMA` drives the Data
module's upload form.

The four concrete loaders and their parameters (defaults in parentheses):

| Loader                         | Extensions             | Parameters                                                                                              |
| ------------------------------ | ---------------------- | ------------------------------------------------------------------------------------------------------- |
| `PlainTextDocumentDataLoader`  | txt, md, rst, tex, csv | `encoding` (utf-8), `split_paragraphs` (False)                                                           |
| `PypdfDocumentDataLoader`      | pdf                    | `strict` (True), `granularity` (block), `extract_images` (False)                                         |
| `PdfPlumberDocumentDataLoader` | pdf                    | `password` (None), `x_tolerance` (3.0), `y_tolerance` (3.0), `layout` (False), `extract_tables` (False), `granularity` (block), `block_gap` (0.6), `detect_headings` (True) |
| `PdfMinerDocumentDataLoader`   | pdf                    | `password` (None), `line_margin` (0.5), `char_margin` (2.0), `boxes_flow` (0.5), `detect_vertical` (False), `granularity` (block), `detect_headings` (True) |

`granularity` is `block` or `page`: whether one text item spans a layout block
or a whole page. Parameters named in `SENSITIVE_PARAMS` (the PDF `password`) are
blanked by `redact_params` before they are stored or returned.

## Storage Model

- **`data_document`** — the document: `id`, `name` (unique), `file_name`,
  `file_type`, `file_hash`, `file_path`, `dataloader`, `dataloader_params`
  (JSON), `content_counts` (JSON), `total_pages`, `folder_id`, `huey_id`,
  `status`, plus timestamps. `name` is unique across the Data module;
  `file_path` is filled when parsing starts and `file_hash` when it finishes, so
  both are empty while the row is `NOT_STARTED`.
- **`rag_session_document`** — one row per (session, document) link: `session_id`
  FK → `generative_session.id` (`ondelete=CASCADE`), `data_document_id` FK →
  `data_document.id` (`ondelete=RESTRICT`), unique on the pair.
- **`rag_chunk_set` / `rag_chunk_set_document`** — the identity of the chunks a
  session built over a set of documents. `rag_chunk_set.session_id` is the owner
  (NULL only for chunk sets built before sessions owned them, which the startup
  backfill deletes) and `signature` is unique; `rag_chunk_set_document` is the
  membership. The chunks themselves live in `chunk`, keyed by
  `(chunk_set_id, document_id, chunk_index)`.

### Files on disk

Each document owns a folder `<DOCUMENTS_PATH>/<uuid>/`:

- `source/<file_name>` — the uploaded file, copied verbatim.
- `document/document.json` — the format version, metadata and `content_counts`.
- `document/text.arrow`, `document/image.arrow` — one Arrow IPC file per content
  type present, with `content`, `position`, `page`, `kind` and `attrs` columns.

`save_document` replaces the `document/` directory atomically, so no file from a
previous version survives. `file_hash` is the SHA-256 of the source file,
computed by the job when it parses it; unlike the retired session-owned design,
files are **not** content-addressed, so two documents with identical bytes get
separate folders.

## Upload and Parsing

Uploading a document is a two-call Data-module flow, not a RAG one:

1. `POST /api/v1/documents/` creates a `NOT_STARTED` row, resolving the loader
   and validating that the file extension is supported and that the loader
   parameters validate. A taken `name` is `409`; an empty name, an unknown
   loader, an unsupported extension or invalid parameters are `422`.
2. `POST /api/v1/job/` with `job_type=DocumentJob` and the file as multipart runs
   the parse. `DocumentJob` copies the upload to `source/`, hashes it, calls
   `load_document`, saves the parsed document under `document/`, fills
   `file_name`, `file_type`, `file_hash`, `content_counts`, `total_pages` and the
   redacted loader parameters, and marks the row `FINISHED`. Any failure deletes
   the partial folder and marks the row `ERROR`.

The status moves `NOT_STARTED → DELIVERED → STARTED → FINISHED` (or `ERROR`);
`DELIVERED` and `STARTED` are the "busy" states that block deletion.

## The RAG Loading Stage

`DocumentService.load(document_ids)` (`services/RAG/document_service.py`) turns
finished rows into the text the chunkers read:

1. Looks each `DataDocument` up; a missing row or one whose status is not
   `FINISHED` raises `ValueError`.
2. Calls `load_document(<file_path>/document)` and builds a `RAGDocument` from
   the stored parse.
3. `RAGDocument.from_dashai_document` keeps only the `Text` items, one
   `TextSegment` each, in reading order. `RAGDocument` joins the segments with
   `"\n\n"` for the chunkers, while `page_at(offset)` maps any character offset
   back to the page of the segment it falls in, so a chunk can carry the pages it
   came from.

The pipeline loads these once per run (`SetupService` calls
`DocumentService.load(config.documents)`). Documents never change after parsing,
so every session using a document sees the same text.

## Attaching Documents to a Session

`SessionDocumentService` (`services/RAG/session_document_service.py`) owns the
links:

- `attach(session_id, document_ids)` — validates that the session is a RAG
  session and that every document exists and is `FINISHED` (an unfinished one
  raises `DocumentNotReadyError`, surfaced as `409`). Documents already linked
  are skipped. When anything new is linked it discards the session's indexes,
  inserts the links, rebuilds `parameters["documents"]` with a history entry, and
  commits once.
- `detach(session_id, document_id)` — discards the indexes, deletes the single
  link and rebuilds the list. The document stays in the Data module.
- `list_documents`, `sessions_using` and `linked_document_ids` read the links.

## Invalidation

Changing a session's documents, updating its parameters, or deleting the session
calls `CleanupService.invalidate_session_artifacts(session_id)`, which deletes
every `rag_chunk_set` the session owns together with everything fitted on it: its
chunking model (once no other pipeline references it), its retrievers, its
embedding matrices and their on-disk storage folders, and the chunks and
membership rows themselves. Chunk sets carry their owner, so this never reaches
another session's index. Nothing is eagerly recomputed — the next pipeline run
re-chunks and rebuilds retrieval automatically.

The method takes `commit=False` so a caller can make it part of a larger unit of
work; on-disk paths are queued with `remove_after_commit` and removed only after
the transaction commits, since an `rmtree` cannot be rolled back.

## API

Data-module document endpoints (`api_v1/endpoints/data_documents.py`, prefix
`/api/v1/documents`):

| Method | Path                                         | Purpose                                                        |
| ------ | -------------------------------------------- | -------------------------------------------------------------- |
| POST   | `/api/v1/documents/`                         | Create the placeholder row (201)                               |
| POST   | `/api/v1/documents/from-notebook`            | Save a document notebook as a new document (201)               |
| GET    | `/api/v1/documents/`                         | List every document                                            |
| GET    | `/api/v1/documents/{id}`                     | One document                                                   |
| PATCH  | `/api/v1/documents/{id}`                     | Rename and/or move to a folder                                 |
| DELETE | `/api/v1/documents/{id}`                     | Delete (204; 409 while parsing or in use by a RAG session)     |
| GET    | `/api/v1/documents/{id}/content`             | A page of items in reading order                               |
| GET    | `/api/v1/documents/{id}/outline`             | Structure without content                                      |
| GET    | `/api/v1/documents/{id}/images/{position}`   | One image item                                                 |
| GET    | `/api/v1/documents/{id}/source`              | Download the original file                                     |
| GET    | `/api/v1/documents/{id}/source/view`         | Original file inline                                           |

The upload file itself is sent to the generic job endpoint
(`POST /api/v1/job/`, `job_type=DocumentJob`), which is what
`RAGDocumentUpload` calls.

RAG session-document endpoints (`api_v1/endpoints/rag.py`, prefix `/api/v1/rag`):

| Method | Path                                                       | Purpose                                           |
| ------ | ---------------------------------------------------------- | ------------------------------------------------- |
| GET    | `/api/v1/rag/sessions/{session_id}/documents`              | Documents the session uses                        |
| POST   | `/api/v1/rag/sessions/{session_id}/documents`              | Attach documents (`{"document_ids": [...]}`)      |
| DELETE | `/api/v1/rag/sessions/{session_id}/documents/{document_id}`| Detach (204)                                      |

The old session-scoped `/api/v1/document` router — upload, per-document
extractor and `related-sessions` — was removed when documents moved to the Data
module. There is no global RAG document list any more.

## Frontend

Documents are managed from inside the session, in its left panel (`DocumentsBar`,
mounted by `RAGSessionPage`). There is no standalone RAG documents page:
`/app/generative/rag/documents` redirects to the RAG home.

Under `components/generative/RAG/`:

- `DocumentsBar` — the session's document panel: the list, the "add from Data"
  picker, the upload button, and per-row preview and detach.
- `AddFromDataDialog` — the "Data documents" picker: lists the Data module's
  documents, disables the ones already attached or still parsing, and attaches
  the selection by id.
- `RAGDocumentUpload` — uploads a new file into the Data module: creates the
  document, enqueues its parse job, then attaches it to the session once parsing
  finishes. It offers only the loaders whose `supported_extensions` accept the
  chosen file.
- `DocumentList` / `DocumentListItem` — presentational list and row; the row
  badges its indexing state (not indexed / indexing / chunk count) and reveals
  its actions on hover.
- `DocumentPreviewModal` — the "show me the document" view on row click; it
  fetches the Data document, renders it with the Data module's `DocumentView`,
  and links to `/app/data/documents/{id}`.

The API clients are `api/rag.ts` (`listSessionDocuments`,
`attachSessionDocuments`, `detachSessionDocument`) and `api/documents.ts`
(`createDocument`, `enqueueDocumentJob`, `getDocument`, and the content, outline
and source helpers).

## Related Docs

- [`01-overview.md`](./01-overview.md) — module overview and component types.
- [`02-backend-architecture.md`](./02-backend-architecture.md) — service layer,
  chunking, and pipeline architecture.
- [`05-known-limitations.md`](./05-known-limitations.md) — known limitations and
  operational notes.
