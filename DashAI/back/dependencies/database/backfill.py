import json
import logging
import os
import pathlib
import shutil
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from sqlalchemy.orm import Session, sessionmaker

    from DashAI.back.dependencies.database.models import (
        DataDocument,
        RAGLegacyDocument,
    )

log = logging.getLogger(__name__)


def backfill_dataset_counts(session_factory: "sessionmaker") -> None:
    """Populate total_rows/total_columns for FINISHED datasets with NULL counts.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory from the DI container.
    """
    from DashAI.back.core.enums.status import DatasetStatus
    from DashAI.back.dependencies.database.models import Dataset

    with session_factory() as db:
        pending = (
            db.query(Dataset)
            .filter(
                Dataset.status == DatasetStatus.FINISHED,
                Dataset.total_rows == None,  # noqa: E711 (SQLAlchemy ORM requires == for column IS NULL)
            )
            .all()
        )
        updated = 0

        if not pending:
            log.debug("No datasets found that require backfilling.")
            return
        for ds in pending:
            try:
                from DashAI.back.dataloaders.classes.dashai_dataset import (
                    get_dataset_info,
                )

                info = get_dataset_info(f"{ds.file_path}/dataset")
                ds.total_rows = info["total_rows"]
                ds.total_columns = info["total_columns"]
                updated += 1
            except Exception as e:
                log.warning("Failed to backfill dataset %d: %s", ds.id, e)
        if updated:
            db.commit()
            log.debug("Backfilled counts for %d dataset(s).", updated)


def backfill_explorer_artifacts(session_factory: "sessionmaker") -> None:
    """Persist the render artifacts of explorations created before they existed.

    Explorations used to build their artifacts on every read request, which
    made them unreadable once their explorer class was removed from the
    registry. This backfill stores the artifacts of every finished exploration
    that still lacks them, while the explorer classes are installed. Explorers
    that are already gone are skipped: nothing can be recovered for them.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory from the DI container.
    """
    from kink import di

    from DashAI.back.core.enums.status import ExplorerStatus
    from DashAI.back.dependencies.database.models import Explorer
    from DashAI.back.exploration.artifact_store import (
        has_stored_artifacts,
        store_artifacts,
    )

    component_registry = di["component_registry"]

    with session_factory() as db:
        pending = (
            db.query(Explorer)
            .filter(
                Explorer.status == ExplorerStatus.FINISHED,
                Explorer.artifacts_path == None,  # noqa: E711 (SQLAlchemy ORM requires == for column IS NULL)
                Explorer.exploration_path != None,  # noqa: E711
            )
            .all()
        )

        if not pending:
            log.debug("No explorers found that require backfilling.")
            return

        updated = 0
        for explorer in pending:
            if has_stored_artifacts(explorer):
                continue
            try:
                explorer_class = component_registry[explorer.exploration_type]["class"]
                explorer_instance = explorer_class(**explorer.parameters)
                explorer.artifacts_path = store_artifacts(
                    explorer_instance, explorer.exploration_path, explorer.id
                )
                updated += 1
            except Exception as e:
                log.warning(
                    "Failed to backfill artifacts of explorer %d: %s", explorer.id, e
                )
        if updated:
            db.commit()
            log.debug("Backfilled artifacts for %d explorer(s).", updated)


_BLOBS_DIRNAME = "blobs"
_EXTRACTOR_LOADERS = {
    "PypdfExtractor": "PypdfDocumentDataLoader",
    "PdfPlumberExtractor": "PdfPlumberDocumentDataLoader",
    "PdfMinerExtractor": "PdfMinerDocumentDataLoader",
    "PlainTextExtractor": "PlainTextDocumentDataLoader",
}
_DEFAULT_PDF_LOADER = "PypdfDocumentDataLoader"
_DEFAULT_TEXT_LOADER = "PlainTextDocumentDataLoader"


@dataclass(frozen=True)
class _ParsedFile:
    """A legacy file parsed into a new document folder.

    Attributes
    ----------
    folder : pathlib.Path
        The ``<uuid>`` folder holding ``source/`` and ``document/``.
    content_counts : dict of str to int
        Items per content type.
    total_pages : int or None
        Page count reported by the DataLoader.
    """

    folder: pathlib.Path
    content_counts: Dict[str, int]
    total_pages: Optional[int]


