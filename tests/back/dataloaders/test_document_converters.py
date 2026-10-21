import json

import pyarrow as pa
import pytest

from DashAI.back.converters.base_converter import BaseConverter, BaseConverterSchema
from DashAI.back.converters.document_converter import DocumentConverter
from DashAI.back.core.data_kinds import DATASET, DOCUMENT, supports_data_kind
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.dataloaders.classes.dashai_document import (
    load_document,
    save_document,
)
from DashAI.back.dataloaders.classes.document_items import (
    ItemFilter,
    apply_converter_to_document,
)
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Integer, Text
from tests.back.document_fixtures import build_document, image, text

TABLE = text("a\tb", kind="table", rows=[["a", "b"]])


def _layout(document):
    return [
        (item.position, item.type.display_name(), item.kind, item.page)
        for item in document.items()
    ]


def _image_values(count):
    return pa.array([{"bytes": b"x", "path": None}] * count, type=DashAIImage.pa_type)


class _Converter(BaseConverter):
    SCHEMA = BaseConverterSchema
    seen = []

    def get_output_type(self, column_name=None):
        return Text(arrow_type=pa.string())

    def fit(self, x, y=None):
        return self

    def _values(self, x):
        values = x.arrow_table.column(0).to_pylist()
        type(self).seen = values
        return values


class _ToImage(_Converter):
    def get_output_type(self, column_name=None):
        return DashAIImage()

    def transform(self, x, y=None):
        values = _image_values(len(self._values(x)))
        return DashAIDataset(pa.table({"Text": values}), types={"Text": DashAIImage()})


class _SaysTextMakesImages(_ToImage):
    def get_output_type(self, column_name=None):
        return Text(arrow_type=pa.string())


class _Ocr(_Converter):
    OUTPUT_KIND = "caption"

    def transform(self, x, y=None):
        values = [f"read {index}" for index in range(len(self._values(x)))]
        return DashAIDataset(
            pa.table({"Image": pa.array(values, type=pa.string())}),
            types={"Image": Text(arrow_type=pa.string())},
        )


class _WrongKindOcr(_Ocr):
    OUTPUT_KIND = "image"


class _Counter(_Converter):
    def transform(self, x, y=None):
        values = pa.array([1] * len(x), type=pa.int64())
        return DashAIDataset(
            pa.table({"Image": values}), types={"Image": Integer(arrow_type=pa.int64())}
        )


def _items(contents, sources, content_type=Text, kinds=None, attrs=None):
    if content_type is DashAIImage:
        content = _image_values(len(contents))
        types = {"content": DashAIImage()}
    else:
        content = pa.array(contents, type=pa.string())
        types = {"content": Text(arrow_type=pa.string())}
    columns = {"content": content, "source": pa.array(sources, type=pa.int64())}
    if kinds is not None:
        columns["kind"] = pa.array(kinds, type=pa.string())
    if attrs is not None:
        columns["attrs"] = pa.array(attrs, type=pa.string())
    return DashAIDataset(pa.table(columns), types=types)


class _Items(DocumentConverter):
    SCHEMA = BaseConverterSchema

    def get_output_type(self, column_name=None):
        return Text(arrow_type=pa.string())

    def fit(self, x, y=None):
        return self


class _Sentences(_Items):
    def transform(self, x, y=None):
        contents, sources = [], []
        for index, value in enumerate(x.arrow_table.column(0).to_pylist()):
            for line in value.split("\n"):
                contents.append(line)
                sources.append(index)
        return _items(contents, sources)


class _DropShort(_Items):
    def transform(self, x, y=None):
        values = x.arrow_table.column(0).to_pylist()
        kept = [index for index, value in enumerate(values) if len(value) > 3]
        return _items([values[index] for index in kept], kept)


class _DropAll(_Items):
    def transform(self, x, y=None):
        return _items([], [], content_type=DashAIImage)


class _Describe(_Items):
    keep_source = True

    def transform(self, x, y=None):
        count = len(x)
        return _items(
            [f"image {index}" for index in range(count)],
            list(range(count)),
            kinds=["caption"] * count,
        )


