import pyarrow as pa
import pytest

from DashAI.back.dataloaders.classes.dashai_data import DashAIData
from DashAI.back.dataloaders.classes.dashai_dataset import (
    DashAIDataset,
    get_arrow_table,
)
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


def test_as_dataset_exposes_typed_content_column():
    dataset = _sample_document().as_dataset(Text)

    assert isinstance(dataset, DashAIDataset)
    assert dataset.column_names == ["content", "position", "page", "kind", "attrs"]
    assert get_arrow_table(dataset).column("content").to_pylist() == [
        "Intro paragraph",
        "Second page text",
    ]
    assert dataset.types["content"].to_string()["type"] == "Text"
    assert dataset.types["position"].to_string()["type"] == "Integer"


def test_as_dataset_of_images_is_image_typed():
    dataset = _sample_document().as_dataset(DashAIImage)

    assert dataset.types["content"].to_string() == {"type": "Image", "dtype": "struct"}
    assert len(dataset) == 1


def test_as_dataset_of_absent_type_is_empty():
    document = DashAIDocument.from_items([DocumentItem(Text, "only text")])

    dataset = document.as_dataset(DashAIImage)

    assert len(dataset) == 0
    assert dataset.column_names == ["content", "position", "page", "kind", "attrs"]


def test_with_content_replaces_one_type_and_keeps_order():
    document = _sample_document()
    table = get_arrow_table(document.as_dataset(Text))
    upper = table.set_column(
        0, "content", pa.array([s.upper() for s in document[Text]])
    )

    updated = document.with_content(Text, DashAIDataset(upper))

    assert updated[Text] == ["INTRO PARAGRAPH", "SECOND PAGE TEXT"]
    assert [i.position for i in updated.items()] == [0, 1, 2]
    assert [i.page for i in updated.items()] == [1, 1, 2]
    assert len(updated[DashAIImage]) == 1
    assert document[Text] == ["Intro paragraph", "Second page text"]


def _heading_document():
    return DashAIDocument.from_items(
        [DocumentItem(Text, "Title", kind="heading", attrs={"level": 1})]
    )


def _with_attrs(document, attrs):
    table = get_arrow_table(document.as_dataset(Text)).drop_columns(["attrs"])
    return table.append_column("attrs", pa.array([attrs], type=pa.string()))


def test_with_content_takes_attrs_from_the_replacement():
    document = _heading_document()

    updated = document.with_content(
        Text, DashAIDataset(_with_attrs(document, '{"level": 3}'))
    )

    assert updated.items()[0].attrs == {"level": 3}


def test_with_content_without_attrs_keeps_the_current_ones():
    document = _heading_document()
    table = get_arrow_table(document.as_dataset(Text)).drop_columns(["attrs"])

    updated = document.with_content(Text, DashAIDataset(table))

    assert updated.items()[0].attrs == {"level": 1}


def test_with_content_rejects_attrs_the_kind_does_not_take():
    document = _heading_document()

    with pytest.raises(ValueError, match="does not take attributes"):
        document.with_content(
            Text, DashAIDataset(_with_attrs(document, '{"level": 1, "rows": []}'))
        )


def test_with_content_rejects_changed_row_count():
    document = _sample_document()
    table = get_arrow_table(document.as_dataset(Text)).slice(0, 1)

    with pytest.raises(ValueError, match="positions"):
        document.with_content(Text, DashAIDataset(table))


def test_with_content_rejects_missing_columns():
    document = _sample_document()

    with pytest.raises(ValueError, match="missing columns"):
        document.with_content(Text, DashAIDataset(pa.table({"content": ["a", "b"]})))


def test_with_content_honours_filtered_plain_dataset():
    document = _sample_document()
    filtered = (
        document.as_dataset(Text)
        .map(lambda row: {"content": row["content"].upper()})
        .filter(lambda row: row["position"] != 0)
    )

    with pytest.raises(ValueError, match="positions"):
        document.with_content(Text, filtered)


def test_with_content_accepts_mapped_plain_dataset():
    document = _sample_document()
    mapped = document.as_dataset(Text).map(
        lambda row: {"content": row["content"].upper()}
    )

    updated = document.with_content(Text, mapped)

    assert updated[Text] == ["INTRO PARAGRAPH", "SECOND PAGE TEXT"]


def _text_replacement(document, contents=None, pages=None):
    table = get_arrow_table(document.as_dataset(Text))
    if contents is not None:
        table = table.set_column(0, "content", pa.array(contents, pa.string()))
    if pages is not None:
        table = table.set_column(2, "page", pa.array(pages, pa.int64()))
    return DashAIDataset(table)