def backfill_rag_documents(
    session_factory: "sessionmaker",
    component_registry,
    documents_path,
) -> None:
    """Turn the staged legacy RAG documents into Data module documents.

    Migration ``c5d1a9e74f28`` stages every legacy RAG document in
    ``rag_legacy_document``. This finishes the move while the document
    DataLoaders are registered:

    1. Chunk sets without an owning session are deleted with their retrievers,
       embeddings and files: they indexed legacy document ids.
    2. Each staged row is parsed with the DataLoader matching its extractor
       into a new ``DataDocument``. Rows with the same file, DataLoader and
       parameters share one ``DataDocument``.
    3. Per session, the documents are linked, ``parameters["documents"]`` is
       rebuilt from the links, the session is marked ``needs_reindex`` and
       its chat citations are pointed at the new ids, in one transaction.
    4. Legacy files no staged row uses any more are removed, then the
       ``blobs`` folder once empty.

    A row that cannot be converted keeps an ``error`` and is not retried.

    Parameters
    ----------
    session_factory : sessionmaker
        SQLAlchemy session factory from the DI container.
    component_registry : ComponentRegistry
        Registry resolving the document DataLoaders by name.
    documents_path : str or pathlib.Path
        The ``DOCUMENTS_PATH`` setting.
    """
    from DashAI.back.dependencies.database.models import RAGLegacyDocument
    from DashAI.back.services.RAG.cleanup_service import CleanupService

    documents_root = pathlib.Path(documents_path)
    with session_factory() as db:
        removed = CleanupService(db).invalidate_legacy_artifacts()
        if removed:
            log.debug("Removed %d legacy RAG chunk set(s).", removed)

        pending = (
            db.query(RAGLegacyDocument)
            .filter(RAGLegacyDocument.error.is_(None))
            .order_by(RAGLegacyDocument.id)
            .all()
        )
        if not pending:
            log.debug("No legacy RAG documents require backfilling.")
        groups: Dict[Optional[int], List["RAGLegacyDocument"]] = {}
        for legacy in pending:
            groups.setdefault(legacy.session_id, []).append(legacy)
        for session_id, rows in groups.items():
            try:
                freed = _convert_session_rows(
                    db, component_registry, documents_root, session_id, rows
                )
            except Exception as e:
                db.rollback()
                log.warning(
                    "Could not convert the legacy RAG documents of session %s: %s",
                    session_id,
                    e,
                )
                continue
            for path in freed:
                _remove_legacy_file(db, documents_root, path)
    _remove_empty_blobs_dir(documents_root)


def _convert_session_rows(
    db: "Session",
    registry,
    documents_root: pathlib.Path,
    session_id: Optional[int],
    rows: List["RAGLegacyDocument"],
) -> List[str]:
    """Convert the staged rows of one session and commit once.

    Parameters
    ----------
    db : Session
        Database session.
    registry : ComponentRegistry
        Registry resolving the DataLoaders.
    documents_root : pathlib.Path
        The documents folder.
    session_id : int or None
        Session the rows belonged to.
    rows : list of RAGLegacyDocument
        Its staged rows.

    Returns
    -------
    list of str
        Legacy file paths of the converted rows.
    """
    from DashAI.back.dependencies.database.models import (
        GenerativeSession,
        RAGSessionDocument,
    )
    from DashAI.back.services.RAG.session_document_service import (
        SessionDocumentService,
    )

    id_map: Dict[int, int] = {}
    converted: List["RAGLegacyDocument"] = []
    for legacy in rows:
        try:
            data_document = _data_document_for(db, registry, documents_root, legacy)
        except Exception as e:
            legacy.error = (str(e) or e.__class__.__name__)[:500]
            log.warning("Could not convert legacy RAG document %d: %s", legacy.id, e)
            continue
        id_map[legacy.id] = data_document.id
        converted.append(legacy)

    session = db.get(GenerativeSession, session_id) if session_id is not None else None
    if session is not None:
        linked = {
            row[0]
            for row in db.query(RAGSessionDocument.data_document_id)
            .filter(RAGSessionDocument.session_id == session.id)
            .all()
        }
        for data_document_id in sorted(set(id_map.values()) - linked):
            db.add(
                RAGSessionDocument(
                    session_id=session.id, data_document_id=data_document_id
                )
            )
        session.needs_reindex = True
        session.index_job_id = None
        SessionDocumentService(db).sync_session_documents(session)
        _remap_chat_references(db, session.id, id_map)

    paths = [legacy.file_path for legacy in converted]
    for legacy in converted:
        db.delete(legacy)
    db.commit()
    return paths


