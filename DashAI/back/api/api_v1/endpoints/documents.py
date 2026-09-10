import json
import logging
import os
from typing import Any, Dict, List
from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from kink import di
from sqlalchemy.orm import sessionmaker

from DashAI.back.api.api_v1.schemas import (
    DocumentResponse,
    UpdateExtractorRequest,
)
from DashAI.back.dependencies.database.models import Document, GenerativeSession
from DashAI.back.models.RAG.documents import DocumentFileType
from DashAI.back.models.RAG.exceptions import (
    RAGDocumentExtractionError,
    RAGDocumentFileTypeError,
)
from DashAI.back.services.RAG.document_service import DocumentService
from DashAI.back.services.RAG.index_job_service import cancel_live_index_job

router = APIRouter()
log = logging.getLogger(__name__)


def _cancel_index_for_document(db, document_id: int) -> None:
    """Stop a running index before changing what it is indexing.

    Dropping a document or re-extracting its text deletes the very chunk,
    retriever and embedding rows a running job is writing, so the two must not
    overlap. The caller's transaction commits the cleared pointer.
    """
    document = db.get(Document, document_id)
    if document is None or document.session_id is None:
        return
    session = db.get(GenerativeSession, document.session_id)
    if session is not None:
        cancel_live_index_job(session, di["job_queue"])


base_url = "/api/v1/document"

DISPOSITION_ATTACHMENT = "attachment"
DISPOSITION_INLINE = "inline"


def _file_response(
    content: bytes, media_type: str, filename: str, disposition: str
) -> Response:
    """Build a ``Response`` serving ``content`` with a Content-Disposition header.

    Parameters
    ----------
    content : bytes
        Raw file bytes.
    media_type : str
        MIME type of the file.
    filename : str
        Original file name, encoded into the disposition header.
    disposition : str
        Either ``"attachment"`` or ``"inline"``.

    Returns
    -------
    Response
        FastAPI response with the given content and disposition.
    """
    encoded_name = quote(filename, safe="")
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": (f"{disposition}; filename*=UTF-8''{encoded_name}")
        },
    )


def _serve_document(
    document_id: int, disposition: str, session_factory: sessionmaker
) -> Response:
    """Load a document from disk and serve it with the given disposition.

    Parameters
    ----------
    document_id : int
        Database ID of the document to serve.
    disposition : str
        Either ``"attachment"`` or ``"inline"``.
    session_factory : sessionmaker
        Database session factory from the DI container.

    Returns
    -------
    Response
        FastAPI response with the document content.

    Raises
    ------
    HTTPException
        If the document or its physical file is not found.
    """
    with session_factory() as db:
        try:
            content, media_type, filename = DocumentService(db).download(document_id)
            return _file_response(content, media_type, filename, disposition)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    request: Request,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Get metadata of a document by its ID."""
    with session_factory() as db:
        try:
            return DocumentService(db).get(document_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
) -> Response:
    """Download the actual file content of a document."""
    return _serve_document(document_id, DISPOSITION_ATTACHMENT, session_factory)


@router.get("/{document_id}/view")
async def view_document(
    document_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
) -> Response:
    """Return file content for inline viewing (e.g. in an iframe preview)."""
    return _serve_document(document_id, DISPOSITION_INLINE, session_factory)


@router.post(
    "/session/{session_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    session_id: int,
    file: UploadFile = File(...),
    metadata: str = Form(...),
    config: Dict[str, Any] = Depends(lambda: di["config"]),
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Upload a document into one RAG session.

    Documents belong to exactly one session, so the same file can be uploaded
    into several sessions independently. Uploading it twice into the *same*
    session changes nothing and returns ``409 Conflict`` with the existing
    document. Extraction failures are surfaced as ``500``.
    """
    from DashAI.back.dependencies.registry.component_registry import ComponentRegistry

    registry: ComponentRegistry = di["component_registry"]
    docs_folder_path = config["DOCUMENTS_PATH"]
    if not docs_folder_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Documents folder {docs_folder_path} does not exist.",
        )
    try:
        metadata_dict = json.loads(metadata)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON in metadata"
        ) from None
    file_name = metadata_dict.get("file_name")
    if not file_name:
        raise HTTPException(
            status_code=400, detail="Missing required 'file_name' in metadata"
        )
    optional_metadata = metadata_dict.get("optional_metadata", {})
    if not isinstance(optional_metadata, dict):
        raise HTTPException(
            status_code=400, detail="'optional_metadata' must be a dictionary"
        )
    try:
        content_bytes = await file.read()
    except Exception:
        raise HTTPException(
            status_code=400, detail="Failed to read file content"
        ) from None
    ext = os.path.splitext(file_name)[1].lstrip(".")
    try:
        file_type = DocumentFileType(ext)
    except ValueError:
        supported = ", ".join(DocumentFileType.supported_extensions())
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: {ext or '(none)'}. "
                f"Supported types: {supported}."
            ),
        ) from None
    with session_factory() as db:
        try:
            result = DocumentService(db, registry).upload(
                content_bytes,
                file_name,
                file_type,
                str(docs_folder_path),
                session_id,
                optional_metadata,
                registry=registry,
            )
        except RAGDocumentExtractionError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            ) from e
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e

        if result.duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "detail": "This session already has this document",
                    "existing_document": result.document.model_dump(mode="json"),
                },
            )

        return result.document


