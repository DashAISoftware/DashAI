import json
import os

import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import SessionPreprocessingStatus
from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
from DashAI.back.dependencies.database.models import Dataset, ModelSession
from DashAI.back.job.base_job import JobError
from DashAI.back.job.dataset_split_utils import NO_OUTPUT_PLACEHOLDER_COLUMN
from DashAI.back.job.session_preprocessing_job import (
    SessionPreprocessingJob,
    get_real_input_output_columns,
    load_preprocessed_session_data,
)

INPUT_COLUMNS = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
OUTPUT_COLUMNS = ["Species"]
INPUT_COLUMN_ATOMS = [{"kind": "column", "name": col} for col in INPUT_COLUMNS]
OUTPUT_COLUMN_ATOMS = [{"kind": "column", "name": col} for col in OUTPUT_COLUMNS]


@pytest.fixture(scope="module", name="dataset_id")
def dataset_id(dataset_1: Dataset) -> int:
    """Get the dataset ID from the dataset_1 fixture (iris.csv, 150 rows)."""
    return dataset_1.id


def _create_model_session(
    client: TestClient,
    dataset_id: int,
    evaluation_strategy: str,
    splits: dict,
    converters: list,
    name: str,
    input_columns: list = INPUT_COLUMN_ATOMS,
    output_columns: list = OUTPUT_COLUMN_ATOMS,
) -> int:
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_id,
            name=name,
            task_name="TabularClassificationTask",
            input_columns=input_columns,
            output_columns=output_columns,
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy=evaluation_strategy,
            splits=json.dumps(splits),
            converters=converters,
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)
        return model_session.id


def _get_session(client: TestClient, model_session_id: int) -> ModelSession:
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        model_session = db.get(ModelSession, model_session_id)
        db.expunge(model_session)
        return model_session


def _delete_session(client: TestClient, model_session_id: int) -> None:
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        model_session = db.get(ModelSession, model_session_id)
        if model_session:
            db.delete(model_session)
            db.commit()


HOLDOUT_SPLITS = {
    "train": 0.6,
    "test": 0.2,
    "validation": 0.2,
    "is_random": True,
    "has_changed": True,
    "seed": 42,
    "shuffle": True,
    "stratify": False,
    "splitType": "random",
    "splitter_name": "HoldoutSplitter",
}

CV_SPLITS = {
    "train": 0.5,
    "test": 0.2,
    "validation": 0.3,
    "is_random": True,
    "has_changed": True,
    "seed": 42,
    "shuffle": False,
    "stratify": False,
    "splitType": "random",
    "splitter_name": "KFoldSplitter",
    "n_splits": 3,
}

STANDARD_SCALER_CONFIG = [{"converter": "StandardScaler", "params": {}, "columns": []}]


def test_holdout_preprocessing_produces_partitions_and_fitted_converters(
    client: TestClient, dataset_id: int
):
    model_session_id = _create_model_session(
        client,
        dataset_id,
        evaluation_strategy="HoldoutEvaluationStrategy",
        splits=HOLDOUT_SPLITS,
        converters=STANDARD_SCALER_CONFIG,
        name="Holdout Preprocessing Session",
    )

    SessionPreprocessingJob(kwargs={"model_session_id": model_session_id}).run()

    model_session = _get_session(client, model_session_id)
    assert model_session.preprocessing_status == SessionPreprocessingStatus.FINISHED
    assert model_session.preprocessed_path is not None

    session_dir = model_session.preprocessed_path
    total_rows = 0
    for split_name in ("train", "validation", "test"):
        x_loaded = load_dataset(os.path.join(session_dir, split_name, "x"))
        y_loaded = load_dataset(os.path.join(session_dir, split_name, "y"))
        assert set(x_loaded.column_names) == set(INPUT_COLUMNS)
        assert set(y_loaded.column_names) == set(OUTPUT_COLUMNS)
        assert len(x_loaded) > 0
        assert len(x_loaded) == len(y_loaded)
        total_rows += len(x_loaded)
    assert total_rows == 150  # iris.csv has 150 rows

    assert os.path.exists(f"{session_dir}_converters.pkl")

    _delete_session(client, model_session_id)


