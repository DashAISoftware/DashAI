from DashAI.back.exploration.base_explorer import BaseExplorer, BaseExplorerSchema
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Float, Integer


def _make_explorer(**metadata_fields):
    """Return a minimal concrete BaseExplorer subclass with the given metadata."""

    class _StubExplorer(BaseExplorer):
        SCHEMA = BaseExplorerSchema
        metadata = metadata_fields

        def launch_exploration(self, dataset, explorer_info):
            return None

        def save_notebook(self, notebook_info, explorer_info, save_path, result):
            return ""

        def get_results(self, exploration_path, options):
            return {}

    return _StubExplorer


def _make_downloadable_explorer():
    """Return a minimal concrete BaseExplorer that requires a download."""

    class _DownloadableExplorer(BaseExplorer):
        SCHEMA = BaseExplorerSchema
        metadata = {}
        REQUIRES_DOWNLOAD = True
        DOWNLOAD_SIZE_BYTES = 5678

        def launch_exploration(self, dataset, explorer_info):
            return None

        def save_notebook(self, notebook_info, explorer_info, save_path, result):
            return ""

        def get_results(self, exploration_path, options):
            return {}

    return _DownloadableExplorer


# --- get_metadata tests ---


def test_get_metadata_serializes_allowed_types():
    cls = _make_explorer(allowed_types=[Float, Integer], allowed_dtypes=[])
    meta = cls.get_metadata()
    assert meta["allowed_types"] == ["Float", "Integer"]


def test_get_metadata_drops_restricted_dtypes():
    cls = _make_explorer(allowed_types=[], allowed_dtypes=[], restricted_dtypes=[])
    meta = cls.get_metadata()
    assert "restricted_dtypes" not in meta


def test_get_metadata_normalizes_star_allowed_dtypes():
    cls = _make_explorer(allowed_types=[], allowed_dtypes=["*"])
    meta = cls.get_metadata()
    assert meta["allowed_dtypes"] == []


def test_get_metadata_empty_metadata_defaults():
    cls = _make_explorer()
    meta = cls.get_metadata()
    assert meta["allowed_types"] == []
    assert meta["allowed_dtypes"] == []
    assert "restricted_dtypes" not in meta
    assert meta["input_cardinality"] == {"min": 1}


def test_get_metadata_none_metadata_defaults():
    class _NoneMetaExplorer(BaseExplorer):
        SCHEMA = BaseExplorerSchema
        metadata = None

        def launch_exploration(self, dataset, explorer_info):
            return None

        def save_notebook(self, notebook_info, explorer_info, save_path, result):
            return ""

        def get_results(self, exploration_path, options):
            return {}

    meta = _NoneMetaExplorer.get_metadata()
    assert meta["allowed_types"] == []
    assert meta["allowed_dtypes"] == []
    assert "restricted_dtypes" not in meta


def test_get_metadata_plain_explorer_not_downloadable():
    cls = _make_explorer()
    meta = cls.get_metadata()
    assert meta["requires_download"] is False
    assert meta["download_size_bytes"] is None


def test_get_metadata_downloadable_explorer_metadata():
    cls = _make_downloadable_explorer()
    meta = cls.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == 5678


def test_get_metadata_does_not_mutate_class_attribute():
    cls = _make_explorer(allowed_types=[Float], allowed_dtypes=[])
    original_metadata = dict(cls.metadata)
    cls.get_metadata()
    assert cls.metadata == original_metadata


# --- validate_columns tests ---


class _MockExplorerInfo:
    def __init__(self, columns):
        self.columns = columns


def test_validate_columns_allowed_types_passes_matching():
    cls = _make_explorer(
        allowed_types=[Float, Integer],
        allowed_dtypes=[],
        input_cardinality={"min": 1},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "age"}])
    column_spec = {"age": {"type": "Float", "dtype": "float64"}}
    assert cls.validate_columns(explorer_info, column_spec) is True


def test_validate_columns_allowed_types_blocks_wrong_type():
    cls = _make_explorer(
        allowed_types=[Float, Integer],
        allowed_dtypes=[],
        input_cardinality={"min": 1},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "label"}])
    column_spec = {"label": {"type": "Categorical", "dtype": "string"}}
    assert cls.validate_columns(explorer_info, column_spec) is False


def test_validate_columns_no_restrictions_passes_any_type():
    cls = _make_explorer(
        allowed_types=[],
        allowed_dtypes=[],
        input_cardinality={"min": 1},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "text_col"}])
    column_spec = {"text_col": {"type": "Text", "dtype": "string"}}
    assert cls.validate_columns(explorer_info, column_spec) is True


def test_validate_columns_cardinality_exact_fails():
    cls = _make_explorer(
        allowed_types=[],
        allowed_dtypes=[],
        input_cardinality={"exact": 2},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "a"}])
    column_spec = {"a": {"type": "Float", "dtype": "float64"}}
    assert cls.validate_columns(explorer_info, column_spec) is False


def test_validate_columns_cardinality_exact_passes():
    cls = _make_explorer(
        allowed_types=[],
        allowed_dtypes=[],
        input_cardinality={"exact": 2},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "a"}, {"columnName": "b"}])
    column_spec = {
        "a": {"type": "Float", "dtype": "float64"},
        "b": {"type": "Float", "dtype": "float64"},
    }
    assert cls.validate_columns(explorer_info, column_spec) is True


