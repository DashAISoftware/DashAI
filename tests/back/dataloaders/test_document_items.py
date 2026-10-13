import json

import pyarrow as pa
import pytest

from DashAI.back.converters.base_converter import BaseConverter, BaseConverterSchema
from DashAI.back.converters.simple_converters.character_replacer import (
    CharacterReplacer,
)
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.dataloaders.classes.dashai_document import (
    load_document,
    save_document,
)
from DashAI.back.dataloaders.classes.document_items import (
    ItemFilter,
    apply_converter_to_document,
    check_selection,
    get_document_columns_spec,
    items_as_column,
    selection_from_columns,
)
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Float, Text
from tests.back.document_fixtures import build_document, image, text, write_document


def _texts(values, name="Text"):
    table = pa.table({name: pa.array(list(values), type=pa.string())})
    return DashAIDataset(table, types={name: Text(arrow_type=pa.string())})


class _Upper(BaseConverter):
    SCHEMA = BaseConverterSchema
    metadata = {"allowed_types": [Text]}

    def get_output_type(self, column_name=None):
        return Text(arrow_type=pa.string())

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        column = x.column_names[0]
        values = x.arrow_table.column(column).to_pylist()
        return _texts([value.upper() for value in values], column)


class _Splitter(_Upper):
    def transform(self, x, y=None):
        n = len(x)
        table = pa.table(
            {
                "emb_0": pa.array([1.0] * n, type=pa.float32()),
                "emb_1": pa.array([2.0] * n, type=pa.float32()),
            }
        )
        types = {
            "emb_0": Float(arrow_type=pa.float32()),
            "emb_1": Float(arrow_type=pa.float32()),
        }
        return DashAIDataset(table, types=types)


class _Dropper(_Upper):
    def transform(self, x, y=None):
        return _texts(x.arrow_table.column(0).to_pylist()[:1])


class _Sampler(_Upper):
    CHANGES_ROW_COUNT = True


class _ToImage(_Upper):
    def transform(self, x, y=None):
        values = pa.array(
            [{"bytes": b"x", "path": None}] * len(x), type=DashAIImage.pa_type
        )
        return DashAIDataset(pa.table({"Text": values}), types={"Text": DashAIImage()})


MIXED = [
    text("Report", kind="title"),
    text("intro", page=1),
    image(page=1),
    text("Results", kind="heading", page=2, level=2),
    text("body", page=2),
]


def test_selection_reads_kinds_from_the_scope_columns():
    assert selection_from_columns(
        [
            {"columnName": "Text", "kinds": ["paragraph"]},
            {"columnName": "Image"},
        ]
    ) == {"Text": ItemFilter(["paragraph"]), "Image": ItemFilter()}


def test_selection_treats_empty_kinds_as_every_kind():
    assert selection_from_columns([{"columnName": "Text", "kinds": []}]) == {
        "Text": ItemFilter()
    }


def test_selection_merges_a_type_selected_twice():
    assert selection_from_columns(
        [
            {"columnName": "Text", "kinds": ["title"]},
            {"columnName": "Text", "kinds": ["heading", "title"]},
        ]
    ) == {"Text": ItemFilter(["title", "heading"])}


def test_items_as_column_keeps_only_the_selected_kinds():
    dataset = items_as_column(build_document(MIXED), "Text", ItemFilter(["paragraph"]))
    assert dataset.column_names == ["Text"]
    assert isinstance(dataset.types["Text"], Text)
    assert dataset.arrow_table.column("Text").to_pylist() == ["intro", "body"]


def test_items_as_column_without_kinds_keeps_every_item_of_the_type():
    dataset = items_as_column(build_document(MIXED), "Text")
    assert dataset.arrow_table.column("Text").to_pylist() == [
        "Report",
        "intro",
        "Results",
        "body",
    ]


def test_items_as_column_refuses_kinds_without_items():
    with pytest.raises(ValueError, match="code"):
        items_as_column(build_document(MIXED), "Text", ItemFilter(["code"]))


