"""Regression test for the N+1 query bug in ``ChunkingService``.

``ChunkingService.create`` persists one ``chunk`` row per chunk and then
patches the in-memory chunk ids via ``_update_chunk_ids``.  That method
used to perform an individual ``SELECT ... FROM chunk WHERE document_id=? AND
chunk_index=? AND chunk_set_id=?`` lookup PER CHUNK, even though the
persisted ORM objects already hold their freshly-assigned primary keys.

This test counts the ``SELECT`` statements against the ``chunk`` table fired
during a single ``ChunkingService.create`` call and asserts that only a
constant, bounded number of them is executed.  It was RED before the fix
(the counter was roughly the number of chunks, ~93 for ~92 chunks) and is
GREEN now that ``_persist_chunks`` reuses the freshly-assigned ORM ids.
"""

import contextlib
import os
import tempfile
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import event

from DashAI.back.services.RAG.chunking_service import ChunkingService
from DashAI.back.services.RAG.document_service import DocumentService
from tests.back.RAG.conftest import _create_test_document

CHUNKING_CONFIG = {
    "chunking_model": {
        "component": "CharacterChunkModel",
        "params": {"chunk_size": 200, "chunk_overlap": 20},
    }
}

CHUNK_SIZE = 200
CHUNK_OVERLAP = 20

DOC_TEXT = (
    "DashAI is a graphical toolbox for training and evaluating machine "
    "learning models. " * 200
)

MAX_ALLOWED_CHUNK_SELECTS = 2


def _write_real_doc(client: TestClient, suffix: str) -> tuple[int, str]:
    """Create a DB document row and write its physical ``.txt`` file."""
    doc_id = _create_test_document(client, suffix=suffix)
    file_path = os.path.join(tempfile.gettempdir(), f"test_doc{suffix}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(DOC_TEXT)
    return doc_id, file_path


def test_chunking_create_does_not_perform_n_plus_1_query(
    client: TestClient,
) -> None:
    """A single ``create`` must not issue one chunk SELECT per chunk."""
    run_tag = uuid.uuid4().hex[:8]
    suffix = f"_{run_tag}_nplus1"
    doc_id, file_path = _write_real_doc(client, suffix=suffix)

    engine = client.app.container["engine"]
    counter = {"selects_chunk": 0}

    def count_chunk_selects(conn, cursor, statement, parameters, context, executemany):
        if (
            statement.lstrip().upper().startswith("SELECT")
            and "FROM chunk" in statement
        ):
            counter["selects_chunk"] += 1

    event.listen(engine, "before_cursor_execute", count_chunk_selects)
    try:
        session_factory = client.app.container["session_factory"]
        registry = client.app.container["component_registry"]

        with session_factory() as db:
            doc_service = DocumentService(db)
            docs = doc_service.load([doc_id])

            chunking = ChunkingService(db, registry)
            chunk_set = chunking.get_or_create_chunk_set([doc_id], CHUNKING_CONFIG)

            _record_id, result = chunking.create(
                docs,
                chunk_set.id,
                "CharacterChunkModel",
                {"chunk_size": CHUNK_SIZE, "chunk_overlap": CHUNK_OVERLAP},
            )

            assert result.chunks, (
                "Sanity check failed: chunking produced no chunks for the "
                "test document."
            )
            for document_chunks in result.chunks.values():
                for chunk in document_chunks.values():
                    assert chunk.id is not None, (
                        "A chunk is missing its DB-assigned id after persistence."
                    )

            actual_chunk_count = sum(
                len(document_chunks) for document_chunks in result.chunks.values()
            )
            assert counter["selects_chunk"] <= MAX_ALLOWED_CHUNK_SELECTS, (
                "N+1 query bug in ChunkingService._update_chunk_ids: "
                f"persisting {actual_chunk_count} chunks issued "
                f"{counter['selects_chunk']} SELECT statements against the "
                "'chunk' table (one query per chunk). The fix must reuse the "
                "ids of the already-persisted ORM chunk objects so a single "
                "create() runs at most "
                f"{MAX_ALLOWED_CHUNK_SELECTS} chunk SELECTs."
            )
    finally:
        event.remove(engine, "before_cursor_execute", count_chunk_selects)
        with contextlib.suppress(OSError):
            os.remove(file_path)
