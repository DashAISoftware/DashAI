"""Tests for document extractors."""

import pytest

from DashAI.back.models.RAG.exceptions import RAGDocumentParsingError
from DashAI.back.models.RAG.extractors.base_extractor import BaseExtractor
from DashAI.back.models.RAG.extractors.pdfminer_extractor import PdfMinerExtractor
from DashAI.back.models.RAG.extractors.pdfplumber_extractor import PdfPlumberExtractor
from DashAI.back.models.RAG.extractors.plain_text_extractor import PlainTextExtractor
from DashAI.back.models.RAG.extractors.pypdf2_extractor import PypdfExtractor

PDF_SAMPLE_TEXT = "Hello DashAI"


def _write_text_pdf(path, text: str = PDF_SAMPLE_TEXT) -> str:
    """Write a one-page PDF whose only content is ``text`` in Helvetica.

    Parameters
    ----------
    path : pathlib.Path
        Destination file, typically under ``tmp_path``.
    text : str
        Latin-1 encodable text to draw on the page.

    Returns
    -------
    str
        The path written, as a string.
    """
    stream = f"BT /F1 24 Tf 72 700 Td ({text}) Tj ET".encode("latin-1")
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
        b"/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>",
        b"<</Length %d>>stream\n%s\nendstream" % (len(stream), stream),
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
    ]
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


class TestBaseExtractor:
    def test_type_is_extractor(self):
        assert BaseExtractor.TYPE == "Extractor"

    def test_supported_file_types_default_empty(self):
        assert BaseExtractor.SUPPORTED_FILE_TYPES == []

    def test_get_metadata_returns_supported_types(self):
        class DummyExtractor(BaseExtractor):
            SUPPORTED_FILE_TYPES = ["pdf"]

            def extract(self, file_path):
                return "dummy"

        metadata = DummyExtractor.get_metadata()
        assert metadata["supported_file_types"] == ["pdf"]

    def test_config_object_inheritance(self):
        """BaseExtractor inherits from ConfigObject."""
        from DashAI.back.config_object import ConfigObject

        assert issubclass(BaseExtractor, ConfigObject)