def test_only_the_selected_kinds_are_converted():
    converted = apply_converter_to_document(
        build_document(MIXED), _Upper, {"Text": ItemFilter(["paragraph"])}
    )
    assert converted[Text] == ["Report", "INTRO", "Results", "BODY"]
    assert len(converted[DashAIImage]) == 1


def test_conversion_keeps_order_kinds_and_attrs_after_a_reload(tmp_path):
    converted = apply_converter_to_document(
        build_document(MIXED), _Upper, {"Text": ItemFilter()}
    )
    save_document(converted, str(tmp_path / "document"))
    items = load_document(str(tmp_path / "document")).items()
    assert [(item.position, item.page, item.kind) for item in items] == [
        (0, 1, "title"),
        (1, 1, "paragraph"),
        (2, 1, "image"),
        (3, 2, "heading"),
        (4, 2, "paragraph"),
    ]
    assert items[3].attrs == {"level": 2}
    assert items[3].content == "RESULTS"


def test_the_character_replacer_runs_on_document_text():
    converted = apply_converter_to_document(
        build_document(["a_b", "c_d"]),
        lambda: CharacterReplacer(char_to_replace="_", replacement_char=" "),
        {"Text": ItemFilter()},
    )
    assert converted[Text] == ["a b", "c d"]


def test_a_number_promotion_is_stored_back_as_text():
    converted = apply_converter_to_document(
        build_document(["1a", "2a"]),
        lambda: CharacterReplacer(char_to_replace="a", replacement_char=None),
        {"Text": ItemFilter()},
    )
    assert converted[Text] == ["1", "2"]


TABLE = text(
    "Name\tCity\nana\t\nbo\tlima",
    kind="table",
    rows=[["Name", "City"], ["ana", ""], ["bo", "lima"]],
    header=True,
)


class _Recorder(_Upper):
    seen = []

    def transform(self, x, y=None):
        _Recorder.seen = x.arrow_table.column(0).to_pylist()
        return super().transform(x, y)


def _table_attrs(document):
    return json.loads(document.tables[Text].column("attrs").to_pylist()[0])


def test_a_table_is_converted_cell_by_cell():
    converted = apply_converter_to_document(
        build_document([TABLE, "note"]), _Recorder, {"Text": ItemFilter()}
    )
    assert _Recorder.seen == ["Name", "City", "ana", "bo", "lima", "note"]
    assert _table_attrs(converted) == {
        "rows": [["NAME", "CITY"], ["ANA", ""], ["BO", "LIMA"]],
        "header": True,
    }
    assert converted[Text] == ["NAME\tCITY\nANA\t\nBO\tLIMA", "NOTE"]


def test_converted_table_cells_survive_a_reload(tmp_path):
    converted = apply_converter_to_document(
        build_document([TABLE]),
        lambda: CharacterReplacer(char_to_replace="a", replacement_char="4"),
        {"Text": ItemFilter(["table"])},
    )
    save_document(converted, str(tmp_path / "document"))
    item = load_document(str(tmp_path / "document")).items()[0]
    assert item.attrs["rows"] == [["N4me", "City"], ["4n4", ""], ["bo", "lim4"]]
    assert item.content == "N4me\tCity\n4n4\t\nbo\tlim4"


def test_a_table_left_out_of_the_selection_keeps_its_cells():
    converted = apply_converter_to_document(
        build_document([TABLE, "note"]), _Upper, {"Text": ItemFilter(["paragraph"])}
    )
    assert _table_attrs(converted)["rows"] == TABLE.attrs["rows"]
    assert converted[Text] == [TABLE.content, "NOTE"]


def test_a_table_without_cells_is_left_unchanged():
    empty = text("\t", kind="table", rows=[["", ""]])
    converted = apply_converter_to_document(
        build_document([empty]), _Upper, {"Text": ItemFilter()}
    )
    assert converted[Text] == ["\t"]


