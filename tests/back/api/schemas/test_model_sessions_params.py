import pytest
from pydantic import ValidationError

from DashAI.back.api.api_v1.schemas.model_sessions_params import (
    ColumnAtom,
    ModelSessionParams,
    SessionConverterParams,
)


def test_column_atom_accepts_column_kind():
    atom = ColumnAtom(kind="column", name="sepal_length")
    assert atom.kind == "column"
    assert atom.name == "sepal_length"


def test_column_atom_accepts_group_kind():
    atom = ColumnAtom(kind="group", converter_id="conv_0", slot=0)
    assert atom.kind == "group"
    assert atom.converter_id == "conv_0"
    assert atom.slot == 0


def test_column_atom_rejects_unknown_kind():
    with pytest.raises(ValidationError):
        ColumnAtom(kind="unknown", name="x")


def test_session_converter_params_has_id_and_input_scope():
    params = SessionConverterParams(
        id="conv_0",
        converter="StandardScaler",
        params={},
        input_scope=[{"kind": "column", "name": "sepal_length"}],
    )
    assert params.id == "conv_0"
    assert params.input_scope[0].kind == "column"
    assert params.input_scope[0].name == "sepal_length"
    assert params.target_column is None


def test_model_session_params_input_columns_are_atoms():
    params = ModelSessionParams(
        dataset_id=1,
        task_name="TabularClassificationTask",
        name="Test",
        input_columns=[{"kind": "column", "name": "a"}],
        output_columns=[{"kind": "group", "converter_id": "conv_0", "slot": 0}],
        train_metrics=[],
        validation_metrics=[],
        test_metrics=[],
        evaluation_strategy="HoldoutEvaluationStrategy",
        splits="{}",
    )
    assert params.input_columns[0].kind == "column"
    assert params.output_columns[0].kind == "group"
