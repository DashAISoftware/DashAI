import pytest

from DashAI.back.dataloaders.classes.dashai_data import DashAIData
from DashAI.back.dataloaders.classes.dashai_document import (
    DashAIDocument,
    DocumentItem,
)
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Integer, Text

PNG_BYTES = b"\x89PNG\r\n\x1a\nfake"


def _image(name="a.png"):
    return DashAIImage(bytes=PNG_BYTES, path=name)


def _sample_document():
    return DashAIDocument.from_items(
        [
            DocumentItem(Text, "Intro paragraph", page=1),
            DocumentItem(DashAIImage, _image("figure-1.png"), page=1),
            DocumentItem(Text, "Second page text", page=2),
        ],
        metadata={"file_name": "report.pdf", "file_type": "pdf"},
    )


def test_document_is_dashai_data():
    document = _sample_document()

    assert isinstance(document, DashAIData)
    assert DashAIDocument.data_kind() == "document"


def test_contents_are_split_by_type():
    document = _sample_document()

    assert document[Text] == ["Intro paragraph", "Second page text"]
    images = document[DashAIImage]
    assert len(images) == 1
    assert images[0].bytes == PNG_BYTES
    assert images[0].path == "figure-1.png"
    assert document.types == [Text, DashAIImage]
    assert document.count(Text) == 2
    assert document.content_counts == {"Text": 2, "Image": 1}
    assert document.metadata["file_name"] == "report.pdf"


def test_items_keep_reading_order_and_pages():
    items = _sample_document().items()

    assert [item.type for item in items] == [Text, DashAIImage, Text]
    assert [item.position for item in items] == [0, 1, 2]
    assert [item.page for item in items] == [1, 1, 2]
    assert items[2].content == "Second page text"


MIXED_ORDER = [Text, DashAIImage, Text, DashAIImage, DashAIImage, Text]


def _mixed_document():
    items = []
    for index, content_type in enumerate(MIXED_ORDER):
        if content_type is Text:
            items.append(DocumentItem(Text, f"text {index}", page=1 + index // 3))
        else:
            items.append(
                DocumentItem(
                    DashAIImage, _image(f"img-{index}.png"), page=1 + index // 3
                )
            )
    return DashAIDocument.from_items(items)


def test_interleaved_order_is_kept():
    items = _mixed_document().items()

    assert [item.type for item in items] == MIXED_ORDER
    assert [item.position for item in items] == list(range(6))
    assert [item.content for item in items if item.type is Text] == [
        "text 0",
        "text 2",
        "text 5",
    ]
    assert [item.content.path for item in items if item.type is DashAIImage] == [
        "img-1.png",
        "img-3.png",
        "img-4.png",
    ]


def test_absent_type_returns_empty_list():
    document = DashAIDocument.from_items([DocumentItem(Text, "only text")])

    assert document[DashAIImage] == []
    assert document.count(DashAIImage) == 0
    assert document.types == [Text]


def test_empty_document():
    document = DashAIDocument.from_items([])

    assert document.types == []
    assert document.items() == []
    assert document.content_counts == {}


def test_unsupported_type_is_rejected():
    with pytest.raises(TypeError, match="Unsupported content type"):
        DashAIDocument.from_items([DocumentItem(Integer, "3")])


def test_text_content_must_be_str():
    with pytest.raises(TypeError, match="Text content must be str"):
        DashAIDocument.from_items([DocumentItem(Text, 42)])


def test_image_content_needs_bytes():
    with pytest.raises(TypeError, match="Image content must be a DashAIImage"):
        DashAIDocument.from_items([DocumentItem(DashAIImage, "a.png")])
    with pytest.raises(ValueError, match="has no bytes"):
        DashAIDocument.from_items([DocumentItem(DashAIImage, DashAIImage())])


@pytest.mark.parametrize("page", [0, -1, 1.5])
def test_invalid_page_is_rejected(page):
    with pytest.raises(ValueError, match="page"):
        DashAIDocument.from_items([DocumentItem(Text, "x", page=page)])


def test_getitem_rejects_unsupported_type():
    with pytest.raises(TypeError, match="Unsupported content type"):
        _sample_document()[Integer]


def test_colliding_positions_across_types_are_rejected():
    tables = _sample_document().tables
    image_table = tables[DashAIImage]
    text_table = tables[Text]
    colliding = image_table.set_column(
        image_table.schema.get_field_index("position"),
        "position",
        text_table.column("position").slice(0, 1),
    )

    with pytest.raises(ValueError, match="positions"):
        DashAIDocument({Text: text_table, DashAIImage: colliding})
