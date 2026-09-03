import json
import logging
import mimetypes
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.api.api_v1.schemas import DocumentResponse
from DashAI.back.dependencies.database.models import (
    Document as DocumentDBModel,
)
from DashAI.back.dependencies.database.models import (
    GenerativeSession,
    GenerativeSessionParameterHistory,
    RAGExtractor,
)
from DashAI.back.models.RAG.documents import (
    BaseDocument,
    DocumentFileType,
    PDFDocument,
    TxtDocument,
)
from DashAI.back.models.RAG.exceptions import (
    RAGDocumentExtractionError,
    RAGDocumentFileTypeError,
)
from DashAI.back.models.RAG.extractors.base_extractor import BaseExtractor
from DashAI.back.models.RAG.utils import hash_function

log = logging.getLogger(__name__)

#: Only RAG sessions own documents.
_RAG_TASK_NAME = "RAGTask"
#: Session parameter key mirroring the documents a session owns.
_DOCUMENTS_KEY = "documents"
#: Sub-directory holding content-addressed document blobs.
_BLOBS_DIRNAME = "blobs"

_DOCUMENT_CLASSES: dict[DocumentFileType, type[BaseDocument]] = {
    DocumentFileType.TXT: TxtDocument,
    DocumentFileType.PDF: PDFDocument,
    DocumentFileType.MD: TxtDocument,
    DocumentFileType.RST: TxtDocument,
    DocumentFileType.TEX: TxtDocument,
    # CSV, MD, RST, TEX are parsed as plain text via TxtDocument.
    # This is a limitation: CSV files are structured data, not free text.
    # A future improvement would add a dedicated CsvDocument parser.
    DocumentFileType.CSV: TxtDocument,
}


@dataclass
class DocumentUploadResult:
    """Outcome of a document upload attempt.

    ``duplicate`` is set when the session already holds this exact file (by
    content hash), in which case nothing is modified and the caller should
    surface a conflict. ``created`` is set for the success path.
    """

    document: DocumentResponse
    created: bool = False
    duplicate: bool = False


