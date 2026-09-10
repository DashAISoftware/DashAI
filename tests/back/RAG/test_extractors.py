"""Tests for document extractors."""

import pytest

from DashAI.back.models.RAG.exceptions import RAGDocumentParsingError
from DashAI.back.models.RAG.extractors.base_extractor import BaseExtractor
from DashAI.back.models.RAG.extractors.plain_text_extractor import PlainTextExtractor
from DashAI.back.models.RAG.extractors.pymupdf_extractor import PyMuPDFExtractor
from DashAI.back.models.RAG.extractors.pypdf2_extractor import PypdfExtractor


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


class TestPyMuPDFExtractor:
    def test_supported_file_types(self):
        assert PyMuPDFExtractor.SUPPORTED_FILE_TYPES == ["pdf"]

    def test_get_metadata(self):
        metadata = PyMuPDFExtractor.get_metadata()
        assert metadata["supported_file_types"] == ["pdf"]


class TestEasyOCRExtractor:
    """Tests for EasyOCR extractor schema and metadata."""

    def test_supported_file_types(self):
        from DashAI.back.models.RAG.extractors.easyocr_extractor import EasyOCRExtractor

        assert EasyOCRExtractor.SUPPORTED_FILE_TYPES == ["pdf"]

    def test_schema_has_languages_and_gpu(self):
        """Schema exposes languages and gpu parameters for the frontend."""
        from DashAI.back.models.RAG.extractors.easyocr_extractor import EasyOCRExtractor

        schema = EasyOCRExtractor.get_schema()
        assert "properties" in schema
        assert "languages" in schema["properties"]
        assert "gpu" in schema["properties"]

    def test_get_metadata(self):
        from DashAI.back.models.RAG.extractors.easyocr_extractor import EasyOCRExtractor

        metadata = EasyOCRExtractor.get_metadata()
        assert metadata["supported_file_types"] == ["pdf"]

    def test_instantiate_with_defaults(self):
        """Should work with no params (uses defaults)."""
        from DashAI.back.models.RAG.extractors.easyocr_extractor import EasyOCRExtractor

        ext = EasyOCRExtractor()
        assert ext.languages == ["en"]
        assert ext.gpu is True

    def test_instantiate_with_params(self):
        """Custom params should be stored on the instance."""
        from DashAI.back.models.RAG.extractors.easyocr_extractor import EasyOCRExtractor

        ext = EasyOCRExtractor(languages=["es", "fr"], gpu=False)
        assert ext.languages == ["es", "fr"]
        assert ext.gpu is False

    def test_instantiate_with_partial_params(self):
        """Missing params should use defaults."""
        from DashAI.back.models.RAG.extractors.easyocr_extractor import EasyOCRExtractor

        ext = EasyOCRExtractor(languages=["de"])
        assert ext.languages == ["de"]
        assert ext.gpu is True  # default

    def test_config_object_inheritance(self):
        """EasyOCRExtractor inherits from ConfigObject."""
        from DashAI.back.config_object import ConfigObject
        from DashAI.back.models.RAG.extractors.easyocr_extractor import EasyOCRExtractor

        assert issubclass(EasyOCRExtractor, ConfigObject)

    def test_type_is_extractor(self):
        from DashAI.back.models.RAG.extractors.easyocr_extractor import EasyOCRExtractor

        assert EasyOCRExtractor.TYPE == "Extractor"


class TestExtractorSchemaRegistration:
    """Verify extractors are properly registered in the component registry."""

    def test_easyocr_registered(self, client):
        """EasyOCRExtractor should appear in component registry under Extractor type."""
        resp = client.get("/api/v1/component/?type=Extractor")
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert "EasyOCRExtractor" in names

    def test_get_child_components(self, client):
        """getChildComponents('BaseExtractor', false) returns all extractors."""
        resp = client.get("/api/v1/component/BaseExtractor/children?recursive=false")
        assert resp.status_code == 200
        components = resp.json()
        names = {c["name"] for c in components}
        expected = {
            "PypdfExtractor",
            "PyMuPDFExtractor",
            "PlainTextExtractor",
            "EasyOCRExtractor",
        }
        assert expected.issubset(names)

    def test_easyocr_schema_in_registry(self, client):
        """Registry entry includes schema with languages and gpu params."""
        resp = client.get("/api/v1/component/?type=Extractor")
        assert resp.status_code == 200
        easyocr_entry = next(
            (c for c in resp.json() if c["name"] == "EasyOCRExtractor"), None
        )
        assert easyocr_entry is not None
        assert easyocr_entry["configurable_object"] is True
        schema = easyocr_entry["schema"]
        assert "languages" in schema.get("properties", {})
        assert "gpu" in schema.get("properties", {})

    def test_easyocr_metadata_has_supported_types(self, client):
        """Registry metadata includes supported_file_types for frontend filtering."""
        resp = client.get("/api/v1/component/?type=Extractor")
        assert resp.status_code == 200
        easyocr_entry = next(
            (c for c in resp.json() if c["name"] == "EasyOCRExtractor"), None
        )
        assert easyocr_entry is not None
        assert easyocr_entry["metadata"]["supported_file_types"] == ["pdf"]


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


class TestPyMuPDFExtractorParams:
    def test_default_no_password(self):
        from DashAI.back.models.RAG.extractors.pymupdf_extractor import PyMuPDFExtractor

        ext = PyMuPDFExtractor()
        assert ext.password is None

    def test_with_password(self):
        from DashAI.back.models.RAG.extractors.pymupdf_extractor import PyMuPDFExtractor

        ext = PyMuPDFExtractor(password="secret123")
        assert ext.password == "secret123"

    def test_schema_has_password(self):
        from DashAI.back.models.RAG.extractors.pymupdf_extractor import PyMuPDFExtractor

        schema = PyMuPDFExtractor.get_schema()
        assert "password" in schema["properties"]
