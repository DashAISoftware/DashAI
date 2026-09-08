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
