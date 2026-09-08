import pandas as pd
import pyarrow as pa
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import (
    load_dataset,
    save_dataset,
    to_dashai_dataset,
    transform_dataset_with_schema,
)
from DashAI.back.types.utils import (
    get_types_from_arrow_metadata,
    save_types_in_arrow_metadata,
)
from DashAI.back.types.value_types import Date, Text


def _table_with_date_type(fmt):
    table = pa.table({"when": pa.array(["2020-01-31", "2020-02-29"])})
    date_type = Date(arrow_type=pa.string(), format=fmt)
    return save_types_in_arrow_metadata(table, {"when": date_type.to_string()})


def test_date_type_survives_the_arrow_metadata_round_trip():
    table = _table_with_date_type("%d/%m/%Y")

    restored = get_types_from_arrow_metadata(table)

    assert isinstance(restored["when"], Date)
    assert restored["when"].format == "%d/%m/%Y"


def test_date_without_a_stored_format_falls_back_to_iso():
    table = pa.table({"when": pa.array(["2020-01-31"])})
    table = save_types_in_arrow_metadata(
        table, {"when": {"type": "Date", "dtype": "string"}}
    )

    restored = get_types_from_arrow_metadata(table)

    assert isinstance(restored["when"], Date)
    assert restored["when"].format == "%Y-%m-%d"


def test_a_date_column_survives_a_real_save_and_load(tmp_path):
    # The end to end version of the round trip: a schema carrying a Date goes
    # through transform, save and load, and comes back a Date with its format
    # and its original text intact.
    frame = pd.DataFrame(
        {"when": ["31/01/2020", "15/02/2020", "03/03/2020"], "sales": [100, 120, 115]}
    )
    schema = {
        "when": {"type": "Date", "dtype": "%d/%m/%Y"},
        "sales": {"type": "Integer", "dtype": "int64"},
    }

    dataset = transform_dataset_with_schema(to_dashai_dataset(frame), schema)
    save_dataset(dataset, tmp_path / "dataset")
    restored = load_dataset(str(tmp_path / "dataset"))

    assert isinstance(restored.types["when"], Date)
    assert restored.types["when"].format == "%d/%m/%Y"
    # Text preserved byte for byte, since nothing parses at rest.
    assert restored.arrow_table.column("when").to_pylist() == [
        "31/01/2020",
        "15/02/2020",
        "03/03/2020",
    ]


def test_text_columns_are_unaffected():
    table = pa.table({"note": pa.array(["hello"])})
    table = save_types_in_arrow_metadata(
        table, {"note": Text(arrow_type=pa.string()).to_string()}
    )

    restored = get_types_from_arrow_metadata(table)

    assert isinstance(restored["note"], Text)


def test_a_date_survives_a_schema_built_from_to_string():
    # Two dict shapes reach transform_dataset_with_schema. Inference and
    # get_columns_spec put the strptime format in "dtype"; to_string() puts it
    # in "format" and leaves "dtype" as the arrow type. predict_job and
    # dataset_job build their schema the second way, which used to overwrite
    # the format with the literal "string".
    frame = pd.DataFrame({"when": ["31/01/2020", "15/02/2020"]})
    dataset = transform_dataset_with_schema(
        to_dashai_dataset(frame), {"when": {"type": "Date", "dtype": "%d/%m/%Y"}}
    )

    schema = {col: typ.to_string() for col, typ in dataset.types.items()}
    reloaded = transform_dataset_with_schema(dataset, schema)

    assert reloaded.types["when"].format == "%d/%m/%Y"


def test_a_date_without_a_resolvable_format_is_refused():
    # Better a named error than the AttributeError raised deep in
    # arrow_to_dashai_types when it is handed a format of None.
    frame = pd.DataFrame({"when": ["31/01/2020"]})

    with pytest.raises(ValueError, match="carries no format"):
        transform_dataset_with_schema(
            to_dashai_dataset(frame), {"when": {"type": "Date", "dtype": None}}
        )