class _Headings(_Items):
    def transform(self, x, y=None):
        count = len(x)
        return _items(
            x.arrow_table.column(0).to_pylist(),
            list(range(count)),
            kinds=["heading"] * count,
            attrs=['{"level": 3}'] * count,
        )


class _BadSource(_Items):
    def transform(self, x, y=None):
        return _items(["a"], [len(x)])


class _NoSource(_Items):
    def transform(self, x, y=None):
        return DashAIDataset(
            pa.table({"content": pa.array(["a"])}),
            types={"content": Text(arrow_type=pa.string())},
        )


class _Numbers(_Items):
    def transform(self, x, y=None):
        return DashAIDataset(
            pa.table({"content": pa.array([1]), "source": pa.array([0])}),
            types={"content": Integer(arrow_type=pa.int64())},
        )


class _DatasetDeclared(_Items):
    metadata = {"data_kinds": [DATASET, DOCUMENT], "allowed_types": [Text]}


def test_text_items_become_images_in_place():
    document = build_document(
        [text("Report", kind="title"), text("Results", kind="heading", level=2)]
    )
    converted = apply_converter_to_document(
        document, _ToImage, {"Text": ItemFilter(["heading"])}
    )
    assert _layout(converted) == [(0, "Text", "title", 1), (1, "Image", "image", 1)]
    assert converted.items()[1].attrs == {}


def test_an_ocr_turns_images_into_text_with_its_output_kind():
    document = build_document(["intro", image(page=2), text("end", page=2)])
    converted = apply_converter_to_document(document, _Ocr, {"Image": ItemFilter()})
    assert _layout(converted) == [
        (0, "Text", "paragraph", 1),
        (1, "Text", "caption", 2),
        (2, "Text", "paragraph", 2),
    ]
    assert converted[Text] == ["intro", "read 0", "end"]
    assert converted.types == [Text]


def test_an_output_kind_of_another_type_is_refused():
    with pytest.raises(ValueError, match="holds Image"):
        apply_converter_to_document(
            build_document([image()]), _WrongKindOcr, {"Image": ItemFilter()}
        )


def test_a_converter_declaring_images_receives_whole_tables():
    converted = apply_converter_to_document(
        build_document([TABLE]), _ToImage, {"Text": ItemFilter()}
    )
    assert _ToImage.seen == ["a\tb"]
    assert _layout(converted) == [(0, "Image", "image", 1)]


def test_table_cells_cannot_become_images():
    with pytest.raises(ValueError, match="cells of a table"):
        apply_converter_to_document(
            build_document([TABLE]), _SaysTextMakesImages, {"Text": ItemFilter()}
        )


def test_an_image_cannot_become_a_number():
    with pytest.raises(ValueError, match="images or text"):
        apply_converter_to_document(
            build_document([image()]), _Counter, {"Image": ItemFilter()}
        )


def test_a_retype_and_a_replace_in_one_run_keep_reading_order():
    class _Both(_Ocr):
        def transform(self, x, y=None):
            if x.column_names[0] == "Image":
                return super().transform(x, y)
            values = [value.upper() for value in self._values(x)]
            return DashAIDataset(
                pa.table({"Text": pa.array(values)}),
                types={"Text": Text(arrow_type=pa.string())},
            )

    converted = apply_converter_to_document(
        build_document(["a", image(), "b"]),
        _Both,
        {"Image": ItemFilter(), "Text": ItemFilter()},
    )
    assert converted[Text] == ["A", "read 0", "B"]


def test_split_items_inherit_kind_attrs_and_page():
    document = build_document(
        [
            text("Title", kind="title"),
            text("one\ntwo", kind="list_item", page=2, depth=1),
            image(page=2),
            text("three", page=3),
        ]
    )
    converted = apply_converter_to_document(
        document, _Sentences, {"Text": ItemFilter(["list_item", "paragraph"])}
    )
    assert _layout(converted) == [
        (0, "Text", "title", 1),
        (1, "Text", "list_item", 2),
        (2, "Text", "list_item", 2),
        (3, "Image", "image", 2),
        (4, "Text", "paragraph", 3),
    ]
    assert converted[Text] == ["Title", "one", "two", "three"]
    assert converted.items()[2].attrs == {"ordered": False, "depth": 1}


