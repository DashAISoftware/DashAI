"""Builders for DashAIDocument test data shared by the document tool tests."""

import io
import shutil
import uuid
from pathlib import Path
from typing import Optional, Sequence


def png_bytes(color=(255, 0, 0)) -> bytes:
    """Return the bytes of a tiny PNG image.

    Parameters
    ----------
    color : tuple of int, optional
        RGB fill colour, by default red.

    Returns
    -------
    bytes
        A 4 x 4 PNG image.
    """
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color).save(buffer, format="PNG")
    return buffer.getvalue()


def text(content: str, kind: str = "paragraph", page: Optional[int] = 1, **attrs):
    """Return a Text item.

    Parameters
    ----------
    content : str
        The text.
    kind : str, optional
        Element kind, by default ``"paragraph"``.
    page : int, optional
        Page number, by default 1.
    **attrs
        Element attributes, such as a heading ``level``.

    Returns
    -------
    DocumentItem
        The item.
    """
    from DashAI.back.dataloaders.classes.dashai_document import DocumentItem
    from DashAI.back.types.value_types import Text

    return DocumentItem(Text, content, page=page, kind=kind, attrs=attrs or None)


def image(page: Optional[int] = 1):
    """Return an Image item holding a tiny PNG.

    Parameters
    ----------
    page : int, optional
        Page number, by default 1.

    Returns
    -------
    DocumentItem
        The item.
    """
    from DashAI.back.dataloaders.classes.dashai_document import DocumentItem
    from DashAI.back.types.dashai_image import DashAIImage

    return DocumentItem(
        DashAIImage, DashAIImage(bytes=png_bytes(), path="image.png"), page=page
    )


def build_document(items: Sequence):
    """Build a document from items listed in reading order.

    Parameters
    ----------
    items : Sequence[DocumentItem or str]
        The items; a bare string is a paragraph.

    Returns
    -------
    DashAIDocument
        The document.
    """
    from DashAI.back.dataloaders.classes.dashai_document import DashAIDocument

    return DashAIDocument.from_items(
        [text(item) if isinstance(item, str) else item for item in items],
        metadata={"file_name": "doc.txt", "file_type": "txt"},
    )


def write_document(path, items: Sequence) -> Path:
    """Build a document and save it at ``path``.

    Parameters
    ----------
    path : str or Path
        Target document directory.
    items : Sequence[DocumentItem or str]
        The items in reading order.

    Returns
    -------
    Path
        The document directory.
    """
    from DashAI.back.dataloaders.classes.dashai_document import save_document

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    save_document(build_document(items), str(path))
    return path


def create_document_notebook(client, name: str, items: Sequence) -> int:
    """Create a stored document, a notebook on it and its working copy.

    Parameters
    ----------
    client : TestClient
        The app test client, used to reach the config and session factory.
    name : str
        Unique document and notebook name.
    items : Sequence[DocumentItem or str]
        The items in reading order.

    Returns
    -------
    int
        The notebook id.
    """
    from DashAI.back.core.enums.status import DocumentStatus
    from DashAI.back.dependencies.database.models import DataDocument, Notebook

    container = client.app.container
    config = container["config"]
    session_factory = container["session_factory"]

    document_dir = Path(config["DOCUMENTS_PATH"]) / uuid.uuid4().hex
    write_document(document_dir / "document", items)
    notebook_dir = Path(config["NOTEBOOK_PATH"]) / "documents" / uuid.uuid4().hex
    shutil.copytree(document_dir / "document", notebook_dir / "document")

    counts = build_document(items).content_counts
    with session_factory() as db:
        document = DataDocument(
            name=name,
            file_name=f"{name}.txt",
            file_type="txt",
            file_hash=uuid.uuid4().hex,
            file_path=str(document_dir),
            dataloader="PlainTextDocumentDataLoader",
            dataloader_params={},
            content_counts=counts,
            status=DocumentStatus.FINISHED,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        notebook = Notebook(
            document_id=document.id, file_path=str(notebook_dir), name=name
        )
        db.add(notebook)
        db.commit()
        db.refresh(notebook)
        return notebook.id
