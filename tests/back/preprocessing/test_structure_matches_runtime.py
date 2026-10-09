"""The structure a converter estimates must match what it really produces.

For every registered converter, `infer_output_columns` (called on an unfitted
instance, with no data) is compared against a real fit + transform on a small
dataset, spliced back the way SessionPreprocessor does it. This is what
guarantees that a converter chain the session wizard accepts never fails at
training time because it references a column that does not exist.
"""

import pandas as pd
import pytest

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.converters.dataset_columns import (
    rebuild_dataset_with_transformed_columns,
)
from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.initial_components import get_initial_components
from DashAI.back.preprocessing.session_preprocessor import SessionPreprocessor
from DashAI.back.preprocessing.structure_types import (
    BlockItem,
    ColumnItem,
    RowsNotSupportedError,
    type_fields,
)
from DashAI.back.splitters.splits_payload import schema_placeholder_defaults

N_ROWS = 30

SCHEMA = {
    "i_full": {"type": "Integer", "dtype": "int64"},
    "i2": {"type": "Integer", "dtype": "int64"},
    "i_null": {"type": "Integer", "dtype": "int64"},
    "f1": {"type": "Float", "dtype": "float64"},
    "f2": {"type": "Float", "dtype": "float64"},
    "f_null": {"type": "Float", "dtype": "float64"},
    "cat": {"type": "Categorical", "dtype": "string"},
    "text": {"type": "Text", "dtype": "string"},
    "code": {"type": "Text", "dtype": "string"},
    "date": {"type": "Date", "dtype": "%Y-%m-%d"},
    "target": {"type": "Categorical", "dtype": "string"},
}

# Converters that cannot run here: they download pretrained models. Their
# overrides get direct unit tests instead.
NEEDS_DOWNLOAD = {
    "Embedding",
    "TokenizerConverter",
    "ImageEmbeddingConverter",
    "SAM3SegmentConverter",
}

# (converter name, params on top of the schema placeholders, scope columns)
CASES = [
    ("StandardScaler", {}, ["i_full", "f1"]),
    ("MinMaxScaler", {}, ["i_full", "f1"]),
    ("MaxAbsScaler", {}, ["i_full", "f1"]),
    ("Normalizer", {}, ["i_full", "f1"]),
    ("SimpleImputer", {"strategy": "mean"}, ["i_null", "f_null"]),
    ("SimpleImputer", {"strategy": "most_frequent"}, ["cat", "i_null"]),
    (
        "SimpleImputer",
        {"strategy": "median", "add_indicator": True},
        ["i_null", "f_null"],
    ),
    ("KNNImputer", {}, ["i_null", "f_null"]),
    ("MissingIndicator", {}, ["i_null", "f_null"]),
    ("Binarizer", {}, ["i_full", "f1"]),
    ("OrdinalEncoder", {}, ["cat"]),
    ("OneHotEncoder", {}, ["cat"]),
    ("LabelEncoder", {}, ["cat"]),
    ("PCA", {"n_components": 2}, ["i_full", "f1", "f2"]),
    ("IncrementalPCA", {"n_components": 2}, ["i_full", "f1", "f2"]),
    ("TruncatedSVD", {"n_components": 2}, ["i_full", "f1", "f2"]),
    ("FastICA", {"n_components": 2}, ["i_full", "f1", "f2"]),
    ("Nystroem", {"n_components": 5}, ["i_full", "f1"]),
    ("RBFSampler", {"n_components": 5}, ["i_full", "f1"]),
    ("SkewedChi2Sampler", {"n_components": 5}, ["i_full", "i2"]),
    ("AdditiveChi2Sampler", {}, ["i_full", "i2"]),
    ("PolynomialFeatures", {"degree": 2}, ["i_full", "f1"]),
    ("VarianceThreshold", {}, ["i_full", "f1"]),
    ("SelectKBest", {"k": 1}, ["i_full", "f1"]),
    ("SelectPercentile", {}, ["i_full", "f1"]),
    ("SelectFdr", {}, ["i_full", "f1"]),
    ("SelectFpr", {}, ["i_full", "f1"]),
    ("SelectFwe", {}, ["i_full", "f1"]),
    ("GenericUnivariateSelect", {}, ["i_full", "f1"]),
    ("BagOfWordsConverter", {}, ["text"]),
    ("TFIDFConverter", {}, ["text"]),
    (
        "CharacterReplacer",
        {"char_to_replace": "-", "replacement_char": ""},
        ["code"],
    ),
    ("ColumnArithmetic", {"operation": "add"}, ["i_full", "i2"]),
    ("ColumnArithmetic", {"operation": "multiply"}, ["i_null", "i2"]),
    ("ColumnArithmetic", {"operation": "divide"}, ["i_full", "f1"]),
    ("ColumnConcat", {}, ["cat", "text"]),
    ("NumericExpansion", {"operation": "square"}, ["i_null", "i_full"]),
    ("NumericExpansion", {"operation": "log1p"}, ["f1"]),
    ("DateFeaturesConverter", {}, ["date"]),
    ("TypeCast", {"new_type": "Float"}, ["i_full"]),
    ("ColumnRemover", {}, ["f1"]),
    ("SMOTEConverter", {"random_state": 0}, ["i_full", "f1"]),
    ("SMOTEENNConverter", {"random_state": 0}, ["i_full", "f1"]),
    ("RandomUnderSamplerConverter", {"random_state": 0}, ["i_full", "f1"]),
    ("NanRemover", {}, ["i_null", "f_null"]),
]