def test_cv_preprocessing_produces_folds_and_full_dataset(
    client: TestClient, dataset_id: int
):
    model_session_id = _create_model_session(
        client,
        dataset_id,
        evaluation_strategy="CrossValidationEvaluationStrategy",
        splits=CV_SPLITS,
        converters=STANDARD_SCALER_CONFIG,
        name="CV Preprocessing Session",
    )

    SessionPreprocessingJob(kwargs={"model_session_id": model_session_id}).run()

    model_session = _get_session(client, model_session_id)
    assert model_session.preprocessing_status == SessionPreprocessingStatus.FINISHED
    session_dir = model_session.preprocessed_path

    fold_totals = []
    for i in range(3):
        fold_train_x = load_dataset(
            os.path.join(session_dir, f"fold_{i}", "train", "x")
        )
        fold_train_y = load_dataset(
            os.path.join(session_dir, f"fold_{i}", "train", "y")
        )
        fold_test_x = load_dataset(os.path.join(session_dir, f"fold_{i}", "test", "x"))
        fold_test_y = load_dataset(os.path.join(session_dir, f"fold_{i}", "test", "y"))
        assert set(fold_train_x.column_names) == set(INPUT_COLUMNS)
        assert set(fold_train_y.column_names) == set(OUTPUT_COLUMNS)
        assert len(fold_train_x) > 0
        assert len(fold_train_x) == len(fold_train_y)
        assert len(fold_test_x) > 0
        assert len(fold_test_x) == len(fold_test_y)
        fold_totals.append(len(fold_train_x) + len(fold_test_x))

    # every fold's train+test covers the whole dataset.
    assert all(total == fold_totals[0] for total in fold_totals)

    full_train_x = load_dataset(os.path.join(session_dir, "full_dataset", "train", "x"))
    full_train_y = load_dataset(os.path.join(session_dir, "full_dataset", "train", "y"))
    assert len(full_train_x) == fold_totals[0]
    assert len(full_train_x) == len(full_train_y)
    # the full_dataset fold's test partition is empty, so it's never saved.
    assert not os.path.exists(os.path.join(session_dir, "full_dataset", "test"))

    assert os.path.exists(f"{session_dir}_converters.pkl")

    _delete_session(client, model_session_id)


def test_holdout_preprocessing_saves_separate_x_and_y_files(
    client: TestClient, dataset_id: int
):
    model_session_id = _create_model_session(
        client,
        dataset_id,
        evaluation_strategy="HoldoutEvaluationStrategy",
        splits=HOLDOUT_SPLITS,
        converters=[
            {
                "id": "conv_0",
                "converter": "StandardScaler",
                "params": {},
                "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
            }
        ],
        name="Two File Save Test",
        input_columns=[{"kind": "group", "converter_id": "conv_0", "slot": 0}],
        output_columns=[{"kind": "column", "name": "Species"}],
    )

    SessionPreprocessingJob(kwargs={"model_session_id": model_session_id}).run()

    model_session = _get_session(client, model_session_id)
    session_dir = model_session.preprocessed_path

    x_train = load_dataset(os.path.join(session_dir, "train", "x"))
    y_train = load_dataset(os.path.join(session_dir, "train", "y"))
    assert x_train.column_names == ["SepalLengthCm"]
    # `input_columns` includes a `group` atom here, but `output_columns` is a
    # plain literal atom — `load_dataset_and_splitter` (dataset_split_utils.py)
    # decides the placeholder-vs-real split based on `output_columns`'s own
    # resolvability alone, never on `input_columns`'s (the main use case this
    # whole feature exists for: a converter's group used as input features).
    # `y` therefore carries the session's REAL output values, not a
    # placeholder — `resolve_final_columns` narrows the saved X down to the
    # real group-atom columns (`["SepalLengthCm"]` above) exactly the same
    # way regardless.
    assert y_train.column_names == ["Species"]
    assert len(y_train) == len(x_train)
    assert set(y_train["Species"]) <= {
        "Iris-setosa",
        "Iris-versicolor",
        "Iris-virginica",
    }

    _delete_session(client, model_session_id)


def test_cv_preprocessing_resolves_group_atom_per_fold(
    client: TestClient, dataset_id: int
):
    """A converter's group, used as the session's final input selection,
    resolves independently per fold (see Task 3's per-fold group registry)."""
    model_session_id = _create_model_session(
        client,
        dataset_id,
        evaluation_strategy="CrossValidationEvaluationStrategy",
        splits=CV_SPLITS,
        converters=[
            {
                "id": "conv_0",
                "converter": "StandardScaler",
                "params": {},
                "input_scope": [{"kind": "column", "name": "SepalLengthCm"}],
            }
        ],
        name="CV Group Resolution Test",
        input_columns=[{"kind": "group", "converter_id": "conv_0", "slot": 0}],
        output_columns=[{"kind": "column", "name": "Species"}],
    )

    SessionPreprocessingJob(kwargs={"model_session_id": model_session_id}).run()

    model_session = _get_session(client, model_session_id)
    session_dir = model_session.preprocessed_path

    for i in range(3):
        x_train = load_dataset(os.path.join(session_dir, f"fold_{i}", "train", "x"))
        assert x_train.column_names == ["SepalLengthCm"]

    _delete_session(client, model_session_id)