def test_text_cannot_become_an_image():
    with pytest.raises(ValueError, match="as text"):
        apply_converter_to_document(
            build_document(["a"]), _ToImage, {"Text": ItemFilter()}
        )


def test_a_converter_that_outputs_many_columns_is_refused():
    with pytest.raises(ValueError, match="exactly one"):
        apply_converter_to_document(
            build_document(["a", "b"]), _Splitter, {"Text": ItemFilter()}
        )


def test_a_converter_that_drops_items_is_refused():
    with pytest.raises(ValueError, match="add or remove items"):
        apply_converter_to_document(
            build_document(["a", "b"]), _Dropper, {"Text": ItemFilter()}
        )


def test_a_row_count_changing_converter_is_refused():
    with pytest.raises(ValueError, match="number of rows"):
        apply_converter_to_document(
            build_document(["a"]), _Sampler, {"Text": ItemFilter()}
        )


def test_an_absent_content_type_is_refused():
    with pytest.raises(ValueError, match="no Image items"):
        apply_converter_to_document(
            build_document(["a"]), _Upper, {"Image": ItemFilter()}
        )


def test_an_empty_selection_is_refused():
    with pytest.raises(ValueError, match="at least one"):
        apply_converter_to_document(build_document(["a"]), _Upper, {})


def test_the_columns_spec_lists_types_and_kinds(tmp_path):
    path = write_document(tmp_path / "document", MIXED)
    assert get_document_columns_spec(str(path)) == {
        "Text": {
            "type": "Text",
            "dtype": "string",
            "count": 4,
            "kinds": {"title": 1, "paragraph": 2, "heading": 1},
        },
        "Image": {
            "type": "Image",
            "dtype": "struct",
            "count": 1,
            "kinds": {"image": 1},
        },
    }


def test_the_columns_spec_leaves_out_absent_types(tmp_path):
    path = write_document(tmp_path / "document", ["a", "b"])
    assert list(get_document_columns_spec(str(path))) == ["Text"]


def test_the_columns_spec_of_a_missing_document_is_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        get_document_columns_spec(str(tmp_path / "nothing"))


def test_selection_reads_positions_from_the_scope_columns():
    assert selection_from_columns(
        [{"columnName": "Text", "kinds": ["paragraph"], "positions": [4, 1, 4]}]
    ) == {"Text": ItemFilter(["paragraph"], [4, 1])}


def test_a_type_selected_twice_with_and_without_positions_keeps_every_item():
    assert selection_from_columns(
        [
            {"columnName": "Text", "positions": [1]},
            {"columnName": "Text"},
        ]
    ) == {"Text": ItemFilter()}


def test_only_the_picked_items_are_converted():
    converted = apply_converter_to_document(
        build_document(MIXED), _Upper, {"Text": ItemFilter(positions=[0, 4])}
    )
    assert converted[Text] == ["REPORT", "intro", "Results", "BODY"]


def test_positions_and_kinds_are_both_applied():
    dataset = items_as_column(
        build_document(MIXED), "Text", ItemFilter(["paragraph"], [0, 1])
    )
    assert dataset.arrow_table.column("Text").to_pylist() == ["intro"]


def test_check_selection_refuses_a_position_of_another_type(tmp_path):
    path = write_document(tmp_path / "document", MIXED)
    spec = get_document_columns_spec(str(path))
    with pytest.raises(ValueError, match="positions 2"):
        check_selection({"Text": ItemFilter(positions=[1, 2])}, spec, str(path))


def test_check_selection_refuses_a_position_outside_the_kinds(tmp_path):
    path = write_document(tmp_path / "document", MIXED)
    spec = get_document_columns_spec(str(path))
    with pytest.raises(ValueError, match="positions 0"):
        check_selection({"Text": ItemFilter(["paragraph"], [0, 1])}, spec, str(path))


def test_check_selection_accepts_picked_items(tmp_path):
    path = write_document(tmp_path / "document", MIXED)
    spec = get_document_columns_spec(str(path))
    check_selection({"Text": ItemFilter(["paragraph"], [1, 4])}, spec, str(path))