def _data_document_for(
    db: "Session",
    registry,
    documents_root: pathlib.Path,
    legacy: "RAGLegacyDocument",
) -> "DataDocument":
    """Return the ``DataDocument`` holding a staged row's parse.

    Reuses a finished document with the same file, DataLoader and parameters;
    otherwise parses the file into a new one (flushed, not committed).

    Parameters
    ----------
    db : Session
        Database session.
    registry : ComponentRegistry
        Registry resolving the DataLoaders.
    documents_root : pathlib.Path
        The documents folder.
    legacy : RAGLegacyDocument
        The staged row.

    Returns
    -------
    DataDocument
        The existing or new document.

    Raises
    ------
    KeyError
        If the DataLoader is not registered.
    FileNotFoundError
        If the legacy file is gone.
    """
    from DashAI.back.core.enums.status import DocumentStatus
    from DashAI.back.dependencies.database.models import DataDocument

    loader_name = _loader_name_for(legacy)
    loader = registry[loader_name]["class"]()
    params = _loader_params(loader, legacy.extractor_params)
    candidates = (
        db.query(DataDocument)
        .filter(
            DataDocument.file_hash == legacy.file_hash,
            DataDocument.dataloader == loader_name,
            DataDocument.status == DocumentStatus.FINISHED,
        )
        .all()
    )
    for candidate in candidates:
        if (candidate.dataloader_params or {}) == params:
            return candidate

    parsed = _parse_legacy_file(loader, documents_root, legacy, params)
    record = DataDocument(
        name=_unique_document_name(db, legacy.file_name),
        file_name=legacy.file_name,
        file_type=legacy.file_type,
        file_hash=legacy.file_hash,
        file_path=str(parsed.folder),
        dataloader=loader_name,
        dataloader_params=params,
        content_counts=parsed.content_counts,
        total_pages=parsed.total_pages,
        status=DocumentStatus.FINISHED,
    )
    db.add(record)
    db.flush()
    return record


def _loader_name_for(legacy: "RAGLegacyDocument") -> str:
    """Return the DataLoader replacing a row's extractor.

    Parameters
    ----------
    legacy : RAGLegacyDocument
        The staged row.

    Returns
    -------
    str
        A registered DataLoader name; the file type default for unknown
        extractors.
    """
    if legacy.extractor_component in _EXTRACTOR_LOADERS:
        return _EXTRACTOR_LOADERS[legacy.extractor_component]
    if legacy.file_type == "pdf":
        return _DEFAULT_PDF_LOADER
    return _DEFAULT_TEXT_LOADER