class TestPlainTextExtractor:
    def test_supported_file_types(self):
        assert set(PlainTextExtractor.SUPPORTED_FILE_TYPES) >= {
            "txt",
            "md",
            "rst",
            "tex",
            "csv",
        }

    def test_extract_txt(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello world\n\nThis is a test.", encoding="utf-8")
        extractor = PlainTextExtractor()
        text = extractor.extract(str(file_path))
        assert text == "Hello world\n\nThis is a test."

    def test_extract_file_not_found(self):
        extractor = PlainTextExtractor()
        with pytest.raises(RAGDocumentParsingError, match="File not found"):
            extractor.extract("/nonexistent/path.txt")


class TestPypdfExtractor:
    def test_supported_file_types(self):
        assert PypdfExtractor.SUPPORTED_FILE_TYPES == ["pdf"]

    def test_get_metadata(self):
        metadata = PypdfExtractor.get_metadata()
        assert metadata["supported_file_types"] == ["pdf"]


class TestPdfMinerExtractor:
    def test_supported_file_types(self):
        assert PdfMinerExtractor.SUPPORTED_FILE_TYPES == ["pdf"]

    def test_get_metadata(self):
        metadata = PdfMinerExtractor.get_metadata()
        assert metadata["supported_file_types"] == ["pdf"]

    def test_schema_exposes_layout_params(self):
        schema = PdfMinerExtractor.get_schema()
        assert set(schema["properties"]) >= {
            "password",
            "line_margin",
            "char_margin",
            "boxes_flow",
            "detect_vertical",
        }

    def test_defaults(self):
        ext = PdfMinerExtractor()
        assert ext.password == ""
        assert ext.line_margin == 0.5
        assert ext.char_margin == 2.0
        assert ext.boxes_flow == 0.5
        assert ext.detect_vertical is False

    def test_custom_params(self):
        ext = PdfMinerExtractor(line_margin=0.1, boxes_flow=-1.0, detect_vertical=True)
        assert ext.line_margin == 0.1
        assert ext.boxes_flow == -1.0
        assert ext.detect_vertical is True

    def test_extract_text(self, tmp_path):
        pdf = _write_text_pdf(tmp_path / "miner.pdf")
        assert PdfMinerExtractor().extract(pdf) == PDF_SAMPLE_TEXT

    def test_extract_missing_file(self):
        with pytest.raises(RAGDocumentParsingError, match="pdfminer.six failed"):
            PdfMinerExtractor().extract("/nonexistent/path.pdf")


class TestPdfPlumberExtractor:
    def test_supported_file_types(self):
        assert PdfPlumberExtractor.SUPPORTED_FILE_TYPES == ["pdf"]

    def test_get_metadata(self):
        metadata = PdfPlumberExtractor.get_metadata()
        assert metadata["supported_file_types"] == ["pdf"]

    def test_schema_exposes_tolerances_and_tables(self):
        schema = PdfPlumberExtractor.get_schema()
        assert set(schema["properties"]) >= {
            "password",
            "x_tolerance",
            "y_tolerance",
            "layout",
            "extract_tables",
        }

    def test_defaults(self):
        ext = PdfPlumberExtractor()
        assert ext.password == ""
        assert ext.x_tolerance == 3.0
        assert ext.y_tolerance == 3.0
        assert ext.layout is False
        assert ext.extract_tables is False

    def test_custom_params(self):
        ext = PdfPlumberExtractor(x_tolerance=1.5, layout=True, extract_tables=True)
        assert ext.x_tolerance == 1.5
        assert ext.layout is True
        assert ext.extract_tables is True

    def test_extract_text(self, tmp_path):
        pdf = _write_text_pdf(tmp_path / "plumber.pdf")
        assert PdfPlumberExtractor().extract(pdf) == PDF_SAMPLE_TEXT

    def test_extract_text_with_tables_enabled(self, tmp_path):
        """A page with no table still yields its text, with no trailing blanks."""
        pdf = _write_text_pdf(tmp_path / "plumber_tables.pdf")
        assert PdfPlumberExtractor(extract_tables=True).extract(pdf) == PDF_SAMPLE_TEXT

    def test_render_table_blanks_empty_cells(self):
        rendered = PdfPlumberExtractor._render_table([["a", None], ["", "b"]])
        assert rendered == "a\t\n\tb"

    def test_extract_missing_file(self):
        with pytest.raises(RAGDocumentParsingError, match="pdfplumber failed"):
            PdfPlumberExtractor().extract("/nonexistent/path.pdf")


class TestExtractorSchemaRegistration:
    """Verify extractors are properly registered in the component registry."""

    def test_extractors_registered(self, client):
        """Remaining extractors appear in the registry under Extractor type."""
        resp = client.get("/api/v1/component/?type=Extractor")
        assert resp.status_code == 200
        names = {c["name"] for c in resp.json()}
        assert {
            "PypdfExtractor",
            "PdfMinerExtractor",
            "PdfPlumberExtractor",
            "PlainTextExtractor",
        }.issubset(names)

    def test_removed_extractors_absent(self, client):
        """PyMuPDF and EasyOCR extractors are gone from the registry."""
        resp = client.get("/api/v1/component/?type=Extractor")
        assert resp.status_code == 200
        names = {c["name"] for c in resp.json()}
        assert "PyMuPDFExtractor" not in names
        assert "EasyOCRExtractor" not in names

    def test_get_child_components(self, client):
        """getChildComponents('BaseExtractor', false) returns all extractors."""
        resp = client.get("/api/v1/component/BaseExtractor/children?recursive=false")
        assert resp.status_code == 200
        components = resp.json()
        names = {c["name"] for c in components}
        expected = {
            "PypdfExtractor",
            "PdfMinerExtractor",
            "PdfPlumberExtractor",
            "PlainTextExtractor",
        }
        assert expected.issubset(names)

    def test_pypdf_metadata_has_supported_types(self, client):
        """Registry metadata includes supported_file_types for frontend filtering."""
        resp = client.get("/api/v1/component/?type=Extractor")
        assert resp.status_code == 200
        pypdf_entry = next(
            (c for c in resp.json() if c["name"] == "PypdfExtractor"), None
        )
        assert pypdf_entry is not None
        assert pypdf_entry["metadata"]["supported_file_types"] == ["pdf"]


class TestPlainTextExtractorParams:
    def test_default_encoding(self):
        from DashAI.back.models.RAG.extractors.plain_text_extractor import (
            PlainTextExtractor,
        )

        ext = PlainTextExtractor()
        assert ext.encoding == "utf-8"

    def test_custom_encoding(self):
        from DashAI.back.models.RAG.extractors.plain_text_extractor import (
            PlainTextExtractor,
        )

        ext = PlainTextExtractor(encoding="latin-1")
        assert ext.encoding == "latin-1"

    def test_schema_has_encoding(self):
        from DashAI.back.models.RAG.extractors.plain_text_extractor import (
            PlainTextExtractor,
        )

        schema = PlainTextExtractor.get_schema()
        assert "encoding" in schema["properties"]


class TestPypdfExtractorParams:
    def test_default_strict(self):
        from DashAI.back.models.RAG.extractors.pypdf2_extractor import PypdfExtractor

        ext = PypdfExtractor()
        assert ext.strict is True

    def test_lenient_mode(self):
        from DashAI.back.models.RAG.extractors.pypdf2_extractor import PypdfExtractor

        ext = PypdfExtractor(strict=False)
        assert ext.strict is False

    def test_schema_has_strict(self):
        from DashAI.back.models.RAG.extractors.pypdf2_extractor import PypdfExtractor

        schema = PypdfExtractor.get_schema()
        assert "strict" in schema["properties"]