@router.get("/session/{session_id}", response_model=List[DocumentResponse])
async def get_documents_by_session(
    session_id: int,
    request: Request,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Get all documents associated with a specific RAG session."""
    with session_factory() as db:
        try:
            base = str(request.base_url).rstrip("/")
            return DocumentService(db).get_by_session(session_id, base_url=base)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Delete a document from the RAG system by its ID."""

    with session_factory() as db:
        try:
            _cancel_index_for_document(db, document_id)
            DocumentService(db).delete(document_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document_metadata(
    document_id: int,
    metadata: str = Form(...),
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Update a document's metadata."""
    with session_factory() as db:
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400, detail="Invalid JSON in metadata"
            ) from None
        file_name = metadata_dict.get("file_name")
        optional_metadata = metadata_dict.get("optional_metadata")

        try:
            return DocumentService(db).update_metadata(
                document_id,
                file_name=file_name,
                optional_metadata=optional_metadata,
            )
        except RAGDocumentFileTypeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e


@router.post("/{document_id}/extract")
async def extract_document_text(
    document_id: int,
    request: Request,
    config: Dict[str, Any] = Depends(lambda: di["config"]),
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Extract text from a document on demand.

    Request body (optional):
        {
            "extractor": {"component": "PyMuPDFExtractor", "params": {}},
            "persist": true  // false for preview mode
        }

    If extractor is not provided, uses the document's stored extractor
    or file-type default.

    Returns:
        dict with text, extractor ref, char_count, cached, created, updated.
    """
    from DashAI.back.dependencies.registry.component_registry import ComponentRegistry

    registry: ComponentRegistry = di["component_registry"]

    try:
        body = await request.json() if request.headers.get("content-length") else {}
    except Exception:
        body = {}

    extractor_ref = body.get("extractor")
    persist = body.get("persist", True)  # Default to True for backward compatibility

    with session_factory() as db:
        try:
            result = DocumentService(db, registry).extract_text(
                document_id,
                extractor_ref=extractor_ref,
                persist=persist,
            )
            return result
        except ValueError as e:
            msg = str(e)
            if "does not support" in msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=msg
                ) from e
            if "not found in registry" in msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=msg
                ) from e
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=msg
            ) from e


@router.put("/{document_id}/extractor", response_model=DocumentResponse)
async def update_document_extractor(
    document_id: int,
    body: UpdateExtractorRequest,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Commit an extractor choice for a document.

    Re-extracts the text and drops the chunks, retrievers and embeddings
    fitted over the previous extraction, as one transaction: if extraction
    fails, nothing changes and the error is reported as ``422``.
    """
    from DashAI.back.dependencies.registry.component_registry import ComponentRegistry

    registry: ComponentRegistry = di["component_registry"]

    with session_factory() as db:
        try:
            _cancel_index_for_document(db, document_id)
            return DocumentService(db, registry).update_extractor(
                document_id,
                extractor_ref=body.extractor.model_dump(),
            )
        except RAGDocumentExtractionError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
            ) from e
        except ValueError as e:
            msg = str(e)
            if "does not support" in msg or "not found in registry" in msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=msg
                ) from e
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=msg
            ) from e