def test_pieces_of_a_table_become_paragraphs():
    table = text("a\tb\nc\td", kind="table", rows=[["a", "b"], ["c", "d"]])
    converted = apply_converter_to_document(
        build_document([table]), _Sentences, {"Text": ItemFilter()}
    )
    assert [(item.kind, item.attrs) for item in converted.items()] == [
        ("paragraph", {}),
        ("paragraph", {}),
    ]


def test_dropped_items_leave_the_document_and_positions_close_up():
    converted = apply_converter_to_document(
        build_document(["ab", "long text", image()]),
        _DropShort,
        {"Text": ItemFilter()},
    )
    assert _layout(converted) == [(0, "Text", "paragraph", 1), (1, "Image", "image", 1)]


def test_dropping_every_item_of_a_type_removes_the_type():
    converted = apply_converter_to_document(
        build_document(["a", image()]), _DropAll, {"Image": ItemFilter()}
    )
    assert converted.types == [Text]


def test_kept_sources_are_followed_by_their_new_items(tmp_path):
    document = build_document([image(page=1), text("after", page=2)])
    converted = apply_converter_to_document(
        document, _Describe, {"Image": ItemFilter()}
    )
    save_document(converted, str(tmp_path / "document"))
    reloaded = load_document(str(tmp_path / "document"))
    assert _layout(reloaded) == [
        (0, "Image", "image", 1),
        (1, "Text", "caption", 1),
        (2, "Text", "paragraph", 2),
    ]
    assert reloaded.metadata == document.metadata


def test_new_items_take_the_kind_and_attrs_they_declare():
    converted = apply_converter_to_document(
        build_document(["Intro"]), _Headings, {"Text": ItemFilter()}
    )
    item = converted.items()[0]
    assert (item.kind, item.attrs) == ("heading", {"level": 3})


def test_picks_after_a_split_resolve_against_the_new_positions():
    class _Upper(_Converter):
        def transform(self, x, y=None):
            values = [value.upper() for value in self._values(x)]
            return DashAIDataset(
                pa.table({"Text": pa.array(values)}),
                types={"Text": Text(arrow_type=pa.string())},
            )

    split = apply_converter_to_document(
        build_document(["a\nb", "c"]), _Sentences, {"Text": ItemFilter()}
    )
    converted = apply_converter_to_document(
        split, _Upper, {"Text": ItemFilter(positions=[2])}
    )
    assert converted[Text] == ["a", "b", "C"]


def test_a_source_outside_the_received_items_is_refused():
    with pytest.raises(ValueError, match="sources"):
        apply_converter_to_document(
            build_document(["a"]), _BadSource, {"Text": ItemFilter()}
        )


def test_a_result_without_sources_is_refused():
    with pytest.raises(ValueError, match="source column"):
        apply_converter_to_document(
            build_document(["a"]), _NoSource, {"Text": ItemFilter()}
        )


def test_new_items_must_be_text_or_images():
    with pytest.raises(ValueError, match="only stores Text and Image"):
        apply_converter_to_document(
            build_document(["a"]), _Numbers, {"Text": ItemFilter()}
        )


def test_a_declared_attr_the_kind_does_not_take_is_refused():
    class _BadAttrs(_Items):
        def transform(self, x, y=None):
            return _items(["a"], [0], kinds=["paragraph"], attrs=['{"level": 1}'])

    with pytest.raises(ValueError, match="does not take attributes"):
        apply_converter_to_document(
            build_document(["a"]), _BadAttrs, {"Text": ItemFilter()}
        )


def test_document_converters_run_on_documents_only():
    assert supports_data_kind(_DatasetDeclared, DOCUMENT)
    assert not supports_data_kind(_DatasetDeclared, DATASET)
    metadata = _DatasetDeclared.get_metadata()
    assert metadata["data_kinds"] == [DOCUMENT]
    assert metadata["allowed_types"] == ["Text"]
    assert metadata["changes_row_count"] is True


def test_attrs_are_stored_as_json_objects():
    converted = apply_converter_to_document(
        build_document(["Intro"]), _Headings, {"Text": ItemFilter()}
    )
    stored = converted.tables[Text].column("attrs").to_pylist()
    assert [json.loads(value) for value in stored] == [{"level": 3}]