def test_validate_columns_cardinality_min_fails():
    cls = _make_explorer(
        allowed_types=[],
        allowed_dtypes=[],
        input_cardinality={"min": 2},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "a"}])
    column_spec = {"a": {"type": "Float", "dtype": "float64"}}
    assert cls.validate_columns(explorer_info, column_spec) is False


def test_validate_columns_cardinality_max_fails():
    cls = _make_explorer(
        allowed_types=[],
        allowed_dtypes=[],
        input_cardinality={"max": 1},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "a"}, {"columnName": "b"}])
    column_spec = {
        "a": {"type": "Float", "dtype": "float64"},
        "b": {"type": "Float", "dtype": "float64"},
    }
    assert cls.validate_columns(explorer_info, column_spec) is False


def test_validate_columns_categorical_passes_categorical_restriction():
    cls = _make_explorer(
        allowed_types=[Categorical],
        allowed_dtypes=[],
        input_cardinality={"min": 1},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "label"}])
    column_spec = {"label": {"type": "Categorical", "dtype": "string"}}
    assert cls.validate_columns(explorer_info, column_spec) is True


def test_validate_columns_missing_column_in_spec_returns_false_when_restricted():
    cls = _make_explorer(
        allowed_types=[Float, Integer],
        allowed_dtypes=[],
        input_cardinality={"min": 1},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "missing_col"}])
    column_spec = {}  # column not in spec → col_type = "" → blocked
    assert cls.validate_columns(explorer_info, column_spec) is False


def test_validate_columns_missing_column_in_spec_passes_when_unrestricted():
    cls = _make_explorer(
        allowed_types=[],
        allowed_dtypes=[],
        input_cardinality={"min": 1},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "missing_col"}])
    column_spec = {}  # no restrictions → passes regardless
    assert cls.validate_columns(explorer_info, column_spec) is True


# --- non_allowed_dtypes tests ---


def test_non_allowed_dtypes_passes_int_dtype():
    cls = _make_explorer(
        allowed_types=[Float, Integer, Categorical],
        allowed_dtypes=[],
        non_allowed_dtypes=["string", "bool", ""],
        input_cardinality={"min": 1},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "cat_num"}])
    column_spec = {"cat_num": {"type": "Categorical", "dtype": "int64"}}
    assert cls.validate_columns(explorer_info, column_spec) is True


def test_non_allowed_dtypes_passes_float_dtype():
    cls = _make_explorer(
        allowed_types=[Float, Integer, Categorical],
        allowed_dtypes=[],
        non_allowed_dtypes=["string", "bool", ""],
        input_cardinality={"min": 1},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "cat_num"}])
    column_spec = {"cat_num": {"type": "Categorical", "dtype": "float64"}}
    assert cls.validate_columns(explorer_info, column_spec) is True


def test_non_allowed_dtypes_blocks_string_dtype():
    cls = _make_explorer(
        allowed_types=[Float, Integer, Categorical],
        allowed_dtypes=[],
        non_allowed_dtypes=["string", "bool", ""],
        input_cardinality={"min": 1},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "cat_str"}])
    column_spec = {"cat_str": {"type": "Categorical", "dtype": "string"}}
    assert cls.validate_columns(explorer_info, column_spec) is False


def test_non_allowed_dtypes_blocks_bool_dtype():
    cls = _make_explorer(
        allowed_types=[Float, Integer, Categorical],
        allowed_dtypes=[],
        non_allowed_dtypes=["string", "bool", ""],
        input_cardinality={"min": 1},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "cat_bool"}])
    column_spec = {"cat_bool": {"type": "Categorical", "dtype": "bool"}}
    assert cls.validate_columns(explorer_info, column_spec) is False


def test_non_allowed_dtypes_absent_allows_string_categorical():
    cls = _make_explorer(
        allowed_types=[Float, Integer, Categorical],
        allowed_dtypes=[],
        input_cardinality={"min": 1},
    )
    explorer_info = _MockExplorerInfo([{"columnName": "cat_str"}])
    column_spec = {"cat_str": {"type": "Categorical", "dtype": "string"}}
    assert cls.validate_columns(explorer_info, column_spec) is True


def test_get_metadata_includes_non_allowed_dtypes():
    cls = _make_explorer(
        allowed_types=[],
        allowed_dtypes=[],
        non_allowed_dtypes=["string", "bool", ""],
    )
    meta = cls.get_metadata()
    assert meta["non_allowed_dtypes"] == ["string", "bool", ""]


def test_get_metadata_non_allowed_dtypes_defaults_to_empty():
    cls = _make_explorer(allowed_types=[], allowed_dtypes=[])
    meta = cls.get_metadata()
    assert meta["non_allowed_dtypes"] == []


def test_get_metadata_drops_numeric_categorical_only():
    cls = _make_explorer(
        allowed_types=[],
        allowed_dtypes=[],
        numeric_categorical_only=True,
    )
    meta = cls.get_metadata()
    assert "numeric_categorical_only" not in meta
