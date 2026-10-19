import pyarrow as pa
import pytest

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.preprocessing.structure_types import (
    BlockItem,
    ColumnItem,
    RowsNotSupportedError,
    type_fields,
)
from DashAI.back.types.value_types import Float, Integer


class _FakeConverter(BaseConverter):
    SCHEMA = None
    metadata = {}

    def get_output_type(self, column_name=None):
        return Float(arrow_type=pa.float64())

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        return x


class _Replace(_FakeConverter):
    COLUMN_OPERATION = "replace"


class _ReplacePreserving(_FakeConverter):
    COLUMN_OPERATION = "replace"
    PRESERVES_INPUT_TYPE = True


class _Add(_FakeConverter):
    COLUMN_OPERATION = "add"


class _Expand(_FakeConverter):
    COLUMN_OPERATION = "expand"


class _Select(_FakeConverter):
    COLUMN_OPERATION = "select"


class _Rows(_FakeConverter):
    COLUMN_OPERATION = "rows"


class _Undeclared(_FakeConverter):
    pass


class _TrainOnlyRows(_FakeConverter):
    COLUMN_OPERATION = "rows"
    ROWS_APPLY_TO = "train"


def _inputs():
    return [
        ColumnItem(name="age", type="Integer", dtype="int64"),
        ColumnItem(name="height", type="Float", dtype="float64"),
    ]


def test_replace_keeps_inputs_retyped_with_output_type():
    delta = _Replace().infer_output_columns(_inputs())

    assert [item.name for item in delta.kept] == ["age", "height"]
    assert {item.type for item in delta.kept} == {"Float"}
    assert delta.added == []


def test_replace_preserving_input_type_keeps_inputs_unchanged():
    inputs = _inputs()
    delta = _ReplacePreserving().infer_output_columns(inputs)

    assert delta.kept == inputs
    assert delta.added == []


def test_replace_retypes_a_block_without_changing_its_identity():
    block = BlockItem(step=0, slot="Categorical", label="ohe_*", type="Categorical")
    delta = _Replace().infer_output_columns([block])

    (kept,) = delta.kept
    assert (kept.step, kept.slot) == (0, "Categorical")
    assert kept.type == "Float"


def test_add_keeps_inputs_and_adds_one_unknown_block():
    inputs = _inputs()
    delta = _Add().infer_output_columns(inputs)

    assert delta.kept == inputs
    (block,) = delta.added
    assert isinstance(block, BlockItem)
    assert block.type == "Float"
    assert block.count is None


def test_expand_removes_inputs_and_adds_one_unknown_block():
    delta = _Expand().infer_output_columns(_inputs())

    assert delta.kept == []
    (block,) = delta.added
    assert block.type == "Float"
    assert block.count is None


def test_select_adds_one_block_per_input_type_preserving_types():
    delta = _Select().infer_output_columns(_inputs())

    assert delta.kept == []
    assert sorted(block.type for block in delta.added) == ["Float", "Integer"]
    assert all(block.count is None for block in delta.added)


def test_rows_is_not_supported():
    with pytest.raises(RowsNotSupportedError):
        _Rows().infer_output_columns(_inputs())


def test_undeclared_operation_behaves_like_expand():
    delta = _Undeclared().infer_output_columns(_inputs())

    assert delta.kept == []
    (block,) = delta.added
    assert block.count is None


def test_metadata_exposes_column_operation():
    assert _Replace.get_metadata()["column_operation"] == "replace"
    assert _Undeclared.get_metadata()["column_operation"] is None


def test_type_fields_reads_display_name_and_dtype():
    assert type_fields(Integer(arrow_type=pa.int32())) == ("Integer", "int32")
    assert type_fields(None) == (None, None)


def test_train_only_rows_keeps_the_scope_and_drops_the_rest():
    inputs = _inputs()
    delta = _TrainOnlyRows().infer_output_columns(inputs)

    assert delta.kept == inputs
    assert delta.added == []
    assert delta.drops_unscoped is True


def test_metadata_exposes_rows_apply_to():
    assert _TrainOnlyRows.get_metadata()["rows_apply_to"] == "train"
    assert _Rows.get_metadata()["rows_apply_to"] is None
