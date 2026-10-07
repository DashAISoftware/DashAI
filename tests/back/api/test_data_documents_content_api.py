"""Tests for the document content, image and source endpoints."""

import io
import uuid

from PIL import Image

from tests.back.dataloaders.document_samples import image_pdf_bytes, write_mixed_pdf


def test_content_lists_items_in_reading_order(client, upload_document):
    document = upload_document(b"One.\n\nTwo.\n\nThree.")
    body = client.get(f"/api/v1/documents/{document['id']}/content").json()
    assert body["total"] == 3
    assert [
        (item["type"], item["position"], item["page"], item["content"])
        for item in body["items"]
    ] == [
        ("Text", 0, None, "One."),
        ("Text", 1, None, "Two."),
        ("Text", 2, None, "Three."),
    ]


def test_content_paginates_and_filters(client, upload_document):
    document = upload_document(b"One.\n\nTwo.\n\nThree.")
    url = f"/api/v1/documents/{document['id']}/content"
    page = client.get(url, params={"content_type": "Text", "offset": 1, "limit": 1})
    assert page.json()["total"] == 3
    assert [item["position"] for item in page.json()["items"]] == [1]
    images = client.get(url, params={"content_type": "Image"}).json()
    assert images["total"] == 0
    assert images["items"] == []
    assert client.get(url, params={"content_type": "Table"}).status_code == 422