def test_loading_survives_a_converter_that_renames_input_columns(
    client: TestClient, dataset_id: int
):
    """Regression test: a converter that changes the input columns'
    names/count (e.g. PCA, which replaces the 4 iris columns with N
    components) must load correctly once `model_session.input_columns` is
    updated to the post-conversion names — exactly what the wizard's
    Columns step does (it only ever runs *after* preprocessing, so it never
    sees the pre-conversion names in the first place). Preprocessing itself
    still runs with the original 4 iris columns as input, same as the real
    wizard: converters apply before the Columns step has set anything.

    `_load_partition` used to select `input_columns` directly rather than
    inferring "everything except output" — that heuristic used to let a
    converter's leftover original column (e.g. BagOfWords appending
    `bow_<word>` next to the untouched source text) silently leak into
    training data the user never selected.

    Under the group-atoms architecture, a session references PCA's
    post-conversion columns as a `group` atom (`{"kind": "group",
    "converter_id": ..., "slot": 0}`) — never a literal name nobody could
    have typed in before PCA ever ran — and `SessionPreprocessingJob.run()`
    resolves it (via `resolve_final_columns`) against the real columns PCA
    actually produced for this partition, at *save* time, filtering the
    saved `x` file down to just those instead of leaving PCA's untouched
    leftover columns (or the whole raw dataset) sitting in it.
    `output_columns` here is a plain literal atom (`Species`), so
    `load_dataset_and_splitter` resolves the split for real —
    `input_columns`'s own resolvability no longer matters to that decision
    — and `y` carries the session's real output values, not a
    placeholder."""
    pca_config = [
        {
            "id": "conv_0",
            "converter": "PCA",
            "params": {"n_components": 2},
            "input_scope": [{"kind": "column", "name": col} for col in INPUT_COLUMNS],
        }
    ]
    model_session_id = _create_model_session(
        client,
        dataset_id,
        evaluation_strategy="HoldoutEvaluationStrategy",
        splits=HOLDOUT_SPLITS,
        converters=pca_config,
        name="PCA Preprocessing Session",
        input_columns=[{"kind": "group", "converter_id": "conv_0", "slot": 0}],
    )

    SessionPreprocessingJob(kwargs={"model_session_id": model_session_id}).run()

    model_session = _get_session(client, model_session_id)
    assert model_session.preprocessing_status == SessionPreprocessingStatus.FINISHED

    x, y = load_preprocessed_session_data(model_session)
    # PCA replaced the 4 original input columns with 2 components.
    assert set(x["train"].column_names) == {"pca0", "pca1"}
    assert y["train"].column_names == ["Species"]
    assert len(x["train"]) == len(y["train"])
    assert set(y["train"]["Species"]) <= {
        "Iris-setosa",
        "Iris-versicolor",
        "Iris-virginica",
    }

    _delete_session(client, model_session_id)


def test_loading_excludes_a_converters_leftover_original_column(
    client: TestClient, dataset_id: int
):
    """Regression test: a converter that *appends* a new column instead of
    replacing the original (e.g. `LabelEncoder` leaving `Species` next to
    the `le_Species` it adds, or `BagOfWords` leaving the source text next
    to its `bow_<word>` columns) must not leak that untouched original
    column into the saved training data — the session's own final input
    selection is resolved (via `resolve_final_columns`) at *save* time
    inside `run()`, narrowing the saved `x` file down to exactly the chosen
    columns. Here `Species` (the label) is neither the chosen input (the 4
    numeric columns, untouched by this converter) nor the chosen output
    (`le_Species`) — it must not appear in `x` at all.

    `le_Species` doesn't exist in the raw dataset before `LabelEncoder`
    actually runs, so `load_dataset_and_splitter` still falls back to a
    placeholder Y — its own `output_columns` resolvability (the only thing
    that decision depends on) genuinely fails here, unrelated to
    `input_columns` — so `y` still carries only the placeholder column;
    what this test verifies is `x`'s leftover-column exclusion."""
    label_encoder_config = [
        {"converter": "LabelEncoder", "params": {}, "columns": ["Species"]}
    ]
    model_session_id = _create_model_session(
        client,
        dataset_id,
        evaluation_strategy="HoldoutEvaluationStrategy",
        splits=HOLDOUT_SPLITS,
        converters=label_encoder_config,
        name="LabelEncoder Leftover Column Session",
        input_columns=INPUT_COLUMN_ATOMS,
        output_columns=[{"kind": "column", "name": "le_Species"}],
    )

    SessionPreprocessingJob(kwargs={"model_session_id": model_session_id}).run()

    model_session = _get_session(client, model_session_id)
    assert model_session.preprocessing_status == SessionPreprocessingStatus.FINISHED

    x, y = load_preprocessed_session_data(model_session)
    assert set(x["train"].column_names) == set(INPUT_COLUMNS)
    assert "Species" not in x["train"].column_names
    assert "le_Species" not in x["train"].column_names
    assert y["train"].column_names == [NO_OUTPUT_PLACEHOLDER_COLUMN]
    assert len(x["train"]) == len(y["train"])

    _delete_session(client, model_session_id)


