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

from DashAI.back.api.api_v1.schemas import DocumentResponse
from DashAI.back.models.RAG.documents import DocumentFileType
from DashAI.back.models.RAG.exceptions import (
    RAGDocumentExtractionError,
    RAGDocumentFileTypeError,
)
from DashAI.back.services.RAG.document_service import DocumentService

router = APIRouter()
log = logging.getLogger(__name__)


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


@router.get("/", response_model=List[DocumentResponse])
async def get_all_documents(
    request: Request,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Get all documents with file_url included."""
    with session_factory() as db:
        base = str(request.base_url).rstrip("/")
        return DocumentService(db).get_all(base_url=base)


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


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    metadata: str = Form(...),
    force: bool = False,
    response: Response = None,
    config: Dict[str, Any] = Depends(lambda: di["config"]),
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Upload a new document to the RAG system with file content and metadata.

    If a document with the same content hash already exists and ``force`` is
    ``False``, returns ``409 Conflict`` with the existing document and the
    affected sessions so the client can ask for confirmation. With
    ``force=True`` the existing document is overwritten and its RAG artifacts
    are invalidated. Extraction failures are surfaced as ``500``.
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
                optional_metadata,
                registry=registry,
                force=force,
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
                    "detail": "Document already exists",
                    "existing_document": result.document.model_dump(mode="json"),
                    "affected_sessions": result.affected_sessions,
                },
            )

        if result.updated and response is not None:
            response.status_code = status.HTTP_200_OK
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


@router.get("/related-sessions/{document_id}", response_model=List[int])
async def get_related_sessions(
    document_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Get all generative session IDs related to a specific document."""
    with session_factory() as db:
        try:
            return DocumentService(db).get_related_sessions(document_id)
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


@router.put("/{document_id}/extractor")
async def update_document_extractor(
    document_id: int,
    request: Request,
    config: Dict[str, Any] = Depends(lambda: di["config"]),
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    """Commit an extractor choice for a document.

    Request body:
        {"extractor": {"component": "PyMuPDFExtractor", "params": {}}, "force": false}

    If the document is linked to RAG pipelines and force=false, returns 409
    Conflict with affected session info. With force=true, artifacts are
    invalidated.
    """
    from DashAI.back.dependencies.registry.component_registry import ComponentRegistry

    registry: ComponentRegistry = di["component_registry"]

    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        ) from e

    extractor_ref = body.get("extractor")
    force = body.get("force", False)

    if not extractor_ref or not isinstance(extractor_ref, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing or invalid 'extractor' in request body. "
            "Expected {component: str, params: dict}.",
        )

    with session_factory() as db:
        try:
            result = DocumentService(db, registry).update_extractor(
                document_id,
                extractor_ref=extractor_ref,
                force=force,
            )
            return result
        except ValueError as e:
            msg = str(e)
            if "linked to" in msg and "RAG pipeline" in msg:
                linked_ids = DocumentService(db).get_related_sessions(document_id)
                from DashAI.back.dependencies.database.models import GenerativeSession

                affected_sessions = []
                if linked_ids:
                    sessions = (
                        db.query(GenerativeSession)
                        .filter(GenerativeSession.id.in_(linked_ids))
                        .all()
                    )
                    affected_sessions = [{"id": s.id, "name": s.name} for s in sessions]
                raise HTTPException(
                    status_code=409,
                    detail={
                        "detail": msg,
                        "affected_sessions": affected_sessions,
                    },
                ) from e
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
