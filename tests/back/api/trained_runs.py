"""Sessions with runs fitted by hand, shared by the package and session tests.

Training through ModelJob is slow and not what those tests are about, so the
models are fitted directly and stored as finished runs: a classifier behind a
Binarizer preprocessing step, so a fitted preprocessor exists, and a plain
regressor.
"""

import json
import random
from pathlib import Path

import pandas as pd

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset
from DashAI.back.dependencies.database.models import Metric, ModelSession, Run
from DashAI.back.job.predict_job import run_manual_prediction
from DashAI.back.preprocessing.session_preprocessor import load_final_preprocessor

RAW_INPUT_COLUMNS = [
    "SepalLengthCm",
    "SepalWidthCm",
    "PetalLengthCm",
    "PetalWidthCm",
]
DERIVED_COLUMN = "bin_SepalLengthCm"
CLASS_COLUMN = "Species"
REGRESSION_INPUTS = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm"]
REGRESSION_TARGET = "PetalWidthCm"
IRIS_ROWS = 150
IRIS_CSV = Path(__file__).parent / "iris.csv"
SPLITS = {
    "splitter_name": "HoldoutSplitter",
    "splitType": "random",
    "train": 0.5,
    "test": 0.2,
    "validation": 0.3,
    "is_random": True,
    "has_changed": True,
    "seed": 42,
    "shuffle": True,
    "stratify": False,
}
BINARIZER_STEP = {
    "converter": "Binarizer",
    "params": {"threshold": 3.0},
    "scope": [{"kind": "raw", "name": "SepalLengthCm"}],
}


def split_indexes():
    rows = list(range(IRIS_ROWS))
    random.Random(875).shuffle(rows)
    return {
        "train_indexes": sorted(rows[:75]),
        "test_indexes": sorted(rows[75:105]),
        "val_indexes": sorted(rows[105:]),
    }


def new_run(session_factory, session_id, model_name, parameters, path=None):
    """Store a run; finished with ``path`` as its model, else never trained."""
    with session_factory() as db:
        run = Run(
            model_session_id=session_id,
            model_name=model_name,
            parameters=parameters,
            optimizer_name="OptunaOptimizer",
            optimizer_parameters={
                "n_trials": 1,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            name=f"Package {model_name}",
            goal_metric="Accuracy",
            run_path=str(path) if path else None,
            split_indexes=json.dumps(split_indexes()),
        )
        if path:
            run.set_status_as_finished()
        db.add(run)
        db.commit()
        db.refresh(run)
        return run.id


def fit_classifier_behind_preprocessing(client, dataset, model_dir, session_name):
    """A KNN on the Binarizer output of a session created through the API."""
    response = client.post(
        "/api/v1/model-session/",
        json={
            "dataset_id": dataset.id,
            "task_name": "TabularClassificationTask",
            "name": session_name,
            "input_columns": [],
            "output_columns": [CLASS_COLUMN],
            "train_metrics": [],
            "validation_metrics": [],
            "test_metrics": [],
            "evaluation_strategy": "HoldoutEvaluationStrategy",
            "splits": json.dumps(SPLITS),
            "preprocessing": [BINARIZER_STEP],
            "input_column_refs": [{"kind": "group", "step": 0}],
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["preprocessing_status"] == "ready", body

    registry = client.app.container["component_registry"]
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = db.get(ModelSession, body["id"])
        db.expunge(session)

    raw = load_dataset(str(Path(dataset.file_path) / "dataset"))
    preprocessor = load_final_preprocessor(session)
    task = registry["TabularClassificationTask"]["class"]()
    transformed = task.prepare_for_task(
        preprocessor.transform_dataset(raw), [DERIVED_COLUMN], [CLASS_COLUMN]
    )
    parameters = {"n_neighbors": 3, "weights": "uniform", "algorithm": "auto"}
    model = registry["KNeighborsClassifier"]["class"](**parameters)
    train = transformed.select(split_indexes()["train_indexes"])
    model.train(
        train.select_columns([DERIVED_COLUMN]), train.select_columns([CLASS_COLUMN])
    )
    path = Path(model_dir) / "model"
    model.save(str(path))
    return new_run(
        session_factory, session.id, "KNeighborsClassifier", parameters, path
    )


def new_regression_session(client, dataset, session_name):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        session = ModelSession(
            dataset_id=dataset.id,
            name=session_name,
            task_name="RegressionTask",
            input_columns=REGRESSION_INPUTS,
            output_columns=[REGRESSION_TARGET],
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="HoldoutEvaluationStrategy",
            splits=json.dumps(SPLITS),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session.id


def fit_regressor(client, dataset, model_dir, session_name):
    """A linear regression in a session without preprocessing."""
    registry = client.app.container["component_registry"]
    session_factory = client.app.container["session_factory"]
    session_id = new_regression_session(client, dataset, session_name)

    raw = load_dataset(str(Path(dataset.file_path) / "dataset"))
    task = registry["RegressionTask"]["class"]()
    prepared = task.prepare_for_task(raw, REGRESSION_INPUTS, [REGRESSION_TARGET])
    model = registry["LinearRegression"]["class"]()
    train = prepared.select(split_indexes()["train_indexes"])
    model.train(
        train.select_columns(REGRESSION_INPUTS),
        train.select_columns([REGRESSION_TARGET]),
    )
    path = Path(model_dir) / "model"
    model.save(str(path))
    return new_run(session_factory, session_id, "LinearRegression", {}, path)


def add_metrics(session_factory, run_id):
    """Final metrics on every split plus one per-trial row, like a real job."""
    rows = [
        (SplitEnum.TRAIN, LevelEnum.LAST, 0.97),
        (SplitEnum.VALIDATION, LevelEnum.LAST, 0.95),
        (SplitEnum.TEST, LevelEnum.LAST, 0.93),
        (SplitEnum.VALIDATION, LevelEnum.TRIAL, 0.9),
    ]
    with session_factory() as db:
        db.add_all(
            Metric(
                run_id=run_id,
                split=split,
                level=level,
                name="Accuracy",
                value=value,
                step=0,
            )
            for split, level, value in rows
        )
        db.commit()


def predicted_in_app(client, run_id, columns, n_rows):
    rows = pd.read_csv(IRIS_CSV).head(n_rows)[columns].to_dict(orient="records")
    _, preview = run_manual_prediction(
        run_id, rows, client.app.container["session_factory"]
    )
    return [row[-1] for row in preview]
