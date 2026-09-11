import pandas as pd

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.dataloaders.classes.dashai_dataset import (
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.preprocessing.column_ref import (
    ConverterSequence,
    ConverterStep,
    GroupColumnRef,
    RawColumnRef,
)
from DashAI.back.preprocessing.session_preprocessor import SessionPreprocessor
from DashAI.back.types.value_types import Integer


def _dataset(columns, schema):
    return transform_dataset_with_schema(
        to_dashai_dataset(pd.DataFrame(columns)), schema
    )


class _DoublingConverter(BaseConverter):
    """Deterministic: doubles a single numeric column in place."""

    SCHEMA = None
    metadata = {"allowed_types": [Integer], "allowed_dtypes": []}
    CHANGES_ROW_COUNT = False

    def get_output_type(self, column_name=None):
        import pyarrow as pa

        return Integer(arrow_type=pa.int64())

    def fit(self, x, y=None):
        self._column = x.column_names[0]
        return self

    def transform(self, x, y=None):
        frame = x.to_pandas()
        frame[self._column] = frame[self._column] * 2
        return to_dashai_dataset(frame)


class _FakeVocabConverter(BaseConverter):
    """Variable output: emits one column per 'word' seen in fit, mirroring
    Bag-of-Words' vocabulary-at-fit-time behavior without needing sklearn."""

    SCHEMA = None
    metadata = {"allowed_types": [Integer], "allowed_dtypes": []}
    CHANGES_ROW_COUNT = False

    def get_output_type(self, column_name=None):
        import pyarrow as pa

        return Integer(arrow_type=pa.int64())

    def fit(self, x, y=None):
        column = x.column_names[0]
        self._vocab = sorted(set(x.to_pandas()[column].tolist()))
        return self

    def transform(self, x, y=None):
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        column = x.column_names[0]
        values = x.to_pandas()[column].tolist()
        output_type = self.get_output_type()
        data = {
            f"vocab_{word}": [1 if v == word else 0 for v in values]
            for word in self._vocab
        }
        table = pa.table(data)
        types = dict.fromkeys(data, output_type)
        return DashAIDataset(table, types=types)


class _FakeAdditiveConverter(BaseConverter):
    """Mirrors BagOfWordsConverter's real behavior: keeps its scope column
    verbatim and appends brand-new derived columns alongside it, instead of
    replacing the scope column or dropping it."""

    SCHEMA = None
    metadata = {"allowed_types": [Integer], "allowed_dtypes": []}
    CHANGES_ROW_COUNT = False

    def get_output_type(self, column_name=None):
        import pyarrow as pa

        return Integer(arrow_type=pa.int64())

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        frame = x.to_pandas()
        column = x.column_names[0]
        frame["derived"] = frame[column] * 10
        output_type = self.get_output_type()
        types = {**x.types, "derived": output_type}
        return to_dashai_dataset(frame, types=types)


class _FakeTypeObj:
    """Minimal stand-in for a DashAIDataType — only display_name() matters
    to SessionPreprocessor._classify_by_type."""

    def __init__(self, name):
        self._name = name

    def display_name(self):
        return self._name


class _MixedTypeConverter(BaseConverter):
    """Mirrors SimpleImputer's most_frequent/FeatureSelectionConverter:
    keeps every scope column's own value and declared type unchanged. Used
    to test that fit_transform classifies real output columns into one slot
    per distinct type when a scope mixes them, without needing a real
    Categorical dataset column — the per-column type is just a hardcoded
    mapping passed in as a param, exactly like a real converter would derive
    it from its own fitted state.
    """

    SCHEMA = None
    metadata = {"allowed_types": [Integer], "allowed_dtypes": []}
    CHANGES_ROW_COUNT = False

    def __init__(self, type_by_column=None, **kwargs):
        self._type_by_column = type_by_column or {}

    def fit(self, x, y=None):
        return self

    def get_output_type(self, column_name=None):
        return _FakeTypeObj(self._type_by_column.get(column_name, "Integer"))

    def transform(self, x, y=None):
        return x


class _FakeRegistry:
    def __init__(self, classes):
        self._classes = classes

    def __getitem__(self, name):
        return {"class": self._classes[name]}


def _split(train_ages, val_ages=None):
    train = _dataset(
        {"age": train_ages}, {"age": {"type": "Integer", "dtype": "int64"}}
    )
    split = {"train": train}
    if val_ages is not None:
        split["validation"] = _dataset(
            {"age": val_ages}, {"age": {"type": "Integer", "dtype": "int64"}}
        )
    return split


def test_fits_only_on_train_and_transforms_every_split_present():
    registry = _FakeRegistry({"Doubler": _DoublingConverter})
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="Doubler", params={}, scope=[RawColumnRef(name="age")]
            )
        ]
    )
    preprocessor = SessionPreprocessor(sequence, registry)

    split = _split(train_ages=[1, 2, 3], val_ages=[10, 20])
    transformed, resolved = preprocessor.fit_transform(split)

    assert transformed["train"].to_pandas()["age"].tolist() == [2, 4, 6]
    assert transformed["validation"].to_pandas()["age"].tolist() == [20, 40]
    assert resolved == {0: ["age"]}


