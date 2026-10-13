"""The text view of a Data document that the RAG chunkers read."""

from DashAI.back.dataloaders.classes.dashai_document import (
    DashAIDocument,
    DocumentItem,
)
from DashAI.back.models.RAG.documents import Chunk, RAGDocument, TextSegment
from DashAI.back.types.value_types import Text

PAGE_ONE = "alpha beta gamma delta"
PAGE_TWO = "epsilon zeta eta theta"


def _two_page_document() -> RAGDocument:
    """Build a document with one segment per page.

    Returns
    -------
    RAGDocument
        Document 7 with ``PAGE_ONE`` on page 1 and ``PAGE_TWO`` on page 2.
    """
    return RAGDocument(
        id=7,
        name="two.pdf",
        segments=[TextSegment(PAGE_ONE, 1), TextSegment(PAGE_TWO, 2)],
    )


def test_text_joins_segments_in_reading_order():
    assert _two_page_document().get_text() == PAGE_ONE + "\n\n" + PAGE_TWO


def test_page_at_maps_offsets_to_their_segment_page():
    document = _two_page_document()
    second_start = len(PAGE_ONE) + len(RAGDocument.SEPARATOR)

    assert document.page_at(0) == 1
    assert document.page_at(len(PAGE_ONE) - 1) == 1
    assert document.page_at(second_start) == 2
    assert document.page_at(10_000) == 2


def test_page_at_is_none_without_segments():
    assert RAGDocument(id=1, name="empty.txt", segments=[]).page_at(0) is None


def test_from_dashai_document_keeps_text_items_and_pages():
    content = DashAIDocument.from_items(
        [DocumentItem(Text, PAGE_ONE, page=1), DocumentItem(Text, PAGE_TWO, page=2)]
    )

    document = RAGDocument.from_dashai_document(3, "two.pdf", content, "pdf")

    assert [segment.text for segment in document.segments] == [PAGE_ONE, PAGE_TWO]
    assert [segment.page for segment in document.segments] == [1, 2]
    assert (document.id, document.file_name, document.file_type) == (
        3,
        "two.pdf",
        "pdf",
    )


def test_a_chunk_has_no_page_unless_given_one():
    assert Chunk(id=None, document_id=1, document_position=0, text="x").page is None
    assert (
        Chunk(id=None, document_id=1, document_position=0, text="x", page=4).page == 4
    )