# Cases whose output size follows from params and input columns alone: the
# estimate must be exact (no block of unknown size), not just conservative.
EXACT = {
    "SimpleImputer[strategy=mean]",
    "SimpleImputer[strategy=most_frequent]",
    "KNNImputer",
    "MissingIndicator",
    "Binarizer",
    "OrdinalEncoder",
    "LabelEncoder",
    "PCA[n_components=2]",
    "IncrementalPCA[n_components=2]",
    "TruncatedSVD[n_components=2]",
    "FastICA[n_components=2]",
    "Nystroem[n_components=5]",
    "RBFSampler[n_components=5]",
    "SkewedChi2Sampler[n_components=5]",
    "AdditiveChi2Sampler",
    "PolynomialFeatures[degree=2]",
    "StandardScaler",
    "MinMaxScaler",
    "MaxAbsScaler",
    "Normalizer",
    "CharacterReplacer[char_to_replace=-,replacement_char=]",
    "ColumnArithmetic[operation=add]",
    "ColumnArithmetic[operation=multiply]",
    "ColumnArithmetic[operation=divide]",
    "ColumnConcat",
    "NumericExpansion[operation=square]",
    "NumericExpansion[operation=log1p]",
    "DateFeaturesConverter",
    "TypeCast[new_type=Float]",
    "ColumnRemover",
}

# Cases whose output is only concrete columns: names must be known.
CONCRETE_ONLY = {
    "ColumnArithmetic[operation=add]",
    "ColumnArithmetic[operation=multiply]",
    "ColumnArithmetic[operation=divide]",
    "ColumnConcat",
    "NumericExpansion[operation=square]",
    "NumericExpansion[operation=log1p]",
    "DateFeaturesConverter",
    "ColumnRemover",
}


def _converter_classes():
    return {
        cls.__name__: cls
        for cls in get_initial_components()
        if isinstance(cls, type)
        and issubclass(cls, BaseConverter)
        and cls.__module__.startswith("DashAI.back.converters")
    }


def _is_rows(cls):
    return cls.COLUMN_OPERATION == "rows"


def _unsupported_rows(cls):
    return _is_rows(cls) and getattr(cls, "ROWS_APPLY_TO", None) not in (
        "train",
        "splits",
    )


def _dataset():
    words = ["red apple", "green pear", "blue plum", "red plum", "green apple"]
    frame = pd.DataFrame(
        {
            "i_full": [(i * 7) % 11 + 1 for i in range(N_ROWS)],
            "i2": [(i * 3) % 5 + 1 for i in range(N_ROWS)],
            "i_null": pd.array(
                [None if i % 6 == 0 else i % 9 for i in range(N_ROWS)],
                dtype="Int64",
            ),
            "f1": [0.5 + (i * 13) % 17 / 3 for i in range(N_ROWS)],
            "f2": [1.25 + (i * 5) % 7 / 2 for i in range(N_ROWS)],
            "f_null": [
                None if i % 5 == 0 else 0.1 + (i % 4) * 1.3 for i in range(N_ROWS)
            ],
            "cat": [["a", "b", "c"][i % 3] for i in range(N_ROWS)],
            "text": [words[i % len(words)] for i in range(N_ROWS)],
            "code": [f"{i % 4}-{i % 7}" for i in range(N_ROWS)],
            "date": [f"2024-{i % 12 + 1:02d}-{i % 28 + 1:02d}" for i in range(N_ROWS)],
            "target": [["yes", "no"][(i * 7) % 11 % 2] for i in range(N_ROWS)],
        }
    )
    return transform_dataset_with_schema(to_dashai_dataset(frame), SCHEMA)


def _build(cls, params):
    return cls(**{**schema_placeholder_defaults(cls), **params})


def _scope_items(dataset, scope):
    items = []
    for name in scope:
        type_name, dtype = type_fields(dataset.types[name])
        items.append(ColumnItem(name=name, type=type_name, dtype=dtype))
    return items


def _case_id(case):
    name, params, _ = case
    extra = ",".join(f"{k}={v}" for k, v in params.items())
    return f"{name}[{extra}]" if extra else name


