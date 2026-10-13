import pytest

from DashAI.back.converters.document.item_filter import DocumentItemFilter
from DashAI.back.converters.document.text_splitter import TextSplitter
from DashAI.back.dataloaders.classes.document_items import (
    ItemFilter,
    apply_converter_to_document,
)
from DashAI.back.types.value_types import Text
from tests.back.document_fixtures import build_document, image, text

TABLE = text("a\tb\nc\td", kind="table", rows=[["a", "b"], ["c", "d"]])


def _layout(document):
    return [
        (item.type.display_name(), item.kind, item.page, item.content)
        for item in document.items()
        if item.type is Text
    ]


def _filter(document, scope=None, **kwargs):
    return apply_converter_to_document(
        document,
        lambda: DocumentItemFilter(**kwargs),
        {"Text": scope or ItemFilter()},
    )


def test_short_and_long_items_are_dropped():
    document = build_document([" a ", "fine", "far too long", "  "])
    converted = _filter(document, min_characters=2, max_characters=10)
    assert converted[Text] == ["fine"]


def test_kept_items_keep_kind_attrs_and_tables():
    document = build_document([text("Intro", kind="heading", level=2), TABLE, "x"])
    converted = _filter(document, min_characters=2)
    items = converted.items()
    assert [(item.kind, item.attrs) for item in items] == [
        ("heading", {"level": 2}),
        ("table", {"rows": [["a", "b"], ["c", "d"]], "header": False}),
    ]


def test_items_matching_a_pattern_are_dropped():
    document = build_document(["Page 1", "Body text", "Page 22"])
    converted = _filter(document, rule="Matching the pattern", pattern=r"^Page \d+$")
    assert converted[Text] == ["Body text"]


def test_only_items_matching_a_pattern_are_kept():
    document = build_document(["keep me", "drop", "keep too"])
    converted = _filter(document, rule="Not matching the pattern", pattern="keep")
    assert converted[Text] == ["keep me", "keep too"]


def test_every_selected_item_drops_the_scope():
    document = build_document(
        [text("Header", kind="page_header"), "body", text("1", kind="page_footer")]
    )
    converted = _filter(
        document,
        scope=ItemFilter(["page_header", "page_footer"]),
        rule="Every selected item",
    )
    assert converted[Text] == ["body"]
    assert [item.position for item in converted.items()] == [0]


def test_every_selected_image_can_be_dropped():
    converted = apply_converter_to_document(
        build_document(["a", image(), "b"]),
        lambda: DocumentItemFilter(rule="Every selected item"),
        {"Image": ItemFilter()},
    )
    assert converted.types == [Text]


def test_text_rules_are_refused_on_images():
    with pytest.raises(ValueError, match="Every selected item"):
        apply_converter_to_document(
            build_document([image()]), DocumentItemFilter, {"Image": ItemFilter()}
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"rule": "Odd ones"}, "Unknown rule"),
        ({"min_characters": 5, "max_characters": 2}, "below the minimum"),
        ({"rule": "Matching the pattern"}, "Write a pattern"),
        ({"rule": "Matching the pattern", "pattern": "("}, "not valid"),
    ],
)
def test_bad_filters_are_refused(kwargs, message):
    with pytest.raises(ValueError, match=message):
        DocumentItemFilter(**kwargs)


def test_sentences_become_items_with_the_source_kind_and_page():
    document = build_document(
        [
            text("Title", kind="title"),
            text('He said "Hi." Then left! Why? End', kind="list_item", page=2),
        ]
    )
    converted = apply_converter_to_document(
        document, TextSplitter, {"Text": ItemFilter(["list_item"])}
    )
    assert _layout(converted) == [
        ("Text", "title", 1, "Title"),
        ("Text", "list_item", 2, 'He said "Hi."'),
        ("Text", "list_item", 2, "Then left!"),
        ("Text", "list_item", 2, "Why?"),
        ("Text", "list_item", 2, "End"),
    ]


def test_a_blank_line_also_ends_a_sentence():
    assert TextSplitter().split("no stop here\n\nnext one") == [
        "no stop here",
        "next one",
    ]


def test_lines_and_paragraphs_are_cut_on_line_breaks():
    value = "one\ntwo\n\n  \nthree\r\nfour"
    assert TextSplitter(split_by="Lines").split(value) == [
        "one",
        "two",
        "three",
        "four",
    ]
    assert TextSplitter(split_by="Paragraphs").split(value) == [
        "one\ntwo",
        "three\r\nfour",
    ]


def test_pieces_of_a_table_are_paragraphs():
    converted = apply_converter_to_document(
        build_document([TABLE]),
        lambda: TextSplitter(split_by="Lines"),
        {"Text": ItemFilter()},
    )
    assert [(item.kind, item.attrs, item.content) for item in converted.items()] == [
        ("paragraph", {}, "a\tb"),
        ("paragraph", {}, "c\td"),
    ]


def test_an_unknown_split_is_refused():
    with pytest.raises(ValueError, match="Unknown split"):
        TextSplitter(split_by="Words")


def test_structure_converters_run_on_documents_only():
    for converter in (DocumentItemFilter, TextSplitter):
        metadata = converter.get_metadata()
        assert metadata["data_kinds"] == ["document"]
        assert metadata["changes_row_count"] is True
        assert metadata["category"].en == "Document Processing"
