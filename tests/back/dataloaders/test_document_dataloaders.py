"""Tests for the document dataloaders."""

import pytest
from pydantic import ValidationError

from DashAI.back.dataloaders.classes.document_dataloader import DocumentLoaderError
from DashAI.back.dataloaders.classes.pdfminer_document_dataloader import (
    PdfMinerDocumentDataLoader,
)
from DashAI.back.dataloaders.classes.pdfplumber_document_dataloader import (
    PdfPlumberDocumentDataLoader,
)
from DashAI.back.dataloaders.classes.plain_text_document_dataloader import (
    PlainTextDocumentDataLoader,
)
from DashAI.back.dataloaders.classes.pypdf_document_dataloader import (
    PypdfDocumentDataLoader,
)
from DashAI.back.dependencies.config_builder import get_initial_components
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Text
from tests.back.dataloaders.document_samples import (
    image_pdf_bytes,
    write_mixed_pdf,
    write_text_pdf,
)

PDF_LOADERS = [
    PypdfDocumentDataLoader,
    PdfPlumberDocumentDataLoader,
    PdfMinerDocumentDataLoader,
]
ALL_LOADERS = [*PDF_LOADERS, PlainTextDocumentDataLoader]


@pytest.mark.parametrize("loader_class", PDF_LOADERS)
def test_pdf_loaders_emit_one_text_item_per_page(tmp_path, loader_class):
    pdf = write_text_pdf(tmp_path / "pages.pdf", ["Alpha", "", "Charlie"])
    document = loader_class().load_document(pdf, {})
    assert [
        (item.type, item.content, item.page, item.position) for item in document.items()
    ] == [(Text, "Alpha", 1, 0), (Text, "Charlie", 3, 1)]
    assert document.metadata["n_pages"] == 3
    assert document.metadata["file_type"] == "pdf"
    assert document.metadata["dataloader"] == loader_class.__name__


@pytest.mark.parametrize("loader_class", PDF_LOADERS)
def test_pdf_loaders_wrap_parse_errors(tmp_path, loader_class):
    with pytest.raises(DocumentLoaderError):
        loader_class().load_document(str(tmp_path / "missing.pdf"), {})


def test_pypdf_loader_keeps_text_and_images_in_reading_order(tmp_path):
    pdf = write_mixed_pdf(tmp_path / "mixed.pdf")
    document = PypdfDocumentDataLoader().load_document(pdf, {"extract_images": True})
    assert [(item.type, item.page, item.position) for item in document.items()] == [
        (Text, 1, 0),
        (DashAIImage, 1, 1),
        (Text, 2, 2),
    ]
    assert document[Text] == ["Alpha", "Bravo"]
    assert document[DashAIImage][0].to_pil().size == (8, 8)


def test_pypdf_loader_ignores_images_by_default(tmp_path):
    path = tmp_path / "image.pdf"
    path.write_bytes(image_pdf_bytes())
    document = PypdfDocumentDataLoader().load_document(str(path), {})
    assert document.count(DashAIImage) == 0
    assert document.metadata["dataloader_params"] == {
        "strict": True,
        "extract_images": False,
    }


def test_pdfplumber_loader_puts_tables_after_their_page_text(tmp_path, monkeypatch):
    monkeypatch.setattr(
        PdfPlumberDocumentDataLoader,
        "_read_pages",
        lambda self, file_path, params: [["Page one", "a\tb"], [], ["Page three"]],
    )
    document = PdfPlumberDocumentDataLoader().load_document(
        str(tmp_path / "t.pdf"), {"extract_tables": True}
    )
    assert [(item.content, item.page) for item in document.items()] == [
        ("Page one", 1),
        ("a\tb", 1),
        ("Page three", 3),
    ]


def test_pdfplumber_render_table_blanks_empty_cells():
    rendered = PdfPlumberDocumentDataLoader.render_table([["a", None], ["", "b"]])
    assert rendered == "a\t\n\tb"


def test_plain_text_loader_emits_one_item_per_paragraph(tmp_path):
    path = tmp_path / "notes.md"
    path.write_bytes(b"# Title\n\nFirst line\nstill first.\n\n\n  \nSecond.\n")
    document = PlainTextDocumentDataLoader().load_document(str(path), {})
    assert document[Text] == ["# Title", "First line\nstill first.", "Second."]
    assert all(item.page is None for item in document.items())
    assert document.metadata["n_pages"] is None


def test_plain_text_loader_honours_and_reports_the_encoding(tmp_path):
    path = tmp_path / "latin.txt"
    path.write_bytes("Ñandú".encode("latin-1"))
    loader = PlainTextDocumentDataLoader()
    assert loader.load_document(str(path), {"encoding": "latin-1"})[Text] == ["Ñandú"]
    with pytest.raises(DocumentLoaderError, match="utf-8"):
        loader.load_document(str(path), {})


def test_params_are_merged_with_defaults_and_validated(tmp_path):
    pdf = write_text_pdf(tmp_path / "one.pdf", ["Alpha"])
    document = PdfMinerDocumentDataLoader().load_document(pdf, {"line_margin": 0.1})
    assert document.metadata["dataloader_params"] == {
        "password": "",
        "line_margin": 0.1,
        "char_margin": 2.0,
        "boxes_flow": 0.5,
        "detect_vertical": False,
    }
    with pytest.raises(ValidationError):
        PdfMinerDocumentDataLoader().resolve_params({"boxes_flow": 5.0})


def test_loaders_are_registered_document_kind_dataloaders():
    components = get_initial_components()
    for loader_class in ALL_LOADERS:
        assert loader_class in components
        assert loader_class.TYPE == "DataLoader"
        assert loader_class.get_metadata()["data_kinds"] == ["document"]


def test_loaders_do_not_depend_on_rag():
    import sys

    for loader_class in ALL_LOADERS:
        source = sys.modules[loader_class.__module__].__file__
        with open(source, encoding="utf-8") as handle:
            assert "models.RAG" not in handle.read()
