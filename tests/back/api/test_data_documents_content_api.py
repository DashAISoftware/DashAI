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