@pytest.mark.parametrize("case", CASES, ids=[_case_id(c) for c in CASES])
def test_estimated_structure_matches_runtime(case):
    name, params, scope = case
    cls = _converter_classes()[name]
    dataset = _dataset()

    delta = _build(cls, params).infer_output_columns(_scope_items(dataset, scope))
    if _case_id(case) in EXACT:
        unknown = [
            item
            for item in delta.added
            if isinstance(item, BlockItem) and item.count is None
        ]
        assert unknown == [], "the estimate should know the output size"
    if _case_id(case) in CONCRETE_ONLY:
        assert not any(isinstance(i, BlockItem) for i in delta.added), "no blocks"

    converter = _build(cls, params)
    x = dataset.select_columns(scope)
    if cls.SUPERVISED:
        converter.fit(x, dataset.select_columns(["target"]))
    else:
        converter.fit(x)
    transformed = converter.transform(x)

    if getattr(cls, "ROWS_APPLY_TO", None) == "splits":
        # Row removal on every split: the step keeps its scope columns and
        # exactly the rows with no missing value in them.
        frame = x.to_pandas()
        expected = [i for i in range(len(frame)) if not frame.iloc[i].isna().any()]
        assert converter.rows_to_keep(x) == expected
        assert list(transformed.column_names) == scope
        assert [item.name for item in delta.kept] == scope
        assert delta.drops_unscoped is True
        return

    if delta.drops_unscoped:
        # A training-only resampler keeps its scope columns (only rows change)
        # plus the target it resampled along with them, and drops the rest.
        assert list(transformed.column_names) == scope + ["target"]
        assert [item.name for item in delta.kept] == scope
        for item in delta.kept:
            real = type_fields(transformed.types[item.name])[0]
            assert real == item.type, f"type of kept {item.name}"
        assert delta.added == []
        return
    rebuilt = rebuild_dataset_with_transformed_columns(
        dataset,
        transformed,
        scope,
        [dataset.column_names.index(column) for column in scope],
    )

    def real_type(column):
        return type_fields(rebuilt.types[column])[0]

    real_out = list(transformed.column_names)
    real_new = [c for c in real_out if c not in scope]
    concrete = [item for item in delta.added if isinstance(item, ColumnItem)]
    blocks = [item for item in delta.added if isinstance(item, BlockItem)]
    assert not (concrete and blocks), "a delta never mixes columns and blocks"

    # Every scope column the estimate says survives really survives, with
    # the estimated type. This is the property that keeps a later step from
    # referencing a column that no longer exists.
    kept_names = [item.name for item in delta.kept if isinstance(item, ColumnItem)]
    for item in delta.kept:
        assert item.name in real_out, f"{item.name} was estimated to survive"
        assert real_type(item.name) == item.type, f"type of kept {item.name}"

    # A scope column the estimate drops may still survive only when a block
    # stands for it (a selector keeps some scope columns, unknown which).
    real_survivors = [c for c in scope if c in real_out and c not in kept_names]
    if real_survivors:
        assert blocks, f"{real_survivors} survive but nothing accounts for them"

    # New concrete columns: exact names and types.
    if concrete:
        assert [item.name for item in concrete] == real_new, "new column names"
        for item in concrete:
            assert real_type(item.name) == item.type, f"type of new {item.name}"
        return
    if not blocks:
        assert real_new == [], f"unexpected new columns {real_new}"
        return

    # Symbolic blocks stand for the new columns plus any unnamed survivors.
    # With an unknown count a block may turn out empty (a selector keeping
    # nothing of that type), so real types only need to be a subset; with a
    # known count, the block has exactly that many columns.
    block_columns = real_new + real_survivors
    real_by_type = {}
    for column in block_columns:
        real_by_type.setdefault(real_type(column), []).append(column)
    estimated_types = {block.type for block in blocks}
    assert set(real_by_type) <= estimated_types, "block types"
    for block in blocks:
        if block.count is not None:
            assert block.count == len(real_by_type.get(block.type, [])), "count"

    # The runtime classifies a step's group (its new columns, or all its
    # output when it adds none) into slots by type; they must line up with
    # the blocks.
    group = real_new or real_out
    runtime_slots = SessionPreprocessor._classify_by_type(converter, group)
    assert set(runtime_slots) <= estimated_types, "runtime slots"


def test_every_converter_is_covered():
    covered = {name for name, _, _ in CASES} | NEEDS_DOWNLOAD
    uncovered = {
        name
        for name, cls in _converter_classes().items()
        if not _unsupported_rows(cls) and name not in covered
    }
    assert uncovered == set(), "add a CASES entry for every new converter"


def test_rows_operation_matches_changes_row_count():
    for name, cls in _converter_classes().items():
        assert _is_rows(cls) == bool(cls.CHANGES_ROW_COUNT), name


def test_unsupported_rows_converters_are_rejected_in_sessions():
    for cls in _converter_classes().values():
        if not _unsupported_rows(cls):
            continue
        with pytest.raises(RowsNotSupportedError):
            BaseConverter.infer_output_columns(
                cls.__new__(cls), _scope_items(_dataset(), ["i_full"])
            )