def test_mixed_pdf_keeps_reading_order_and_serves_images(
    client, upload_document, tmp_path
):
    pdf = write_mixed_pdf(tmp_path / "mixed.pdf")
    with open(pdf, "rb") as handle:
        content = handle.read()
    document = upload_document(
        content,
        file_name="mixed.pdf",
        dataloader="PypdfDocumentDataLoader",
        dataloader_params={"extract_images": True},
    )
    assert document["content_counts"] == {"Text": 2, "Image": 1}
    assert document["total_pages"] == 2
    items = client.get(f"/api/v1/documents/{document['id']}/content").json()["items"]
    assert [(item["type"], item["position"], item["page"]) for item in items] == [
        ("Text", 0, 1),
        ("Image", 1, 1),
        ("Text", 2, 2),
    ]
    image = client.get(items[1]["url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"
    assert Image.open(io.BytesIO(image.content)).size == (8, 8)
    assert client.get(f"/api/v1/documents/{document['id']}/images/0").status_code == 404


def test_source_is_served_inline_and_as_download(client, upload_document):
    document = upload_document(b"Plain body.", file_name="body.txt")
    view = client.get(f"/api/v1/documents/{document['id']}/source/view")
    assert view.status_code == 200
    assert view.text == "Plain body."
    assert view.headers["content-type"].startswith("text/plain")
    assert view.headers["content-disposition"].startswith("inline")
    download = client.get(f"/api/v1/documents/{document['id']}/source")
    assert download.headers["content-disposition"].startswith("attachment")


def test_source_is_always_revalidated(client, upload_document):
    """Document ids are reused once a row is deleted, so a browser must never
    reuse a cached source without checking it against the server first."""
    document = upload_document(b"Plain body.", file_name="body.txt")
    base = f"/api/v1/documents/{document['id']}"
    for url in (f"{base}/source", f"{base}/source/view"):
        assert client.get(url).headers["cache-control"] == "no-cache"


def test_pdf_source_is_served_as_pdf(client, upload_document):
    document = upload_document(
        image_pdf_bytes(), file_name="picture.pdf", dataloader="PypdfDocumentDataLoader"
    )
    view = client.get(f"/api/v1/documents/{document['id']}/source/view")
    assert view.headers["content-type"] == "application/pdf"


def test_source_of_a_placeholder_is_not_served(client):
    created = client.post(
        "/api/v1/documents/",
        json={
            "name": f"doc_{uuid.uuid4().hex[:8]}",
            "file_name": "notes.txt",
            "dataloader": "PlainTextDocumentDataLoader",
        },
    ).json()
    base = f"/api/v1/documents/{created['id']}"
    assert client.get(f"{base}/source/view").status_code == 409
    assert client.get(f"{base}/content").status_code == 409
    assert client.get(f"{base}/images/0").status_code == 409


def _mixed_document(upload_document, tmp_path, **extra_params):
    pdf = write_mixed_pdf(tmp_path / "mixed.pdf")
    with open(pdf, "rb") as handle:
        content = handle.read()
    return upload_document(
        content,
        file_name="mixed.pdf",
        dataloader="PypdfDocumentDataLoader",
        dataloader_params={"extract_images": True, **extra_params},
    )


def test_content_and_images_never_load_the_whole_document(
    client, upload_document, tmp_path, monkeypatch
):
    from DashAI.back.dataloaders.classes import dashai_document

    document = _mixed_document(upload_document, tmp_path)

    def refuse(*args, **kwargs):
        raise AssertionError("load_document must not be called")

    monkeypatch.setattr(dashai_document, "load_document", refuse)
    base = f"/api/v1/documents/{document['id']}"

    everything = client.get(f"{base}/content").json()
    texts = client.get(f"{base}/content", params={"content_type": "Text"}).json()
    images = client.get(f"{base}/content", params={"content_type": "Image"}).json()

    assert [(i["type"], i["position"]) for i in everything["items"]] == [
        ("Text", 0),
        ("Image", 1),
        ("Text", 2),
    ]
    assert [i["position"] for i in texts["items"]] == [0, 2]
    assert all(isinstance(i["content"], str) for i in texts["items"])
    assert [i["url"] for i in images["items"]] == [f"{base}/images/1"]
    assert client.get(f"{base}/images/1").status_code == 200
    assert client.get(f"{base}/images/0").status_code == 404


def test_content_endpoints_run_in_the_threadpool():
    import inspect

    from DashAI.back.api.api_v1.endpoints import data_documents

    assert not inspect.iscoroutinefunction(data_documents.get_data_document_content)
    assert not inspect.iscoroutinefunction(data_documents.get_data_document_image)


def test_pdf_password_is_never_stored_or_returned(client, upload_document, tmp_path):
    import json
    from pathlib import Path

    from DashAI.back.dependencies.database.models import DataDocument

    pdf = write_mixed_pdf(tmp_path / "secret.pdf")
    with open(pdf, "rb") as handle:
        content = handle.read()
    created = client.post(
        "/api/v1/documents/",
        json={
            "name": f"secret_{uuid.uuid4().hex[:8]}",
            "file_name": "secret.pdf",
            "dataloader": "PdfPlumberDocumentDataLoader",
            "dataloader_params": {"password": "s3cret"},
        },
    )
    assert created.status_code == 201
    assert created.json()["dataloader_params"]["password"] is None

    document = upload_document(
        content,
        file_name="secret.pdf",
        dataloader="PdfPlumberDocumentDataLoader",
        dataloader_params={"password": "s3cret"},
    )

    assert document["dataloader_params"]["password"] is None
    assert "s3cret" not in json.dumps(client.get("/api/v1/documents/").json())
    with client.app.container["session_factory"]() as db:
        row = db.get(DataDocument, document["id"])
        assert row.dataloader_params["password"] is None
        sidecar = Path(row.file_path) / "document" / "document.json"
    assert "s3cret" not in sidecar.read_text("utf-8")


def test_content_items_carry_kind_and_attrs(client, upload_document, tmp_path):
    document = _mixed_document(upload_document, tmp_path)

    items = client.get(f"/api/v1/documents/{document['id']}/content").json()["items"]

    assert [(item["kind"], item["attrs"]) for item in items] == [
        ("paragraph", {}),
        ("image", {}),
        ("paragraph", {}),
    ]


def test_outline_lists_every_item_without_content(client, upload_document):
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_document import (
        DashAIDocument,
        DocumentItem,
        save_document,
    )
    from DashAI.back.dependencies.database.models import DataDocument
    from DashAI.back.types.dashai_image import DashAIImage
    from DashAI.back.types.value_types import Text

    document = upload_document(b"placeholder")
    png = io.BytesIO()
    Image.new("RGB", (4, 4)).save(png, format="PNG")
    long_heading = "Results " + "x" * 200
    structured = DashAIDocument.from_items(
        [
            DocumentItem(Text, "Annual\nreport", page=1, kind="title"),
            DocumentItem(
                Text, long_heading, page=1, kind="heading", attrs={"level": 2}
            ),
            DocumentItem(Text, "Body text.", page=1),
            DocumentItem(DashAIImage, DashAIImage(bytes=png.getvalue()), page=2),
        ]
    )
    with client.app.container["session_factory"]() as db:
        folder = Path(db.get(DataDocument, document["id"]).file_path)
    save_document(structured, folder / "document")

    body = client.get(f"/api/v1/documents/{document['id']}/outline").json()

    assert body["total"] == 4
    assert body["items"] == [
        {
            "position": 0,
            "type": "Text",
            "kind": "title",
            "page": 1,
            "level": None,
            "label": "Annual report",
        },
        {
            "position": 1,
            "type": "Text",
            "kind": "heading",
            "page": 1,
            "level": 2,
            "label": long_heading[:120],
        },
        {
            "position": 2,
            "type": "Text",
            "kind": "paragraph",
            "page": 1,
            "level": None,
            "label": None,
        },
        {
            "position": 3,
            "type": "Image",
            "kind": "image",
            "page": 2,
            "level": None,
            "label": None,
        },
    ]


def test_outline_of_an_unknown_document_is_404(client):
    assert client.get("/api/v1/documents/987654/outline").status_code == 404