def test_output_columns_group_atom_is_rejected(client: TestClient, dataset_id: int):
    """A session's own `output_columns` must always be a literal `column`
    atom, never a `group` atom: a converter-produced target value cannot
    exist yet at split time (the raw dataset is split into train/test
    *before* any converter runs). `run()` must reject this configuration
    loudly instead of silently persisting a placeholder target."""
    model_session_id = _create_model_session(
        client,
        dataset_id,
        evaluation_strategy="HoldoutEvaluationStrategy",
        splits=HOLDOUT_SPLITS,
        converters=[
            {
                "id": "conv_0",
                "converter": "LabelEncoder",
                "params": {},
                "input_scope": [{"kind": "column", "name": "Species"}],
            }
        ],
        name="Output Group Atom Rejected Test",
        input_columns=INPUT_COLUMN_ATOMS,
        output_columns=[{"kind": "group", "converter_id": "conv_0", "slot": 0}],
    )

    with pytest.raises(JobError, match="group"):
        SessionPreprocessingJob(kwargs={"model_session_id": model_session_id}).run()

    model_session = _get_session(client, model_session_id)
    assert model_session.preprocessing_status == SessionPreprocessingStatus.ERROR
    assert model_session.preprocessed_path is None

    _delete_session(client, model_session_id)


def test_preprocessing_fit_failure_sets_error_status(
    client: TestClient, dataset_id: int
):
    # n_components > number of input columns (4): sklearn's PCA.fit raises.
    pca_config = [{"converter": "PCA", "params": {"n_components": 10}, "columns": []}]
    model_session_id = _create_model_session(
        client,
        dataset_id,
        evaluation_strategy="HoldoutEvaluationStrategy",
        splits=HOLDOUT_SPLITS,
        converters=pca_config,
        name="Preprocessing Error Session",
    )

    with pytest.raises(JobError):
        SessionPreprocessingJob(kwargs={"model_session_id": model_session_id}).run()

    model_session = _get_session(client, model_session_id)
    assert model_session.preprocessing_status == SessionPreprocessingStatus.ERROR
    assert model_session.preprocessed_path is None

    _delete_session(client, model_session_id)


def test_get_real_input_output_columns_reads_from_saved_partition(
    client: TestClient, dataset_id: int
):
    """When the session has converters (so `preprocessed_path` is set),
    `get_real_input_output_columns` must return exactly the column names
    saved in the reference partition's `x`/`y` files — the single
    production resolution `predict_job.py`/`explainer_job.py` rely on."""
    model_session_id = _create_model_session(
        client,
        dataset_id,
        evaluation_strategy="HoldoutEvaluationStrategy",
        splits=HOLDOUT_SPLITS,
        converters=STANDARD_SCALER_CONFIG,
        name="Real Columns From Partition Test",
    )

    SessionPreprocessingJob(kwargs={"model_session_id": model_session_id}).run()

    model_session = _get_session(client, model_session_id)
    session_dir = model_session.preprocessed_path
    x_reference = load_dataset(os.path.join(session_dir, "train", "x"))
    y_reference = load_dataset(os.path.join(session_dir, "train", "y"))

    input_columns, output_columns = get_real_input_output_columns(model_session)
    assert input_columns == list(x_reference.column_names)
    assert output_columns == list(y_reference.column_names)

    _delete_session(client, model_session_id)


def test_get_real_input_output_columns_extracts_atom_names_without_converters(
    client: TestClient, dataset_id: int
):
    """When the session has no converters at all (so `preprocessed_path` is
    never set), every atom is necessarily a literal `column` atom — the real
    names are just each atom's own `name`, no partition to read."""
    model_session_id = _create_model_session(
        client,
        dataset_id,
        evaluation_strategy="HoldoutEvaluationStrategy",
        splits=HOLDOUT_SPLITS,
        converters=[],
        name="Real Columns No Converters Test",
    )

    model_session = _get_session(client, model_session_id)
    assert model_session.preprocessed_path is None

    input_columns, output_columns = get_real_input_output_columns(model_session)
    assert input_columns == INPUT_COLUMNS
    assert output_columns == OUTPUT_COLUMNS

    _delete_session(client, model_session_id)