def test_variable_output_step_records_whatever_columns_it_produced():
    registry = _FakeRegistry({"FakeVocab": _FakeVocabConverter})
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="FakeVocab", params={}, scope=[RawColumnRef(name="age")]
            )
        ]
    )
    preprocessor = SessionPreprocessor(sequence, registry)

    split = _split(train_ages=[1, 2, 1])
    transformed, resolved = preprocessor.fit_transform(split)

    assert sorted(resolved[0]) == ["vocab_1", "vocab_2"]
    assert set(transformed["train"].column_names) == {"vocab_1", "vocab_2"}


def test_additive_step_that_keeps_its_scope_column_excludes_it_from_the_group():
    registry = _FakeRegistry({"Additive": _FakeAdditiveConverter})
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="Additive", params={}, scope=[RawColumnRef(name="age")]
            )
        ]
    )
    preprocessor = SessionPreprocessor(sequence, registry)

    split = _split(train_ages=[1, 2, 3])
    transformed, resolved = preprocessor.fit_transform(split)

    # "age" is carried through unchanged (a passthrough, like BagOfWords
    # keeping its source text column) — it must not be part of the step's
    # own group, only the genuinely new "derived" column is.
    assert resolved == {0: ["derived"]}
    assert set(transformed["train"].column_names) == {"age", "derived"}


def test_chained_step_can_reference_the_previous_steps_group():
    registry = _FakeRegistry(
        {"FakeVocab": _FakeVocabConverter, "Doubler": _DoublingConverter}
    )
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="FakeVocab", params={}, scope=[RawColumnRef(name="age")]
            ),
            ConverterStep(
                converter="Doubler", params={}, scope=[GroupColumnRef(step=0)]
            ),
        ]
    )
    preprocessor = SessionPreprocessor(sequence, registry)

    split = _split(train_ages=[1, 2])
    transformed, resolved = preprocessor.fit_transform(split)

    # Doubler's scope is step 0's whole output group (both vocab columns);
    # it doubles column_names[0] but its transform returns every column in
    # its scope, so step 1 produces the same column set step 0 did.
    assert set(resolved[1]) == set(resolved[0])
    assert len(resolved[1]) == 2


def test_fit_transform_classifies_a_steps_real_output_columns_by_type():
    registry = _FakeRegistry({"MixedType": _MixedTypeConverter})
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="MixedType",
                params={"type_by_column": {"age": "Integer", "city": "Categorical"}},
                scope=[RawColumnRef(name="age"), RawColumnRef(name="city")],
            )
        ]
    )
    preprocessor = SessionPreprocessor(sequence, registry)

    train = _dataset(
        {"age": [1, 2, 3], "city": [10, 20, 10]},
        {
            "age": {"type": "Integer", "dtype": "int64"},
            "city": {"type": "Integer", "dtype": "int64"},
        },
    )
    preprocessor.fit_transform({"train": train})

    assert preprocessor.resolved_slots[0] == {
        "Integer": ["age"],
        "Categorical": ["city"],
    }


