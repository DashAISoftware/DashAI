import json

import pytest
from fastapi.testclient import TestClient

from DashAI.back.dependencies.database.models import Dataset, ModelSession
from DashAI.back.job.dataset_job import DatasetJob
from DashAI.back.job.dataset_split_utils import (
    NO_OUTPUT_PLACEHOLDER_COLUMN,
    load_dataset_and_splitter,
)

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


def test_load_dataset_and_splitter_without_output_columns_treats_whole_dataset_as_x(
    client: TestClient, dataset_1: Dataset
) -> None:
    session_factory = client.app.container["session_factory"]
    component_registry = client.app.container["component_registry"]

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_1.id,
            name="No Columns Split Test",
            task_name="TabularClassificationTask",
            input_columns=[],
            output_columns=[],
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="HoldoutEvaluationStrategy",
            splits=json.dumps(HOLDOUT_SPLITS),
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)

        X, Y, splitter, _task, _prepared = load_dataset_and_splitter(
            model_session, db, component_registry
        )

        assert set(X.column_names) == {
            "SepalLengthCm",
            "SepalWidthCm",
            "PetalLengthCm",
            "PetalWidthCm",
            "Species",
        }
        # Y can't truly have 0 columns and still report the right row count
        # (a `datasets.Dataset` quirk: a 0-column Dataset always reports 0
        # rows) — it carries a reserved placeholder column instead.
        assert Y.column_names == ["__no_output_placeholder__"]
        assert len(Y) == len(X)

        x, _y, _splits = splitter.split(X, Y)
        assert len(x["train"]) + len(x["test"]) + len(x["validation"]) == len(X)

        db.delete(model_session)
        db.commit()


def test_load_dataset_and_splitter_honors_a_literal_input_columns_subset(
    client: TestClient, dataset_1: Dataset
) -> None:
    """Regression test: a plain, already-working session (no converters)
    whose `input_columns` is a genuine SUBSET of the raw dataset's columns
    must build `X` from exactly that subset — not silently overridden to
    "every raw column except output". This is exactly the bug the
    group-atom-`input_columns` fix (letting `output_columns`'s own
    resolvability decide the placeholder-vs-real split, ignoring
    `input_columns`) introduced by building the input side unconditionally
    from "everything except output," and had to be corrected to only do
    that when the literal `input_columns` selection genuinely can't be
    used as-is (a `group` atom, or a name that doesn't exist in the raw
    dataset)."""
    session_factory = client.app.container["session_factory"]
    component_registry = client.app.container["component_registry"]

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_1.id,
            name="Literal Input Subset Test",
            task_name="TabularClassificationTask",
            input_columns=[
                {"kind": "column", "name": "SepalLengthCm"},
                {"kind": "column", "name": "SepalWidthCm"},
            ],
            output_columns=[{"kind": "column", "name": "Species"}],
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="HoldoutEvaluationStrategy",
            splits=json.dumps(HOLDOUT_SPLITS),
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)

        X, Y, _splitter, _task, _prepared = load_dataset_and_splitter(
            model_session, db, component_registry
        )

        # The deselected columns (PetalLengthCm/PetalWidthCm exist in the raw
        # dataset but were never chosen as input) must NOT silently leak in.
        assert set(X.column_names) == {"SepalLengthCm", "SepalWidthCm"}
        assert "PetalLengthCm" not in X.column_names
        assert "PetalWidthCm" not in X.column_names
        assert Y.column_names == ["Species"]

        db.delete(model_session)
        db.commit()


@pytest.fixture(name="text_dataset", scope="module")
def create_text_dataset(client: TestClient, tmp_path_factory) -> Dataset:
    """A tiny dataset with a free-text column alongside a categorical
    target — the shape this whole feature exists for (a
    `BagOfWordsConverter` consuming the text column), and the only shape
    that can exercise "a raw column the task itself can't accept".
    """
    csv_path = tmp_path_factory.mktemp("text_dataset") / "reviews.csv"
    rows = ["review,rating,label"]
    for index in range(20):
        rows.append(
            f"this is review number {index},{index},{'pos' if index % 2 else 'neg'}"
        )
    csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        dataset_entry = Dataset(name="test_text_dataset", file_path="")
        db.add(dataset_entry)
        db.commit()
        db.refresh(dataset_entry)

        job = DatasetJob(
            job_type="DatasetJob",
            kwargs={
                "dataset_id": dataset_entry.id,
                "url": "",
                "params": {
                    "dataloader": "CSVDataLoader",
                    "separator": ",",
                    "name": dataset_entry.name,
                    "inferred_types": {
                        "review": {"type": "Text", "dtype": "string"},
                        "rating": {"type": "Integer", "dtype": "int64"},
                        "label": {"type": "Categorical", "dtype": "string"},
                    },
                },
                "file_path": str(csv_path),
            },
            db=db,
        )
        job.run()
        db.refresh(dataset_entry)
    return dataset_entry


def test_task_incompatible_raw_column_does_not_discard_the_real_target(
    client: TestClient, text_dataset: Dataset
) -> None:
    """Regression test: when `input_columns` is a converter `group` atom,
    the input side falls back to "every raw column except the output" — and
    that necessarily drags in the free-text column the task can't accept as
    an input, making `prepare_for_task` raise. That used to be swallowed as
    "output_columns doesn't resolve", silently replacing a perfectly valid
    target with the all-zero placeholder while the job still reported
    FINISHED (failing much later, at Run/predict/explain time, with a
    confusing "no real output column configured"). The real target must
    survive: validation is retried with an empty input selection first."""
    session_factory = client.app.container["session_factory"]
    component_registry = client.app.container["component_registry"]

    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=text_dataset.id,
            name="Text Column Target Survival Test",
            task_name="TabularClassificationTask",
            input_columns=[{"kind": "group", "converter_id": "conv_0", "slot": 0}],
            output_columns=[{"kind": "column", "name": "label"}],
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="HoldoutEvaluationStrategy",
            splits=json.dumps(HOLDOUT_SPLITS),
            converters=[
                {
                    "id": "conv_0",
                    "converter": "BagOfWordsConverter",
                    "params": {},
                    "input_scope": [{"kind": "column", "name": "review"}],
                }
            ],
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)

        _X, Y, _splitter, _task, _prepared = load_dataset_and_splitter(
            model_session, db, component_registry
        )

        assert Y.column_names == ["label"]
        assert NO_OUTPUT_PLACEHOLDER_COLUMN not in Y.column_names

        db.delete(model_session)
        db.commit()