class DocumentService:
    """Service layer for document CRUD, file storage, and hydration."""

    _DEFAULT_EXTRACTORS: dict[str, str] = {
        "pdf": "PyMuPDFExtractor",
        "txt": "PlainTextExtractor",
        "md": "PlainTextExtractor",
        "rst": "PlainTextExtractor",
        "tex": "PlainTextExtractor",
        "csv": "PlainTextExtractor",
    }

    def __init__(self, db: Session, registry=None):
        self.db = db
        self._registry = registry

    def _resolve_extractor_ref(
        self, db_doc
    ) -> "Tuple[Optional[BaseExtractor], Optional[str], dict]":
        """Resolve a document's extractor together with how it is configured.

        Callers need the component name and params, not just the instance: the
        extraction cache signature is built from them. Deriving them separately
        (e.g. reading ``params`` as ``{}`` while instantiating with the stored
        params) makes the signature disagree with itself, which never hits the
        cache and re-invalidates the index on every call.

        Parameters
        ----------
        db_doc : DocumentDBModel

        Returns
        -------
        tuple
            ``(extractor, component_name, params)``. The extractor is ``None``
            when no component applies or no registry is available; the name and
            params still describe what *would* be used.
        """
        extractor_record = db_doc.extractor_record  # RAGExtractor or None

        if extractor_record is not None:
            component_name = extractor_record.component_name
            params = dict(extractor_record.params or {})
        else:
            # Default by file type
            component_name = self._DEFAULT_EXTRACTORS.get(db_doc.file_type)
            params = {}

        if component_name is None or self._registry is None:
            return None, component_name, params

        try:
            extractor_cls = self._registry[component_name]["class"]
        except KeyError:
            return None, component_name, params
        return extractor_cls(**params), component_name, params

    def _resolve_extractor(self, db_doc) -> "Optional[BaseExtractor]":
        """Resolve the extractor instance for a document."""
        extractor, _, _ = self._resolve_extractor_ref(db_doc)
        return extractor

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_rag_session_or_raise(self, session_id: int) -> GenerativeSession:
        """Return the RAG session that may own documents, or raise.

        Parameters
        ----------
        session_id : int

        Returns
        -------
        GenerativeSession

        Raises
        ------
        ValueError
            If the session does not exist or is not a RAG session.
        """
        session = self.db.get(GenerativeSession, session_id)
        if session is None:
            raise ValueError(f"GenerativeSession with ID {session_id} not found.")
        if session.task_name != _RAG_TASK_NAME:
            raise ValueError(
                f"Session {session_id} is a '{session.task_name}' session; "
                "only RAG sessions hold documents."
            )
        return session

    @staticmethod
    def _write_blob(docs_path: str, file_hash: str, file_content: bytes) -> str:
        """Store bytes content-addressed and return their path.

        Naming files after ``file_name`` alone let two different uploads with
        the same name resolve to the same path, so the second silently
        overwrote the first. Keying on the content hash removes that collision
        and lets sessions holding identical files share one file on disk.

        Parameters
        ----------
        docs_path : str
            Root documents directory.
        file_hash : str
            SHA-256 of the file contents.
        file_content : bytes

        Returns
        -------
        str
            Absolute path of the stored blob.
        """
        blobs_dir = os.path.join(docs_path, _BLOBS_DIRNAME)
        os.makedirs(blobs_dir, exist_ok=True)
        file_path = os.path.join(blobs_dir, file_hash)
        # Identical content yields an identical path; writing again is a no-op
        # apart from the cost, so skip it.
        if not os.path.exists(file_path):
            with open(file_path, "wb") as f:
                f.write(file_content)
        return file_path

    def _get_or_create_extractor_row(
        self, component_name: str, params: dict
    ) -> RAGExtractor:
        """Return the extractor record for a configuration, creating it once.

        ``rag_extractor`` rows are immutable value objects, so identical
        configurations should share one row. Creating a fresh row per call
        leaked one row on every extractor change, and none of them could be
        removed while a document still pointed at any of them.

        Parameters
        ----------
        component_name : str
        params : dict
            Canonicalised (key-sorted) extractor parameters.

        Returns
        -------
        RAGExtractor
            An existing or freshly flushed record.
        """
        existing = (
            self.db.query(RAGExtractor)
            .filter_by(component_name=component_name, params=params)
            .first()
        )
        if existing is not None:
            return existing
        record = RAGExtractor(component_name=component_name, params=params)
        self.db.add(record)
        self.db.flush()
        return record

    def _drop_extractor_if_orphaned(self, extractor_id: int | None) -> None:
        """Delete an extractor record once no document references it.

        Call this *after* flushing the deletion of the documents that used to
        reference it: ``document.extractor_id`` is NOT NULL, so removing the
        record while a row still points at it fails on the next flush.

        Parameters
        ----------
        extractor_id : int | None
        """
        if extractor_id is None:
            return
        still_used = (
            self.db.query(DocumentDBModel)
            .filter(DocumentDBModel.extractor_id == extractor_id)
            .count()
        )
        if still_used:
            return
        record = self.db.get(RAGExtractor, extractor_id)
        if record is not None:
            self.db.delete(record)

    def _sync_session_documents(self, session: GenerativeSession) -> None:
        """Mirror the session's documents into its ``parameters`` list.

        The foreign key is the authority on which documents a session owns,
        but ``parameters["documents"]`` is what the pipeline, the chunk-set
        signature and the parameter history all read, so the two must be kept
        in step. Clients never send this key; only the document endpoints
        change it.

        Parameters
        ----------
        session : GenerativeSession
        """
        self.db.flush()
        document_ids = [
            row[0]
            for row in self.db.query(DocumentDBModel.id)
            .filter_by(session_id=session.id)
            .order_by(DocumentDBModel.id)
            .all()
        ]
        parameters = dict(session.parameters or {})
        if parameters.get(_DOCUMENTS_KEY) == document_ids:
            return
        parameters[_DOCUMENTS_KEY] = document_ids
        session.parameters = parameters
        self.db.add(
            GenerativeSessionParameterHistory(
                session_id=session.id, parameters=parameters
            )
        )

    def _unlink_if_unreferenced(self, file_path: str, exclude_id: int) -> None:
        """Remove a stored file once the last document pointing at it is gone.

        Blobs are shared by every session holding the same bytes (and legacy
        rows migrated from the global library may share a path too), so the
        file may only be removed when no other row references it.

        Parameters
        ----------
        file_path : str
        exclude_id : int
            The document being deleted, ignored when counting references.
        """
        if not file_path:
            return
        others = (
            self.db.query(DocumentDBModel)
            .filter(
                DocumentDBModel.file_path == file_path,
                DocumentDBModel.id != exclude_id,
            )
            .count()
        )
        if others:
            return
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            log.warning("Failed to remove document file %s: %s", file_path, e)

    def _to_response(
        self, doc: DocumentDBModel, base_url: str = ""
    ) -> DocumentResponse:
        """Build a ``DocumentResponse`` from a DB row.

        Parameters
        ----------
        doc : DocumentDBModel
            Database document row.
        base_url : str
            URL prefix used to build absolute ``file_url`` and ``preview_url``.

        Returns
        -------
        DocumentResponse
            API representation of the document.
        """
        extractor_dict = None
        if doc.extractor_record is not None:
            extractor_dict = {
                "component": doc.extractor_record.component_name,
                "params": doc.extractor_record.params or {},
            }
        else:
            default_name = self._DEFAULT_EXTRACTORS.get(doc.file_type)
            if default_name:
                extractor_dict = {"component": default_name, "params": {}}

        default_extractor_dict = None
        if doc.extractor_record is None:
            default_name = self._DEFAULT_EXTRACTORS.get(doc.file_type)
            if default_name:
                default_extractor_dict = {"component": default_name, "params": {}}

        return DocumentResponse(
            id=doc.id,
            session_id=doc.session_id,
            file_name=doc.file_name,
            file_type=doc.file_type,
            file_hash=doc.file_hash,
            created=doc.created,
            last_modified=doc.last_modified,
            optional_metadata=doc.optional_metadata,
            extractor=extractor_dict,
            default_extractor=default_extractor_dict,
            file_url=f"{base_url}/api/v1/document/{doc.id}/download",
            preview_url=f"{base_url}/api/v1/document/{doc.id}/view",
        )

    def _get_document_or_raise(self, document_id: int) -> DocumentDBModel:
        doc = self.db.get(DocumentDBModel, document_id)
        if doc is None:
            raise ValueError(f"Document with ID {document_id} does not exist.")
        return doc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upload(
        self,
        file_content: bytes,
        file_name: str,
        file_type: str | DocumentFileType,
        docs_path: str,
        session_id: int,
        optional_metadata: dict = None,
        registry=None,
    ) -> DocumentUploadResult:
        """Upload a document into one RAG session.

        Documents belong to exactly one session, so deduplication is per
        session: uploading the same bytes into a *different* session creates a
        second, independent document, free to pick its own extractor.
        Re-uploading into the same session changes nothing and is reported as
        a duplicate.

        The bytes are stored content-addressed under ``<docs_path>/blobs``, so
        two sessions holding the same file share one file on disk and two
        different files with the same name cannot overwrite each other.

        After the record is committed, extraction runs immediately (when a
        component registry is available) to populate the extraction cache so a
        subsequent ``extract_text`` call returns ``cached=True``. Extraction
        failures are raised as ``RAGDocumentExtractionError``.

        Parameters
        ----------
        file_content : bytes
            Raw file bytes.
        file_name : str
            Original file name.
        file_type : str | DocumentFileType
            File extension / type, e.g. ``DocumentFileType.PDF`` or ``"pdf"``.
        docs_path : str
            Directory on disk where the file will be written.
        session_id : int
            The RAG session that will own the document.
        optional_metadata : dict, optional
            Arbitrary metadata attached to the document.
        registry : ComponentRegistry, optional
            Component registry used to resolve extractors. When provided,
            default extraction runs on upload to warm the cache.

        Returns
        -------
        DocumentUploadResult
            Result describing the created document or the duplicate.

        Raises
        ------
        ValueError
            If ``docs_path`` does not exist, the session does not exist or is
            not a RAG session, or a database error occurs.
        RAGDocumentExtractionError
            If pre-extraction fails during upload.
        """
        if isinstance(file_type, DocumentFileType):
            file_type = file_type.value
        if not os.path.isdir(docs_path):
            raise ValueError(f"Documents folder does not exist: {docs_path}")

        session = self._get_rag_session_or_raise(session_id)
        optional_metadata = optional_metadata or {}
        file_content_hash = hash_function(file_content)

        try:
            existing = (
                self.db.query(DocumentDBModel)
                .filter_by(session_id=session_id, file_hash=file_content_hash)
                .first()
            )
            if existing is not None:
                return DocumentUploadResult(
                    document=self._to_response(existing), duplicate=True
                )

            file_path = self._write_blob(docs_path, file_content_hash, file_content)

            default_component = self._DEFAULT_EXTRACTORS.get(file_type)
            extractor_record = None
            if default_component:
                extractor_record = self._get_or_create_extractor_row(
                    default_component, {}
                )

            doc = DocumentDBModel(
                session_id=session_id,
                file_name=file_name,
                file_type=file_type,
                file_path=file_path,
                file_hash=file_content_hash,
                optional_metadata=optional_metadata or None,
                extractor_id=extractor_record.id if extractor_record else None,
            )
            self.db.add(doc)
            self.db.flush()
            self._sync_session_documents(session)
            self.db.commit()
            self.db.refresh(doc)

            if registry is not None:
                self._registry = registry
                self._pre_extract_or_raise(doc.id, file_name)

            return DocumentUploadResult(document=self._to_response(doc), created=True)

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise ValueError("Database error during document upload.") from e

    def _pre_extract_or_raise(self, document_id: int, file_name: str) -> None:
        """Extract text after upload, raising a typed error on failure.

        Parameters
        ----------
        document_id : int
            Document whose text should be pre-extracted.
        file_name : str
            Original file name, used in the error message.

        Raises
        ------
        RAGDocumentExtractionError
            If extraction fails for any reason.
        """
        try:
            self.extract_text(document_id)
        except RAGDocumentExtractionError:
            raise
        except Exception as e:
            log.exception("Failed to pre-extract text during upload")
            raise RAGDocumentExtractionError(
                f"Failed to extract text from '{file_name}': {e}"
            ) from e

    def get(self, document_id: int) -> DocumentResponse:
        """Get document metadata by ID.

        Parameters
        ----------
        document_id : int

        Returns
        -------
        DocumentResponse

        Raises
        ------
        ValueError
            If the document does not exist.
        """
        try:
            doc = self._get_document_or_raise(document_id)
            return self._to_response(doc)
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise ValueError("Database error retrieving document.") from e

    def get_by_session(
        self, session_id: int, base_url: str = ""
    ) -> List[DocumentResponse]:
        """Get the documents owned by a generative session.

        Parameters
        ----------
        session_id : int
        base_url : str

        Returns
        -------
        list[DocumentResponse]
        """
        try:
            session = self.db.get(GenerativeSession, session_id)
            if session is None:
                raise ValueError(f"GenerativeSession with ID {session_id} not found.")

            docs = (
                self.db.query(DocumentDBModel)
                .filter_by(session_id=session_id)
                .order_by(DocumentDBModel.id)
                .all()
            )
            return [self._to_response(d, base_url) for d in docs]

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise ValueError("Database error retrieving session documents.") from e

    def delete(self, document_id: int) -> None:
        """Delete a document, its RAG artifacts, and its file.

        The chunks, retrievers and embedding matrices fitted over this document
        are invalidated first: leaving them behind kept stale directories on
        disk that nothing would ever reclaim.

        Parameters
        ----------
        document_id : int

        Raises
        ------
        ValueError
            If the document does not exist.
        """
        from DashAI.back.services.RAG.cleanup_service import CleanupService

        try:
            doc = self._get_document_or_raise(document_id)
            session = self.db.get(GenerativeSession, doc.session_id)
            file_path = doc.file_path

            artifact_paths: List[str] = []
            CleanupService(self.db).invalidate_document_artifacts(
                document_id, commit=False, defer_paths=artifact_paths
            )
            self._unlink_if_unreferenced(file_path, document_id)

            extractor_id = doc.extractor_id
            self.db.delete(doc)
            self.db.flush()
            self._drop_extractor_if_orphaned(extractor_id)
            if session is not None:
                self._sync_session_documents(session)
            self.db.commit()
        except exc.SQLAlchemyError as e:
            self.db.rollback()
            log.exception(e)
            raise ValueError("Database error deleting document.") from e

        for path in artifact_paths:
            CleanupService._delete_path(path)

    def delete_by_session(self, session_id: int) -> None:
        """Delete every document a session owns, with its files and artifacts.

        Called before a session is deleted. The ORM cascade would drop the rows
        on its own, but nothing would remove the files or the fitted artifacts
        from disk.

        Parameters
        ----------
        session_id : int
        """
        from DashAI.back.services.RAG.cleanup_service import CleanupService

        documents = (
            self.db.query(DocumentDBModel).filter_by(session_id=session_id).all()
        )
        if not documents:
            return

        artifact_paths: List[str] = []
        try:
            extractor_ids = set()
            for doc in documents:
                CleanupService(self.db).invalidate_document_artifacts(
                    doc.id, commit=False, defer_paths=artifact_paths
                )
                self._unlink_if_unreferenced(doc.file_path, doc.id)
                extractor_ids.add(doc.extractor_id)
                self.db.delete(doc)
            self.db.flush()
            for extractor_id in extractor_ids:
                self._drop_extractor_if_orphaned(extractor_id)
            self.db.commit()
        except exc.SQLAlchemyError as e:
            self.db.rollback()
            log.exception(e)
            raise ValueError("Database error deleting session documents.") from e

        for path in artifact_paths:
            CleanupService._delete_path(path)

    def update_metadata(
        self,
        document_id: int,
        file_name: str = None,
        optional_metadata: dict = None,
    ) -> DocumentResponse:
        """Update document metadata (``file_name``, ``optional_metadata``).

        Parameters
        ----------
        document_id : int
        file_name : str, optional
            New file name.  Also updates ``file_type`` from the extension.
        optional_metadata : dict, optional

        Returns
        -------
        DocumentResponse

        Raises
        ------
        ValueError
            If the document does not exist.
        """
        try:
            doc = self._get_document_or_raise(document_id)

            if file_name is not None:
                doc.file_name = file_name
                ext = os.path.splitext(file_name)[1].lstrip(".")
                try:
                    doc.file_type = DocumentFileType(ext).value
                except ValueError as err:
                    raise RAGDocumentFileTypeError(
                        f"Unsupported file type: {ext}"
                    ) from err

            if optional_metadata is not None:
                doc.optional_metadata = optional_metadata

            doc.last_modified = datetime.now()
            self.db.commit()
            self.db.refresh(doc)
            return self._to_response(doc)

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise ValueError("Database error updating document metadata.") from e

    def download(self, document_id: int) -> Tuple[bytes, str, str]:
        """Return file content, media type, and filename for download.

        Parameters
        ----------
        document_id : int

        Returns
        -------
        tuple[bytes, str, str]
            ``(file_content, media_type, filename)``.

        Raises
        ------
        ValueError
            If the document or its physical file is not found.
        """
        try:
            doc = self._get_document_or_raise(document_id)

            if not os.path.exists(doc.file_path):
                raise ValueError(f"File not found on disk: {doc.file_path}")

            ext = os.path.splitext(doc.file_name)[1].lower()
            media_type, _ = mimetypes.guess_type(doc.file_name)
            if media_type is None:
                media_type = {
                    ".txt": "text/plain",
                    ".pdf": "application/pdf",
                }.get(ext, "application/octet-stream")

            with open(doc.file_path, "rb") as f:
                content = f.read()

            return content, media_type, doc.file_name

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise ValueError("Database error during document download.") from e

    def load(self, document_ids: List[int]) -> Dict[int, BaseDocument]:
        """Load and hydrate DB document rows into ``BaseDocument`` instances.

        Parameters
        ----------
        document_ids : list[int]

        Returns
        -------
        dict[int, BaseDocument]
            Mapping from document ID to hydrated document object.

        Raises
        ------
        ValueError
            If any document ID is not found or the file type is unsupported.
        """
        documents: Dict[int, BaseDocument] = {}
        for doc_id in document_ids:
            db_doc: DocumentDBModel = (
                self.db.query(DocumentDBModel)
                .filter(DocumentDBModel.id == doc_id)
                .first()
            )
            if db_doc is None:
                raise ValueError(f"Document with ID {doc_id} not found in database.")
            try:
                doc_class = _DOCUMENT_CLASSES[DocumentFileType(db_doc.file_type)]
            except (KeyError, ValueError) as err:
                supported = ", ".join(e.value for e in DocumentFileType)
                raise ValueError(
                    f"Unsupported file type '{db_doc.file_type}'. "
                    f"Supported types: {supported}."
                ) from err

            extractor = self._resolve_extractor(db_doc)
            documents[doc_id] = doc_class(
                id=db_doc.id,
                file_name=db_doc.file_name,
                file_path=db_doc.file_path,
                file_hash=db_doc.file_hash,
                created=db_doc.created,
                optional_metadata=db_doc.optional_metadata,
                extractor=extractor,
            )
        return documents

    def _build_text_signature(
        self, file_hash: str, component_name: str, params: dict
    ) -> str:
        """Build a cache signature for extracted text.

        The signature captures the file content hash and the exact extractor
        configuration, so re-extraction only happens when either changes.
        """
        payload = f"{file_hash}:{component_name}:{json.dumps(params, sort_keys=True)}"
        return hash_function(payload)

    def extract_text(
        self,
        document_id: int,
        extractor_ref: Optional[dict] = None,
        persist: bool = True,
    ) -> dict:
        """Extract text from a document on demand, with 1:1 caching.

        Each document has exactly one ``processed_document_content`` row. On a
        cache miss the existing row (if any) is updated in place rather than
        creating a second record. When the content changes because a different
        extractor or set of parameters produced a new signature, RAG artifacts
        (chunks, retrievers, embeddings) of the related sessions are
        invalidated via ``CleanupService.invalidate_document_artifacts``.

        Args:
            document_id: Document ID.
            extractor_ref: Optional {component, params} dict. If None, uses
                stored/default.
            persist: If False, extract text without persisting to cache or
                invalidating artifacts (preview mode). Defaults to True.

        Returns:
            dict with keys: text, extractor, char_count, cached (bool),
            created (bool), updated (bool).

        Raises:
            ValueError if document not found or extractor incompatible.
        """
        from DashAI.back.dependencies.database.models import ProcessedDocumentContent
        from DashAI.back.services.RAG.cleanup_service import CleanupService

        doc = self._get_document_or_raise(document_id)

        # Resolve which extractor to use
        if extractor_ref is not None:
            component_name = extractor_ref.get("component")
            params = extractor_ref.get("params", {})
            if component_name is None:
                raise ValueError("extractor_ref must include 'component' key")
            if self._registry is None:
                raise ValueError("No registry available to resolve extractor")
            try:
                extractor_cls = self._registry[component_name]["class"]
            except KeyError as err:
                raise ValueError(
                    f"Extractor '{component_name}' not found in registry"
                ) from err
            extractor = extractor_cls(**params)
        else:
            extractor, component_name, params = self._resolve_extractor_ref(doc)
            if extractor is None:
                raise ValueError(f"No extractor available for document {document_id}")

        # Check compatibility
        supported = getattr(extractor, "SUPPORTED_FILE_TYPES", [])
        if supported and doc.file_type not in supported:
            raise ValueError(
                f"Extractor '{component_name}' does not support file type "
                f"'{doc.file_type}'. Supported types: {supported}"
            )

        # Build signature and check the single cached row
        signature = self._build_text_signature(doc.file_hash, component_name, params)

        if not persist:
            # Preview mode: extract without persisting or invalidating
            text = extractor.extract(doc.file_path)
            char_count = len(text)
            return {
                "text": text,
                "extractor": {"component": component_name, "params": params},
                "char_count": char_count,
                "cached": False,
                "created": False,
                "updated": False,
            }

        existing = (
            self.db.query(ProcessedDocumentContent)
            .filter_by(document_id=document_id)
            .first()
        )
        if existing is not None and existing.signature == signature:
            return {
                "text": existing.content,
                "extractor": {"component": component_name, "params": params},
                "char_count": existing.char_count,
                "cached": True,
                "created": False,
                "updated": False,
            }

        # Cache miss — extract and store (updating the single row if present)
        text = extractor.extract(doc.file_path)
        char_count = len(text)

        artifact_paths: List[str] = []
        if existing is not None:
            # A different extractor or different params produced different
            # text, so everything fitted over the old text is stale.
            CleanupService(self.db).invalidate_document_artifacts(
                document_id, commit=False, defer_paths=artifact_paths
            )
            existing.content = text
            existing.signature = signature
            existing.char_count = char_count
            created, updated = False, True
        else:
            # Nothing has been chunked yet -- chunking needs extracted text --
            # so there are no artifacts to invalidate on a first extraction.
            cache_entry = ProcessedDocumentContent(
                document_id=document_id,
                content=text,
                signature=signature,
                char_count=char_count,
            )
            self.db.add(cache_entry)
            created, updated = True, False
        self.db.commit()

        for path in artifact_paths:
            CleanupService._delete_path(path)

        return {
            "text": text,
            "extractor": {"component": component_name, "params": params},
            "char_count": char_count,
            "cached": False,
            "created": created,
            "updated": updated,
        }

    def update_extractor(
        self, document_id: int, extractor_ref: dict
    ) -> "DocumentResponse":
        """Change a document's extractor, re-extract it, and drop stale artifacts.

        The whole operation is one transaction, and the extraction runs *before*
        anything is mutated. Committing the new ``extractor_id`` first meant a
        failing extractor (a malformed PDF under ``strict=True``, say) left the
        document pointing at an extractor that had never produced its text,
        still serving the previous extractor's chunks.

        Artifacts are invalidated unconditionally. The old ``force`` flag was
        meant to make the user confirm a destructive re-index, but it asked
        ``RAGDocumentPipelineSessionLink`` -- a table nothing ever wrote to --
        which sessions were affected, so the confirmation never triggered.
        A document now belongs to exactly one session, so there is nobody else
        to warn.

        Args:
            document_id: Document ID.
            extractor_ref: ``{component, params}`` dict.

        Returns:
            DocumentResponse with the updated extractor.

        Raises:
            ValueError: If the document does not exist, or the extractor is
                unknown or incompatible with the document's file type.
            RAGDocumentExtractionError: If extraction with the new extractor
                fails. Nothing is changed in that case.
        """
        from DashAI.back.dependencies.database.models import ProcessedDocumentContent
        from DashAI.back.services.RAG.cleanup_service import CleanupService

        doc = self._get_document_or_raise(document_id)

        component_name = extractor_ref.get("component")
        if not component_name:
            raise ValueError("extractor_ref must include 'component' key")
        # Canonical (key-sorted) form, so the same configuration always hashes
        # and compares equal.
        params = dict(sorted((extractor_ref.get("params") or {}).items()))

        if self._registry is None:
            raise ValueError("No registry available to resolve extractor")
        try:
            extractor_cls = self._registry[component_name]["class"]
        except KeyError as err:
            raise ValueError(
                f"Extractor '{component_name}' not found in registry"
            ) from err

        supported = getattr(extractor_cls, "SUPPORTED_FILE_TYPES", [])
        if supported and doc.file_type not in supported:
            raise ValueError(
                f"Extractor '{component_name}' does not support file type "
                f"'{doc.file_type}'. Supported types: {supported}"
            )

        signature = self._build_text_signature(doc.file_hash, component_name, params)
        cached = (
            self.db.query(ProcessedDocumentContent)
            .filter_by(document_id=document_id)
            .first()
        )

        # Saving the extractor it already has must not throw away a good index.
        current = doc.extractor_record
        unchanged = (
            current is not None
            and current.component_name == component_name
            and dict(current.params or {}) == params
            and cached is not None
            and cached.signature == signature
        )
        if unchanged:
            return self._to_response(doc)

        extractor = extractor_cls(**params)
        try:
            text = extractor.extract(doc.file_path)
        except Exception as e:
            log.exception(e)
            raise RAGDocumentExtractionError(
                f"Failed to extract text from '{doc.file_name}' with "
                f"'{component_name}': {e}"
            ) from e

        artifact_paths: List[str] = []
        try:
            record = self._get_or_create_extractor_row(component_name, params)
            previous_extractor_id = doc.extractor_id
            doc.extractor_id = record.id
            doc.last_modified = datetime.now()

            CleanupService(self.db).invalidate_document_artifacts(
                document_id, commit=False, defer_paths=artifact_paths
            )

            if cached is not None:
                cached.content = text
                cached.signature = signature
                cached.char_count = len(text)
            else:
                self.db.add(
                    ProcessedDocumentContent(
                        document_id=document_id,
                        content=text,
                        signature=signature,
                        char_count=len(text),
                    )
                )

            if previous_extractor_id != record.id:
                self._drop_extractor_if_orphaned(previous_extractor_id)

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        for path in artifact_paths:
            CleanupService._delete_path(path)

        self.db.refresh(doc)
        return self._to_response(doc)

    def validate_exist(self, document_ids: List[int]) -> None:
        """Raise ``ValueError`` if any document ID does not exist in the DB.

        Parameters
        ----------
        document_ids : list[int]

        Raises
        ------
        ValueError
            If one or more document IDs are not found.
        """
        existing = (
            self.db.query(DocumentDBModel.id)
            .filter(DocumentDBModel.id.in_(document_ids))
            .all()
        )
        existing_ids = {row.id for row in existing}
        missing = [str(i) for i in document_ids if i not in existing_ids]
        if missing:
            raise ValueError(f"Documents with IDs {', '.join(missing)} not found.")

    def validate_belong_to_session(
        self, document_ids: List[int], session_id: int
    ) -> None:
        """Raise ``ValueError`` unless every document belongs to the session.

        A session must never reference another session's document: the two
        would share chunks and an extractor choice.

        Parameters
        ----------
        document_ids : list[int]
        session_id : int

        Raises
        ------
        ValueError
            If a document is missing or owned by a different session.
        """
        if not document_ids:
            return
        rows = (
            self.db.query(DocumentDBModel.id, DocumentDBModel.session_id)
            .filter(DocumentDBModel.id.in_(document_ids))
            .all()
        )
        owner_by_id = {row.id: row.session_id for row in rows}
        missing = [str(i) for i in document_ids if i not in owner_by_id]
        if missing:
            raise ValueError(f"Documents with IDs {', '.join(missing)} not found.")
        foreign = [str(i) for i in document_ids if owner_by_id[i] != session_id]
        if foreign:
            raise ValueError(
                f"Documents with IDs {', '.join(foreign)} belong to a different "
                "session."
            )