def test_chained_step_can_reference_a_specific_slot_of_an_earlier_steps_group():
    registry = _FakeRegistry(
        {"MixedType": _MixedTypeConverter, "Doubler": _DoublingConverter}
    )
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="MixedType",
                params={"type_by_column": {"age": "Integer", "city": "Categorical"}},
                scope=[RawColumnRef(name="age"), RawColumnRef(name="city")],
            ),
            ConverterStep(
                converter="Doubler",
                params={},
                scope=[GroupColumnRef(step=0, slot="Integer")],
            ),
        ]
    )
    preprocessor = SessionPreprocessor(sequence, registry)

    train = _dataset(
        {"age": [1, 2, 3], "city": [10, 20, 10]},
        {
            "age": {"type": "Integer", "dtype": "int64"},
            "city": {"type": "Integer", "dtype": "int64"},
        },
    )
    transformed, _ = preprocessor.fit_transform({"train": train})

    # Doubler was scoped only to the "Integer" slot (age); city, the
    # "Categorical" slot, is untouched.
    assert transformed["train"].to_pandas()["age"].tolist() == [2, 4, 6]
    assert transformed["train"].to_pandas()["city"].tolist() == [10, 20, 10]


def test_transform_only_resolves_a_slotted_scope_using_persisted_resolved_slots():
    registry = _FakeRegistry(
        {"MixedType": _MixedTypeConverter, "Doubler": _DoublingConverter}
    )
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="MixedType",
                params={"type_by_column": {"age": "Integer", "city": "Categorical"}},
                scope=[RawColumnRef(name="age"), RawColumnRef(name="city")],
            ),
            ConverterStep(
                converter="Doubler",
                params={},
                scope=[GroupColumnRef(step=0, slot="Integer")],
            ),
        ]
    )
    preprocessor = SessionPreprocessor(sequence, registry)
    train = _dataset(
        {"age": [1, 2, 3], "city": [10, 20, 10]},
        {
            "age": {"type": "Integer", "dtype": "int64"},
            "city": {"type": "Integer", "dtype": "int64"},
        },
    )
    preprocessor.fit_transform({"train": train})

    new_data = _dataset(
        {"age": [5], "city": [99]},
        {
            "age": {"type": "Integer", "dtype": "int64"},
            "city": {"type": "Integer", "dtype": "int64"},
        },
    )
    result = preprocessor.transform_only({"train": new_data})

    assert result["train"].to_pandas()["age"].tolist() == [10]
    assert result["train"].to_pandas()["city"].tolist() == [99]


def test_transform_only_applies_an_already_fitted_sequence_without_refitting():
    registry = _FakeRegistry({"Doubler": _DoublingConverter})
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="Doubler", params={}, scope=[RawColumnRef(name="age")]
            )
        ]
    )
    preprocessor = SessionPreprocessor(sequence, registry)
    preprocessor.fit_transform(_split(train_ages=[1, 2, 3]))

    new_split = _split(train_ages=[100])
    transformed = preprocessor.transform_only(new_split)

    assert transformed["train"].to_pandas()["age"].tolist() == [200]


def test_transform_dataset_is_a_single_dataset_convenience_wrapper():
    registry = _FakeRegistry({"Doubler": _DoublingConverter})
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="Doubler", params={}, scope=[RawColumnRef(name="age")]
            )
        ]
    )
    preprocessor = SessionPreprocessor(sequence, registry)
    preprocessor.fit_transform(_split(train_ages=[1, 2, 3]))

    single = _dataset({"age": [5]}, {"age": {"type": "Integer", "dtype": "int64"}})
    result = preprocessor.transform_dataset(single)

    assert result.to_pandas()["age"].tolist() == [10]