def _loader_params(loader, raw_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Translate legacy extractor parameters into DataLoader parameters.

    The document DataLoaders kept the extractor parameter names (pypdf
    ``strict``; pdfplumber ``password``, ``x_tolerance``, ``y_tolerance``,
    ``layout``, ``extract_tables``; pdfminer ``password``, ``line_margin``,
    ``char_margin``, ``boxes_flow``, ``detect_vertical``; plain text
    ``encoding``), so the accepted keys are copied and the rest dropped.
    ``resolve_params`` then fills the new ones (pypdf ``extract_images`` stays
    at its default ``False``, as the extractor never read images) and
    validates them, exactly as ``DocumentJob`` stores them.

    Parameters
    ----------
    loader : DocumentDataLoader
        The DataLoader instance.
    raw_params : dict or None
        The legacy extractor parameters.

    Returns
    -------
    dict
        Resolved parameters, key sorted.
    """
    accepted = set(getattr(loader.SCHEMA, "model_fields", None) or {})
    kept = {key: value for key, value in (raw_params or {}).items() if key in accepted}
    return dict(sorted(loader.resolve_params(kept).items()))


def _parse_legacy_file(
    loader,
    documents_root: pathlib.Path,
    legacy: "RAGLegacyDocument",
    params: Dict[str, Any],
) -> _ParsedFile:
    """Copy a legacy file into a new document folder and parse it.

    Lays the folder out as ``DocumentJob`` does: ``<uuid>/source/<file>`` and
    ``<uuid>/document/``, with the realpath of ``<uuid>`` as ``file_path``.

    Parameters
    ----------
    loader : DocumentDataLoader
        The DataLoader instance.
    documents_root : pathlib.Path
        The documents folder.
    legacy : RAGLegacyDocument
        The staged row.
    params : dict
        DataLoader parameters.

    Returns
    -------
    _ParsedFile
        The new folder and what it holds.

    Raises
    ------
    FileNotFoundError
        If the legacy file is gone.
    """
    from DashAI.back.dataloaders.classes.dashai_document import save_document

    source = pathlib.Path(legacy.file_path)
    if not source.is_file():
        raise FileNotFoundError(f"Legacy RAG file is missing: {source}")
    folder = pathlib.Path(os.path.realpath(documents_root / uuid.uuid4().hex))
    try:
        source_dir = folder / "source"
        source_dir.mkdir(parents=True)
        source_copy = source_dir / legacy.file_name
        shutil.copy2(source, source_copy)
        document = loader.load_document(str(source_copy), params)
        save_document(document, str(folder / "document"))
    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    return _ParsedFile(
        folder=folder,
        content_counts=_content_counts(document),
        total_pages=document.metadata.get("n_pages"),
    )


def _content_counts(document) -> Dict[str, int]:
    """Count a document's items per content type, as ``DocumentJob`` does.

    Parameters
    ----------
    document : DashAIDocument
        The parsed document.

    Returns
    -------
    dict of str to int
        ``{"Text": n, "Image": m}`` for the types present.
    """
    return {
        dashai_type.display_name(): document.count(dashai_type)
        for dashai_type in document.types
    }


def _unique_document_name(db: "Session", base: str) -> str:
    """Return ``base``, or ``stem (n).ext``, unused by any ``DataDocument``.

    Parameters
    ----------
    db : Session
        Database session.
    base : str
        Preferred name.

    Returns
    -------
    str
        A free name.
    """
    from DashAI.back.dependencies.database.models import DataDocument

    stem, extension = os.path.splitext(base)
    candidate, index = base, 2
    while (
        db.query(DataDocument.id).filter(DataDocument.name == candidate).first()
        is not None
    ):
        candidate = f"{stem} ({index}){extension}"
        index += 1
    return candidate


def _remap_chat_references(
    db: "Session", session_id: int, id_map: Dict[int, int]
) -> None:
    """Point a session's stored chat citations at the new document ids.

    All ids of the session are mapped at once, so a new id that equals another
    legacy id is never mapped twice. A legacy id with no new id, because its
    file could not be converted, becomes None, so it never names an unrelated
    ``data_document`` that happens to take that id.

    Parameters
    ----------
    db : Session
        Database session.
    session_id : int
        The session whose answers are rewritten.
    id_map : dict of int to int
        Legacy id to ``data_document`` id.
    """
    from DashAI.back.dependencies.database.models import (
        GenerativeProcess,
        ProcessData,
    )

    rows = (
        db.query(ProcessData)
        .join(GenerativeProcess, ProcessData.process_id == GenerativeProcess.id)
        .filter(
            GenerativeProcess.session_id == session_id,
            ProcessData.data_type == "Dict",
        )
        .all()
    )
    for row in rows:
        try:
            references = json.loads(row.data)
        except (TypeError, ValueError):
            continue
        if not isinstance(references, dict):
            continue
        changed = False
        for reference in references.values():
            if not isinstance(reference, dict):
                continue
            legacy_id = reference.get("document_id")
            if legacy_id is not None:
                reference["document_id"] = id_map.get(legacy_id)
                changed = True
        if changed:
            row.data = json.dumps(references, ensure_ascii=False)


def _remove_legacy_file(db: "Session", documents_root: pathlib.Path, path: str) -> None:
    """Delete a legacy file once no staged row uses it.

    Only files directly in the documents folder or in ``blobs/`` are touched:
    those are the two legacy layouts, and the Data documents live in
    ``<uuid>/`` folders.

    Parameters
    ----------
    db : Session
        Database session.
    documents_root : pathlib.Path
        The documents folder.
    path : str
        The legacy file path.
    """
    from DashAI.back.dependencies.database.models import RAGLegacyDocument

    if (
        db.query(RAGLegacyDocument.id)
        .filter(RAGLegacyDocument.file_path == path)
        .first()
        is not None
    ):
        return
    file_path = pathlib.Path(path)
    legacy_dirs = {
        documents_root.resolve(),
        (documents_root / _BLOBS_DIRNAME).resolve(),
    }
    if file_path.is_file() and file_path.resolve().parent in legacy_dirs:
        file_path.unlink()


def _remove_empty_blobs_dir(documents_root: pathlib.Path) -> None:
    """Remove the legacy ``blobs`` folder once it is empty.

    Parameters
    ----------
    documents_root : pathlib.Path
        The documents folder.
    """
    blobs = documents_root / _BLOBS_DIRNAME
    if blobs.is_dir() and not any(blobs.iterdir()):
        blobs.rmdir()