def test_with_content_rejects_null_text():
    document = _sample_document()

    with pytest.raises(ValueError, match="null"):
        document.with_content(Text, _text_replacement(document, contents=[None, "Y"]))


@pytest.mark.parametrize("page", [0, -5])
def test_with_content_rejects_invalid_pages(page):
    document = _sample_document()

    with pytest.raises(ValueError, match="page"):
        document.with_content(Text, _text_replacement(document, pages=[page, 2]))


def test_constructor_rejects_image_without_bytes():
    image_table = _sample_document().tables[DashAIImage]
    no_bytes = image_table.set_column(
        0,
        "content",
        pa.array([{"bytes": None, "path": "x.png"}], DashAIImage.pa_type),
    )

    with pytest.raises(ValueError, match="no bytes"):
        DashAIDocument({DashAIImage: no_bytes})


def test_constructor_rejects_null_positions():
    text_table = _sample_document().tables[Text]
    nulls = text_table.set_column(1, "position", pa.array([None, 1], pa.int64()))

    with pytest.raises(ValueError, match="positions"):
        DashAIDocument({Text: nulls})


def test_constructor_rejects_wrong_content_type_for_key():
    text_table = _sample_document().tables[Text]

    with pytest.raises(ValueError, match="content column"):
        DashAIDocument({DashAIImage: text_table})


def _structured_document():
    return DashAIDocument.from_items(
        [
            DocumentItem(Text, "Report", page=1, kind="title"),
            DocumentItem(Text, "Intro", page=1, kind="heading", attrs={"level": 2}),
            DocumentItem(Text, "First point", page=1, kind="list_item"),
            DocumentItem(DashAIImage, _image("fig.png"), page=1, attrs={"alt": "Fig"}),
            DocumentItem(
                Text, "a\tb", page=2, kind="table", attrs={"rows": [["a", "b"]]}
            ),
            DocumentItem(Text, "Plain text", page=2),
        ]
    )


def test_items_keep_kinds_and_attrs_in_reading_order():
    items = _structured_document().items()

    assert [(item.kind, item.type) for item in items] == [
        ("title", Text),
        ("heading", Text),
        ("list_item", Text),
        ("image", DashAIImage),
        ("table", Text),
        ("paragraph", Text),
    ]
    assert items[1].attrs == {"level": 2}
    assert items[2].attrs == {"ordered": False, "depth": 0}
    assert items[3].attrs == {"alt": "Fig"}
    assert items[4].attrs == {"rows": [["a", "b"]], "header": False}
    assert items[5].attrs == {}


def test_from_items_rejects_an_invalid_element():
    with pytest.raises(ValueError, match="Unknown element kind"):
        DashAIDocument.from_items([DocumentItem(Text, "x", kind="sidebar")])
    with pytest.raises(ValueError, match="requires attribute 'level'"):
        DashAIDocument.from_items([DocumentItem(Text, "x", kind="heading")])
    with pytest.raises(ValueError, match="holds Image"):
        DashAIDocument.from_items([DocumentItem(Text, "x", kind="image")])


def test_as_dataset_exposes_kind_and_attrs():
    dataset = _structured_document().as_dataset(Text)
    table = get_arrow_table(dataset)

    assert table.column("kind").to_pylist() == [
        "title",
        "heading",
        "list_item",
        "table",
        "paragraph",
    ]
    assert dataset.types["kind"].to_string()["type"] == "Text"
    assert dataset.types["attrs"].to_string()["type"] == "Text"


def test_with_content_keeps_kinds_and_attrs():
    document = _structured_document()
    table = get_arrow_table(document.as_dataset(Text))
    upper = table.set_column(
        0, "content", pa.array([s.upper() for s in document[Text]])
    ).drop_columns(["kind", "attrs"])

    updated = document.with_content(Text, DashAIDataset(upper))

    assert [item.kind for item in updated.items()] == [
        item.kind for item in document.items()
    ]
    assert updated.items()[1].attrs == {"level": 2}
    assert updated.items()[1].content == "INTRO"


def test_constructor_rejects_a_table_with_an_invalid_kind():
    table = _structured_document().tables[Text]
    broken = table.set_column(
        table.schema.get_field_index("kind"),
        "kind",
        pa.array(["sidebar"] * table.num_rows, pa.string()),
    )

    with pytest.raises(ValueError, match="Unknown element kind"):
        DashAIDocument({Text: broken})