def test_a_pickled_and_restored_preprocessor_still_transforms_correctly():
    import pickle

    registry = _FakeRegistry({"Doubler": _DoublingConverter})
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="Doubler", params={}, scope=[RawColumnRef(name="age")]
            )
        ]
    )
    preprocessor = SessionPreprocessor(sequence, registry)
    preprocessor.fit_transform(_split(train_ages=[1, 2, 3]))

    restored = pickle.loads(pickle.dumps(preprocessor))
    single = _dataset({"age": [5]}, {"age": {"type": "Integer", "dtype": "int64"}})

    assert restored.transform_dataset(single).to_pandas()["age"].tolist() == [10]


class _CrashesOnEmptyConverter(_DoublingConverter):
    """Mirrors sklearn transformers that reject a 0-row array, e.g. Binarizer."""

    def transform(self, x, y=None):
        if x.num_rows == 0:
            raise ValueError("Found array with 0 sample(s)")
        return super().transform(x, y)


def test_fit_transform_does_not_crash_on_an_empty_split():
    registry = _FakeRegistry({"CrashesOnEmpty": _CrashesOnEmptyConverter})
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="CrashesOnEmpty",
                params={},
                scope=[RawColumnRef(name="age")],
            )
        ]
    )
    preprocessor = SessionPreprocessor(sequence, registry)

    train = _dataset({"age": [1, 2, 3]}, {"age": {"type": "Integer", "dtype": "int64"}})
    empty_test = _dataset({"age": []}, {"age": {"type": "Integer", "dtype": "int64"}})
    split = {"train": train, "test": empty_test}

    transformed, resolved = preprocessor.fit_transform(split)

    assert transformed["train"].to_pandas()["age"].tolist() == [2, 4, 6]
    assert transformed["test"].num_rows == 0
    assert transformed["test"].column_names == transformed["train"].column_names
    assert resolved == {0: ["age"]}


def test_transform_only_does_not_crash_on_an_empty_split():
    registry = _FakeRegistry({"CrashesOnEmpty": _CrashesOnEmptyConverter})
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="CrashesOnEmpty",
                params={},
                scope=[RawColumnRef(name="age")],
            )
        ]
    )
    preprocessor = SessionPreprocessor(sequence, registry)
    preprocessor.fit_transform(
        {
            "train": _dataset(
                {"age": [1, 2, 3]}, {"age": {"type": "Integer", "dtype": "int64"}}
            )
        }
    )

    empty_test = _dataset({"age": []}, {"age": {"type": "Integer", "dtype": "int64"}})
    transformed = preprocessor.transform_only(
        {
            "train": _dataset(
                {"age": [5]}, {"age": {"type": "Integer", "dtype": "int64"}}
            ),
            "test": empty_test,
        }
    )

    assert transformed["train"].to_pandas()["age"].tolist() == [10]
    assert transformed["test"].num_rows == 0


def test_a_preprocessor_pickles_even_when_its_registry_cannot_be_pickled():
    import pickle

    class _UnpicklableRegistry(_FakeRegistry):
        def __init__(self, classes):
            super().__init__(classes)
            # Mirrors ComponentRegistry, which is not picklable because it
            # holds RelationshipManager lambdas.
            self._unpicklable = lambda: None

    registry = _UnpicklableRegistry({"Doubler": _DoublingConverter})
    sequence = ConverterSequence(
        steps=[
            ConverterStep(
                converter="Doubler", params={}, scope=[RawColumnRef(name="age")]
            )
        ]
    )
    preprocessor = SessionPreprocessor(sequence, registry)
    preprocessor.fit_transform(_split(train_ages=[1, 2, 3]))

    restored = pickle.loads(pickle.dumps(preprocessor))
    single = _dataset({"age": [5]}, {"age": {"type": "Integer", "dtype": "int64"}})

    assert restored.transform_dataset(single).to_pandas()["age"].tolist() == [10]
    assert restored.component_registry is None
