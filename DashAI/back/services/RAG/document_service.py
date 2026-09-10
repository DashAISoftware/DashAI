import json
import logging
import mimetypes
import os
from dataclasses import dataclass, field
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

    ``duplicate`` is set when the same file (by content hash) already exists
    and ``force=False``: in that case the caller should surface a conflict and
    let the user decide whether to overwrite. ``created`` / ``updated`` are set
    for the success paths.
    """

    document: DocumentResponse
    created: bool = False
    updated: bool = False
    duplicate: bool = False
    affected_sessions: List[dict] = field(default_factory=list)


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

    def _resolve_extractor(self, db_doc) -> "Optional[BaseExtractor]":
        """Resolve the extractor for a document from its extractor_record."""
        extractor_record = db_doc.extractor_record  # RAGExtractor or None

        if extractor_record is not None:
            component_name = extractor_record.component_name
            params = extractor_record.params or {}
        else:
            # Default by file type
            component_name = self._DEFAULT_EXTRACTORS.get(db_doc.file_type)
            if component_name is None:
                return None
            params = {}

        if self._registry is None:
            return None

        try:
            extractor_cls = self._registry[component_name]["class"]
            return extractor_cls(**params)
        except KeyError:
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

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
            file_name=doc.file_name,
            file_type=doc.file_type,
            file_hash=doc.file_hash,
            created=doc.created,
            last_modified=doc.last_modified,
            optional_metadata=doc.optional_metadata,
            extractor=extractor_dict,
            default_extractor=default_extractor_dict,
            related_sessions=[s.id for s in doc.get_related_sessions]
            if doc.get_related_sessions
            else None,
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
        optional_metadata: dict = None,
        registry=None,
        force: bool = False,
    ) -> DocumentUploadResult:
        """Upload a document, deduplicating by content hash.

        Handles hash deduplication, file storage, and DB record creation.

        If a document with the same file hash already exists and ``force`` is
        ``False``, nothing is modified and the result reports the existing
        document together with its related sessions so the caller can ask the
        user whether to overwrite. With ``force=True`` the file is rewritten
        and RAG artifacts are invalidated.

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
        optional_metadata : dict, optional
            Arbitrary metadata attached to the document.
        registry : ComponentRegistry, optional
            Component registry used to resolve extractors. When provided,
            default extraction runs on upload to warm the cache.
        force : bool
            If ``True`` and the file already exists, overwrite it instead of
            reporting a duplicate.

        Returns
        -------
        DocumentUploadResult
            Result describing the created/updated document or the duplicate.

        Raises
        ------
        ValueError
            If ``docs_path`` does not exist or a database error occurs.
        RAGDocumentExtractionError
            If pre-extraction fails during upload.
        """
        if isinstance(file_type, DocumentFileType):
            file_type = file_type.value
        if not os.path.isdir(docs_path):
            raise ValueError(f"Documents folder does not exist: {docs_path}")

        optional_metadata = optional_metadata or {}
        file_content_hash = hash_function(file_content)
        file_path = os.path.join(docs_path, file_name)

        try:
            existing = (
                self.db.query(DocumentDBModel)
                .filter_by(file_hash=file_content_hash)
                .first()
            )

            if existing is not None and not force:
                affected_sessions = [
                    {"id": s.id, "name": s.name} for s in existing.get_related_sessions
                ]
                return DocumentUploadResult(
                    document=self._to_response(existing),
                    duplicate=True,
                    affected_sessions=affected_sessions,
                )

            if existing is not None:
                return self._overwrite_existing(
                    existing,
                    file_content,
                    file_path,
                    file_name,
                    optional_metadata,
                    registry,
                )

            with open(file_path, "wb") as f:
                f.write(file_content)

            default_component = self._DEFAULT_EXTRACTORS.get(file_type)
            extractor_record = None
            if default_component:
                extractor_record = RAGExtractor(
                    component_name=default_component,
                    params={},
                )
                self.db.add(extractor_record)
                self.db.flush()

            doc = DocumentDBModel(
                file_name=file_name,
                file_type=file_type,
                file_path=file_path,
                file_hash=file_content_hash,
                optional_metadata=optional_metadata or None,
                extractor_id=extractor_record.id if extractor_record else None,
            )
            self.db.add(doc)
            self.db.commit()
            self.db.refresh(doc)

            if registry is not None:
                self._registry = registry
                self._pre_extract_or_raise(doc.id, file_name)

            return DocumentUploadResult(document=self._to_response(doc), created=True)

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise ValueError("Database error during document upload.") from e

    def _overwrite_existing(
        self,
        existing: DocumentDBModel,
        file_content: bytes,
        file_path: str,
        file_name: str,
        optional_metadata: dict,
        registry,
    ) -> DocumentUploadResult:
        """Overwrite an existing document's file and metadata on force re-upload.

        Re-extracts text and invalidates any RAG artifacts tied to the
        document so downstream fitted models are recomputed on the next run.

        Parameters
        ----------
        existing : DocumentDBModel
            The existing document row matched by content hash.
        file_content : bytes
            Raw file bytes to write to disk.
        file_path : str
            Absolute path of the uploaded file.
        file_name : str
            Original file name.
        optional_metadata : dict
            Metadata to attach to the document.
        registry : ComponentRegistry, optional
            Registry used to resolve extractors for re-extraction.

        Returns
        -------
        DocumentUploadResult
            Result marking the document as updated.
        """
        from DashAI.back.services.RAG.cleanup_service import CleanupService

        with open(file_path, "wb") as f:
            f.write(file_content)

        existing.file_name = file_name
        existing.file_path = file_path
        existing.optional_metadata = optional_metadata
        existing.last_modified = datetime.now()
        self.db.commit()
        self.db.refresh(existing)

        CleanupService(self.db).invalidate_document_artifacts(existing.id)

        if registry is not None:
            self._registry = registry
            self._pre_extract_or_raise(existing.id, file_name)

        return DocumentUploadResult(document=self._to_response(existing), updated=True)

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

    def get_all(self, base_url: str = "") -> List[DocumentResponse]:
        """Get all documents with ``file_url`` included.

        Parameters
        ----------
        base_url : str
            Base URL prefix for download links.

        Returns
        -------
        list[DocumentResponse]
        """
        try:
            docs: List[DocumentDBModel] = self.db.query(DocumentDBModel).all()
            return [self._to_response(d, base_url) for d in docs]
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise ValueError("Database error listing documents.") from e

    def get_by_session(
        self, session_id: int, base_url: str = ""
    ) -> List[DocumentResponse]:
        """Get documents linked to a generative session.

        Documents are identified from ``session.parameters["documents"]``.

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

            document_ids: List[int] = session.parameters.get("documents", [])
            if not document_ids:
                return []

            docs = (
                self.db.query(DocumentDBModel)
                .filter(DocumentDBModel.id.in_(document_ids))
                .all()
            )
            return [self._to_response(d, base_url) for d in docs]

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise ValueError("Database error retrieving session documents.") from e

    def delete(self, document_id: int) -> None:
        """Delete a document file from disk and its DB record.

        Parameters
        ----------
        document_id : int

        Raises
        ------
        ValueError
            If the document does not exist.
        """
        try:
            doc = self._get_document_or_raise(document_id)

            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)

            self.db.delete(doc)
            self.db.commit()

        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise ValueError("Database error deleting document.") from e
        except OSError as e:
            log.exception(e)
            raise ValueError("Error deleting physical file.") from e

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
            extractor = self._resolve_extractor(doc)
            if extractor is None:
                raise ValueError(f"No extractor available for document {document_id}")
            component_name = extractor.__class__.__name__
            params = {}

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

        if existing is not None:
            CleanupService(self.db).invalidate_document_artifacts(document_id)
            existing.content = text
            existing.signature = signature
            existing.char_count = char_count
            created, updated = False, True
        else:
            cache_entry = ProcessedDocumentContent(
                document_id=document_id,
                content=text,
                signature=signature,
                char_count=char_count,
            )
            self.db.add(cache_entry)
            created, updated = True, False
        self.db.commit()

        return {
            "text": text,
            "extractor": {"component": component_name, "params": params},
            "char_count": char_count,
            "cached": False,
            "created": created,
            "updated": updated,
        }

    def update_extractor(
        self, document_id: int, extractor_ref: dict, force: bool = False
    ) -> "DocumentResponse":
        """Persist an extractor choice via rag_extractor table.

        When the extractor changes, the single ``processed_document_content``
        row is re-extracted with the new extractor. With ``force=True`` (or
        when the document has no linked sessions) RAG artifacts are
        invalidated via ``CleanupService.invalidate_document_artifacts``.

        Args:
            document_id: Document ID.
            extractor_ref: {component, params} dict.
            force: If True, skip confirmation and invalidate artifacts.

        Returns:
            DocumentResponse with updated extractor.

        Raises:
            ValueError if document not found or extractor invalid.
        """
        from DashAI.back.dependencies.database.models import RAGExtractor
        from DashAI.back.services.RAG.cleanup_service import CleanupService

        doc = self._get_document_or_raise(document_id)

        component_name = extractor_ref.get("component")
        params = extractor_ref.get("params", {})

        if not component_name:
            raise ValueError("extractor_ref must include 'component' key")

        # Validate extractor exists and is compatible
        if self._registry is not None:
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

        if not force:
            linked_session_ids = self.get_related_sessions(document_id)
            if linked_session_ids:
                raise ValueError(
                    f"Document is linked to {len(linked_session_ids)} RAG "
                    f"pipeline(s). Changing the extractor will delete existing "
                    f"chunks and retrievers. Use force=true to proceed."
                )

        # Create a new RAGExtractor record (no dedup for now — simple approach)
        extractor_record = RAGExtractor(
            component_name=component_name,
            params=params if params else None,
        )
        self.db.add(extractor_record)
        self.db.flush()  # Get the ID
        doc.extractor_id = extractor_record.id
        doc.last_modified = datetime.now()

        if force:
            CleanupService(self.db).invalidate_document_artifacts(document_id)

        self.db.commit()
        self.db.refresh(doc)

        # Re-extract with the new extractor so the single processed content row
        # reflects the new extractor config (keeps the 1:1 invariant).
        if self._registry is not None:
            self.extract_text(document_id, extractor_ref=extractor_ref)
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

    def get_related_sessions(self, document_id: int) -> List[int]:
        """Get session IDs linked to a document.

        Parameters
        ----------
        document_id : int

        Returns
        -------
        list[int]
            Session IDs related to the document.

        Raises
        ------
        ValueError
            If the document is not found.
        """
        try:
            doc = self._get_document_or_raise(document_id)
            if not doc.get_related_sessions:
                return []
            return [s.id for s in doc.get_related_sessions]
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise ValueError("Database error retrieving related sessions.") from e
