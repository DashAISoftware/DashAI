"""PDF samples for the document loader tests."""

import io
from pathlib import Path
from typing import List


def write_text_pdf(path: Path, pages: List[str]) -> str:
    """Write a PDF with one Helvetica text line per page.

    Parameters
    ----------
    path : pathlib.Path
        Destination file.
    pages : List[str]
        Latin-1 text of each page; an empty string makes a page without text.

    Returns
    -------
    str
        The path written.
    """
    page_refs = [4 + 2 * index for index in range(len(pages))]
    kids = " ".join(f"{ref} 0 R" for ref in page_refs)
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        f"<</Type/Pages/Kids[{kids}]/Count {len(pages)}>>".encode("latin-1"),
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
    ]
    for ref, text in zip(page_refs, pages, strict=True):
        stream = f"BT /F1 24 Tf 72 700 Td ({text}) Tj ET".encode("latin-1")
        objects.append(
            (
                "<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
                f"/Resources<</Font<</F1 3 0 R>>>>/Contents {ref + 1} 0 R>>"
            ).encode("latin-1")
        )
        objects.append(b"<</Length %d>>stream\n%s\nendstream" % (len(stream), stream))
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj" % number + body + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer<</Size %d/Root 1 0 R>>\n" % (len(objects) + 1)
    out += b"startxref\n%d\n%%%%EOF" % xref_pos
    path.write_bytes(bytes(out))
    return str(path)


def image_pdf_bytes() -> bytes:
    """Return a one page PDF holding a single 8x8 red JPEG and no text.

    Returns
    -------
    bytes
        The PDF file content.
    """
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, format="PDF")
    return buffer.getvalue()


def write_mixed_pdf(path: Path) -> str:
    """Write a two page PDF: "Alpha" plus an image on page 1, "Bravo" on page 2.

    Parameters
    ----------
    path : pathlib.Path
        Destination file.

    Returns
    -------
    str
        The path written.
    """
    from pypdf import PdfReader, PdfWriter

    text_path = path.with_name(f"{path.stem}_text.pdf")
    write_text_pdf(text_path, ["Alpha", "Bravo"])
    writer = PdfWriter(clone_from=str(text_path))
    writer.pages[0].merge_page(PdfReader(io.BytesIO(image_pdf_bytes())).pages[0])
    writer.write(str(path))
    return str(path)
