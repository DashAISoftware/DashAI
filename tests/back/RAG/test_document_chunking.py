"""Chunkers split the text items of a DashAIDocument into chunk items."""

import io

from PIL import Image

from DashAI.back.dataloaders.classes.dashai_document import (
    DashAIDocument,
    DocumentItem,
)
from DashAI.back.dataloaders.classes.document_elements import CHUNK_KIND
from DashAI.back.models.RAG.chunking_models.character_chunk_model import (
    CharacterChunkModel,
)
from DashAI.back.models.RAG.chunking_models.recursive_character_chunk_model import (
    RecursiveCharacterChunkModel,
)
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Text

PAGE_ONE = "Alpha beta gamma delta."
PAGE_TWO = "Epsilon zeta eta theta."


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1)).save(buffer, "PNG")
    return buffer.getvalue()


def _document(with_image: bool = False) -> DashAIDocument:
    items = [DocumentItem(Text, PAGE_ONE, page=1)]
    if with_image:
        items.append(DocumentItem(DashAIImage, DashAIImage(bytes=_png()), page=1))
    items.append(DocumentItem(Text, PAGE_TWO, page=2))
    return DashAIDocument.from_items(items, metadata={"file_name": "two.pdf"})


def _character(chunk_size: int, chunk_overlap: int) -> CharacterChunkModel:
    return CharacterChunkModel(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def test_each_chunk_becomes_a_chunk_item():
    chunked = _character(30, 5).chunk(_document())

    items = chunked.items()
    assert [item.position for item in items] == list(range(len(items)))
    assert all(item.type is Text for item in items)
    assert all(item.kind == CHUNK_KIND for item in items)
    assert items[0].content.startswith("Alpha")
    assert chunked.metadata["chunker"] == "CharacterChunkModel"
    assert chunked.metadata["chunker_params"] == {"chunk_size": 30, "chunk_overlap": 5}


def test_a_chunk_spanning_two_items_names_both_sources_and_pages():
    chunked = _character(40, 1).chunk(_document())

    first = chunked.items()[0]
    assert first.attrs["sources"] == [0, 1]
    assert first.attrs["pages"] == [1, 2]
    assert first.page == 1


def test_images_are_ignored():
    chunked = _character(1000, 1).chunk(_document(with_image=True))

    items = chunked.items()
    assert len(items) == 1
    assert items[0].content == PAGE_ONE + "\n\n" + PAGE_TWO
    assert items[0].attrs["sources"] == [0, 2]
    assert chunked.count(DashAIImage) == 0


def test_a_document_without_text_gives_no_chunks():
    document = DashAIDocument.from_items(
        [DocumentItem(DashAIImage, DashAIImage(bytes=_png()), page=1)]
    )

    assert _character(30, 5).chunk(document).count(Text) == 0


def test_pages_follow_the_items_even_when_text_is_rewritten():
    model = RecursiveCharacterChunkModel(
        chunk_size=12,
        chunk_overlap=0,
        separators=["\n\n", " ", ""],
    )

    items = model.chunk(_document()).items()

    assert all(item.page in (1, 2) for item in items)
    pages = [item.page for item in items]
    assert pages == sorted(pages)
    assert items[-1].page == 2
