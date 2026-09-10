"""End to end regression net for the ModelJob cross-validation paths.

``test_model_job_orchestration.py`` pins the holdout path. Nothing pins the
fold paths: the only end-to-end cross-validated run in the suite is a fixture
in ``test_reports_api.py`` that asserts the run reached ``FINISHED`` and
nothing else, and it configures no optimizer, so cross-validation combined with
a hyperparameter search never executes anywhere.

These tests pin the observable contract of a cross-validated run: the shape of
the persisted split indexes, which rows each partition holds, how many times
the model is actually fitted and on what, the fold level ``Metric`` rows and
their aggregation, the single saved artifact, and the verbatim text of every
error branch.

They deliberately assert exact values rather than ``status in [...]``: a run
that quietly stops doing part of its work still finishes.
"""

import json
import os

import joblib
import numpy as np
import pytest
from datasets import ClassLabel, Value
from fastapi.testclient import TestClient

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.core.enums.status import RunStatus
from DashAI.back.core.schema_fields import BaseSchema, int_field, schema_field
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dependencies.database.models import Dataset, Metric, ModelSession, Run
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.evaluation.cv import CrossValidationEvaluationStrategy
from DashAI.back.evaluation.holdout import HoldoutEvaluationStrategy
from DashAI.back.job.base_job import JobError
from DashAI.back.job.model_job import ModelJob
from DashAI.back.metrics.base_metric import BaseMetric
from DashAI.back.models.base_model import BaseModel
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer
from DashAI.back.splitters.holdout import HoldoutSplitter
from DashAI.back.splitters.k_fold import KFoldSplitter
from DashAI.back.splitters.stratified_k_fold import StratifiedKFoldSplitter
from DashAI.back.tasks.base_task import BaseTask

INPUT_COLUMNS = ["SepalLengthCm", "SepalWidthCm"]
OUTPUT_COLUMNS = ["Species"]

#: Rows in ``tests/back/api/iris.csv``.
DATASET_ROWS = 150

#: Every ``train`` call any model instance makes, in order. A module level list
#: rather than instance state: cross-validation reuses one model instance across
#: folds, so counting on the instance could not tell several fits apart from one.
FIT_LOG: list = []


def _squash(text: str) -> str:
    """Collapse whitespace, so a triple quoted message can be compared whole.

    Several messages on this path are written as triple quoted f-strings, so
    they carry the newline and the source indentation literally. Comparing the
    squashed form pins the whole sentence instead of a fragment of it, without
    pinning the indentation of the file it came from.
    """
    return " ".join(text.split())


class CvTask(BaseTask):
    name: str = "CvTask"
    metadata: dict = {
        "inputs_types": [ClassLabel, Value],
        "outputs_types": [ClassLabel],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }

    def prepare_for_task(self, dataset, input_columns=None, output_columns=None):
        return dataset

    def num_labels(self, dataset, output_column):
        return 3


class CountingModel(BaseModel):
    """Model that records every fit and predicts from its own input rows.

    ``predict`` returns the first input column verbatim, so the paired metric
    below scores every partition differently. That matters for the aggregation
    assertions: with a constant score the standard deviation is zero whether it
    was computed or hardcoded.
    """

    COMPATIBLE_COMPONENTS = ["CvTask"]

    def __init__(self, **kwargs):
        self.trained_with = None

    def save(self, filename):
        joblib.dump({"trained_with": self.trained_with}, filename)

    def load(self, filename):
        return joblib.load(filename)

    def predict(self, x):
        column = x.column_names[0]
        return [float(value) for value in x[column]]

    def train(self, x_train, y_train, x_validation=None, y_validation=None):
        self.trained_with = {
            "train": x_train.shape[0],
            "validation": None if x_validation is None else x_validation.shape[0],
        }
        FIT_LOG.append(dict(self.trained_with))
        return self

    def prepare_dataset(self, dataset, is_fit=False):
        return dataset


class TunableSchema(BaseSchema):
    n_estimators: schema_field(
        int_field(gt=0),
        placeholder=2,
        description="Number of estimators.",
    )  # type: ignore


class TunableCvModel(CountingModel):
    """A ``CountingModel`` with one optimizable parameter, for the search branch."""

    COMPATIBLE_COMPONENTS = ["CvTask"]
    SCHEMA = TunableSchema

    def __init__(self, n_estimators=2, **kwargs):
        super().__init__(**kwargs)
        self.n_estimators = n_estimators


class MeanPredictionMetric(BaseMetric):
    """Mean of the predicted values.

    Deterministic and different for every partition, without depending on how
    the target column happens to be encoded.
    """

    COMPATIBLE_COMPONENTS = ["CvTask"]
    MAXIMIZE = True

    @staticmethod
    def score(true_labels, probs_pred_labels):
        return float(np.mean(np.asarray(probs_pred_labels, dtype=float)))


@pytest.fixture(scope="module", name="cv_registry", autouse=True)
def setup_cv_registry(client):
    container = client.app.container
    sentinel = object()
    services = container._services
    old = services.get("component_registry", sentinel)

    services["component_registry"] = ComponentRegistry(
        initial_components=[
            CvTask,
            CountingModel,
            TunableCvModel,
            MeanPredictionMetric,
            CSVDataLoader,
            ModelJob,
            OptunaOptimizer,
            HoldoutSplitter,
            HoldoutEvaluationStrategy,
            KFoldSplitter,
            StratifiedKFoldSplitter,
            CrossValidationEvaluationStrategy,
        ]
    )
    yield services["component_registry"]
    if old is sentinel:
        del services["component_registry"]
    else:
        services["component_registry"] = old


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _make_session(
    client: TestClient,
    dataset_id: int,
    name: str,
    splits: dict,
    strategy: str = "CrossValidationEvaluationStrategy",
) -> int:
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=dataset_id,
            name=name,
            task_name="CvTask",
            input_columns=INPUT_COLUMNS,
            output_columns=OUTPUT_COLUMNS,
            train_metrics=["MeanPredictionMetric"],
            validation_metrics=["MeanPredictionMetric"],
            test_metrics=["MeanPredictionMetric"],
            evaluation_strategy=strategy,
            splits=json.dumps(splits),
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)
        return model_session.id


def _kfold_splits(n_splits: int = 3, test_size: float = 0.2, **extra) -> dict:
    payload = {
        "splitter_name": "KFoldSplitter",
        "splitType": "cv",
        "n_splits": n_splits,
        "shuffle": True,
        "random_state": 42,
        "test_size": test_size,
    }
    payload.update(extra)
    return payload


def _make_run(client: TestClient, model_session_id: int, **overrides) -> int:
    session_factory = client.app.container["session_factory"]
    fields = {
        "model_name": "CountingModel",
        "parameters": {},
        "optimizer_name": "",
        "optimizer_parameters": {},
        "goal_metric": "",
        "name": f"CvRun-{model_session_id}",
    }
    fields.update(overrides)
    with session_factory() as db:
        run = Run(model_session_id=model_session_id, **fields)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run.id


def _run_job(run_id: int) -> list:
    """Run the job and return the fits it performed, in order."""
    FIT_LOG.clear()
    ModelJob(run_id=run_id).run()
    return list(FIT_LOG)


def _reload(client: TestClient, run_id: int) -> Run:
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        return db.get(Run, run_id)


def _metrics(client: TestClient, run_id: int, **filters) -> list:
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        return db.query(Metric).filter_by(run_id=run_id, **filters).all()


def _fold_values(client: TestClient, run_id: int, level, split) -> list:
    """Fold metric values for one level and split, ordered by fold index."""
    rows = _metrics(client, run_id, level=level, split=split)
    return [row.value for row in sorted(rows, key=lambda row: row.fold_index)]


# --------------------------------------------------------------------------- #
# A plain cross-validated run: 3 folds over 120 rows, 30 reserved
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module", name="cv_run")
def run_a_cross_validated_job(client: TestClient, dataset_1: Dataset) -> dict:
    session_id = _make_session(
        client, dataset_1.id, "CvSession", _kfold_splits(n_splits=3, test_size=0.2)
    )
    run_id = _make_run(client, session_id, name="PlainCvRun")
    fits = _run_job(run_id)
    return {"run_id": run_id, "fits": fits}


def test_a_cross_validated_run_reaches_finished(client: TestClient, cv_run: dict):
    assert _reload(client, cv_run["run_id"]).status == RunStatus.FINISHED


def test_a_cross_validated_run_stamps_its_timestamps(client: TestClient, cv_run: dict):
    run = _reload(client, cv_run["run_id"])

    assert run.start_time is not None
    assert run.end_time is not None
    assert run.end_time >= run.start_time


def test_the_split_indexes_name_every_fold_and_the_full_dataset(
    client: TestClient, cv_run: dict
):
    """The shape a fold splitter persists, which is not the holdout shape.

    A holdout run stores one flat ``{train,test,val}_indexes`` mapping. Every
    consumer of ``Run.split_indexes`` has to tell the two apart, which is what
    ``BaseSplitter.explainable_partitions`` exists for.
    """
    split_indexes = json.loads(_reload(client, cv_run["run_id"]).split_indexes)

    assert set(split_indexes) == {"fold_0", "fold_1", "fold_2", "full_dataset"}


def test_every_fold_names_a_train_and_a_validation_partition(
    client: TestClient, cv_run: dict
):
    split_indexes = json.loads(_reload(client, cv_run["run_id"]).split_indexes)

    for name in ("fold_0", "fold_1", "fold_2"):
        assert set(split_indexes[name]) == {"train_indexes", "validation_indexes"}, name


def test_the_full_dataset_entry_names_a_train_and_a_test_partition(
    client: TestClient, cv_run: dict
):
    """The trailing entry is not a fold: it fits the kept model and scores it."""
    split_indexes = json.loads(_reload(client, cv_run["run_id"]).split_indexes)

    assert set(split_indexes["full_dataset"]) == {"train_indexes", "test_indexes"}
    assert len(split_indexes["full_dataset"]["train_indexes"]) == 120
    assert len(split_indexes["full_dataset"]["test_indexes"]) == 30


def test_the_reserved_rows_reach_no_fold(client: TestClient, cv_run: dict):
    """The assertion the whole reserved-rows design exists for.

    If a reserved row leaked into any fold, the score reported on the reserved
    rows would be measured on data the folds had already seen, and nothing
    about that failure raises.
    """
    split_indexes = json.loads(_reload(client, cv_run["run_id"]).split_indexes)
    reserved = set(split_indexes["full_dataset"]["test_indexes"])

    for name in ("fold_0", "fold_1", "fold_2"):
        fold = split_indexes[name]
        seen = set(fold["train_indexes"]) | set(fold["validation_indexes"])
        assert reserved.isdisjoint(seen), name


def test_every_pooled_row_is_validated_exactly_once(client: TestClient, cv_run: dict):
    """K-fold's defining property, checked on the rows it actually produced."""
    split_indexes = json.loads(_reload(client, cv_run["run_id"]).split_indexes)
    pool = split_indexes["full_dataset"]["train_indexes"]

    validated = [
        index
        for name in ("fold_0", "fold_1", "fold_2")
        for index in split_indexes[name]["validation_indexes"]
    ]

    assert sorted(validated) == sorted(pool)
    assert len(validated) == len(set(validated))


def test_the_pool_and_the_reserved_rows_cover_the_dataset(
    client: TestClient, cv_run: dict
):
    split_indexes = json.loads(_reload(client, cv_run["run_id"]).split_indexes)
    pool = set(split_indexes["full_dataset"]["train_indexes"])
    reserved = set(split_indexes["full_dataset"]["test_indexes"])

    assert pool.isdisjoint(reserved)
    assert pool | reserved == set(range(DATASET_ROWS))


def test_the_model_is_fitted_once_per_fold_and_once_more_on_the_whole_pool(
    cv_run: dict,
):
    """Three fold fits and a final refit, and only the refit is kept."""
    fits = cv_run["fits"]

    assert len(fits) == 4
    assert [fit["train"] for fit in fits] == [80, 80, 80, 120]


def test_no_cross_validated_fit_receives_validation_data(cv_run: dict):
    """A fold is scored on its validation partition, so it is not fitted on it.

    The holdout strategy does hand validation data to ``train`` (models use it
    for early stopping); the fold strategy deliberately does not, and the
    trailing entry has no validation partition to hand over at all.
    """
    assert [fit["validation"] for fit in cv_run["fits"]] == [None, None, None, None]


def test_the_saved_artifact_is_the_refitted_model_and_not_a_fold(
    client: TestClient, cv_run: dict
):
    """One model is saved, and it is the one fitted on every pooled row."""
    run = _reload(client, cv_run["run_id"])

    assert run.run_path is not None
    assert run.run_path.endswith(str(run.id))
    assert os.path.exists(run.run_path)
    assert joblib.load(run.run_path)["trained_with"]["train"] == 120


def test_a_fold_metric_is_written_for_every_fold_and_every_scored_split(
    client: TestClient, cv_run: dict
):
    rows = _metrics(client, cv_run["run_id"], level=LevelEnum.FOLD)

    by_split = {}
    for row in rows:
        by_split.setdefault(row.split, []).append(row)

    assert set(by_split) == {SplitEnum.TRAIN, SplitEnum.VALIDATION}
    for split, split_rows in by_split.items():
        indexes = sorted(row.fold_index for row in split_rows)
        # Contiguous from zero: the fold charts bucket repeated runs with
        # ``fold_index // n_splits``, so a gap silently reassigns a fold to the
        # wrong repetition instead of raising.
        assert indexes == [0, 1, 2], split
        assert all(row.name == "MeanPredictionMetric" for row in split_rows)
        assert all(row.std_value is None for row in split_rows)


def test_the_last_metric_is_the_mean_and_deviation_of_the_fold_metrics(
    client: TestClient, cv_run: dict
):
    """The aggregation, checked against the fold rows it aggregated."""
    for split in (SplitEnum.TRAIN, SplitEnum.VALIDATION):
        folds = _fold_values(client, cv_run["run_id"], LevelEnum.FOLD, split)
        # Otherwise the deviation below is zero whether it was computed or not.
        assert len(set(folds)) > 1, split

        aggregated = _metrics(
            client, cv_run["run_id"], level=LevelEnum.LAST, split=split
        )
        assert len(aggregated) == 1, split
        assert aggregated[0].value == pytest.approx(float(np.mean(folds)))
        assert aggregated[0].std_value == pytest.approx(float(np.std(folds)))


def test_the_reserved_rows_are_scored_once_and_carry_no_deviation(
    client: TestClient, cv_run: dict
):
    """A single measurement, so there is nothing to take a deviation over."""
    rows = _metrics(
        client, cv_run["run_id"], level=LevelEnum.LAST, split=SplitEnum.TEST
    )

    assert len(rows) == 1
    assert rows[0].std_value is None
    assert rows[0].fold_index is None


def test_the_aggregated_rows_are_written_at_step_zero(client: TestClient, cv_run: dict):
    """Pins an inconsistency rather than endorsing it.

    Fold rows get an auto-incremented step, and so does the reserved-rows
    measurement, because both go through ``calculate_metrics``. The aggregated
    rows are written directly with ``step=0``. Anything that orders metrics by
    step sees the summary before the folds it summarises.
    """
    aggregated = _metrics(
        client, cv_run["run_id"], level=LevelEnum.LAST, split=SplitEnum.VALIDATION
    )
    folds = _metrics(
        client, cv_run["run_id"], level=LevelEnum.FOLD, split=SplitEnum.VALIDATION
    )

    assert [row.step for row in aggregated] == [0]
    assert sorted(row.step for row in folds) == [1, 2, 3]


def test_the_inner_fold_index_is_never_written(client: TestClient, cv_run: dict):
    """``Metric.inner_fold_index`` was added with cross-validation and is unused.

    Pinned so that a reconciliation either starts populating it deliberately or
    drops it deliberately, rather than either happening by accident.
    """
    rows = _metrics(client, cv_run["run_id"])

    assert rows
    assert all(row.inner_fold_index is None for row in rows)


# --------------------------------------------------------------------------- #
# A session that reserves nothing
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module", name="unreserved_run")
def run_without_reserved_rows(client: TestClient, dataset_1: Dataset) -> dict:
    session_id = _make_session(
        client,
        dataset_1.id,
        "CvSessionNoTest",
        _kfold_splits(n_splits=3, test_size=0),
    )
    run_id = _make_run(client, session_id, name="UnreservedCvRun")
    fits = _run_job(run_id)
    return {"run_id": run_id, "fits": fits}


def test_a_session_that_reserves_nothing_still_finishes(
    client: TestClient, unreserved_run: dict
):
    run = _reload(client, unreserved_run["run_id"])
    split_indexes = json.loads(run.split_indexes)

    assert run.status == RunStatus.FINISHED
    assert split_indexes["full_dataset"]["test_indexes"] == []
    assert len(split_indexes["full_dataset"]["train_indexes"]) == DATASET_ROWS


def test_a_session_that_reserves_nothing_writes_no_test_metric(
    client: TestClient, unreserved_run: dict
):
    """With nothing held out there is no honest test score, so none is written."""
    rows = _metrics(client, unreserved_run["run_id"], split=SplitEnum.TEST)

    assert rows == []


def test_a_session_that_reserves_nothing_refits_on_every_row(unreserved_run: dict):
    fits = unreserved_run["fits"]

    assert [fit["train"] for fit in fits] == [100, 100, 100, DATASET_ROWS]


# --------------------------------------------------------------------------- #
# Cross-validation inside a hyperparameter search
# --------------------------------------------------------------------------- #

HPO_FOLDS = 2
HPO_TRIALS = 3


@pytest.fixture(scope="module", name="hpo_run")
def run_a_search_over_folds(client: TestClient, dataset_1: Dataset) -> dict:
    session_id = _make_session(
        client,
        dataset_1.id,
        "CvSessionHpo",
        _kfold_splits(n_splits=HPO_FOLDS, test_size=0.2),
    )
    run_id = _make_run(
        client,
        session_id,
        model_name="TunableCvModel",
        parameters={
            "n_estimators": {
                "optimize": True,
                "lower_bound": 1,
                "upper_bound": 5,
                "fixed_value": 2,
            }
        },
        optimizer_name="OptunaOptimizer",
        optimizer_parameters={
            "n_trials": HPO_TRIALS,
            "sampler": "TPESampler",
            "pruner": "None",
        },
        goal_metric="MeanPredictionMetric",
        name="HpoCvRun",
    )
    fits = _run_job(run_id)
    return {"run_id": run_id, "fits": fits}


def test_a_search_over_folds_reaches_finished(client: TestClient, hpo_run: dict):
    assert _reload(client, hpo_run["run_id"]).status == RunStatus.FINISHED


def test_every_trial_fits_every_fold(hpo_run: dict):
    """Cross-validation runs *inside* each trial, which is what it costs.

    The optimizer's objective is the whole fold loop, so one trial is k fits.
    On top of the search come the scoring loop's k fits and the final refit.
    """
    fits = hpo_run["fits"]
    pooled = [fit for fit in fits if fit["train"] == 60]
    refits = [fit for fit in fits if fit["train"] == 120]

    assert len(pooled) == HPO_TRIALS * HPO_FOLDS + HPO_FOLDS
    assert len(refits) == 1
    assert len(fits) == len(pooled) + len(refits)


def test_a_trial_metric_is_written_once_per_trial_for_each_scored_split(
    client: TestClient, hpo_run: dict
):
    """One row per trial, holding the mean over that trial's folds."""
    rows = _metrics(client, hpo_run["run_id"], level=LevelEnum.TRIAL)

    by_split = {}
    for row in rows:
        by_split.setdefault(row.split, []).append(row)

    assert set(by_split) == {SplitEnum.TRAIN, SplitEnum.VALIDATION}
    for split, split_rows in by_split.items():
        assert len(split_rows) == HPO_TRIALS, split
        assert all(row.fold_index is None for row in split_rows), split


def test_a_search_over_folds_persists_the_best_parameters(
    client: TestClient, hpo_run: dict
):
    run = _reload(client, hpo_run["run_id"])
    best = run.parameters["n_estimators"]["fixed_value"]

    assert 1 <= best <= 5


def test_a_search_over_folds_saves_two_plots_named_after_the_run(
    client: TestClient, hpo_run: dict
):
    run = _reload(client, hpo_run["run_id"])

    assert run.plot_history_path is not None
    assert run.plot_slice_path is not None
    assert os.path.exists(run.plot_history_path)
    assert os.path.exists(run.plot_slice_path)
    assert os.path.basename(run.plot_history_path) == (
        f"history_objective_plot_{run.id}.pickle"
    )
    # The contour and importance plots need more than one searched parameter.
    assert run.plot_contour_path is None
    assert run.plot_importance_path is None


def test_a_search_over_folds_still_aggregates_its_folds(
    client: TestClient, hpo_run: dict
):
    """The scoring loop runs after the search, so the summary is still written."""
    for split in (SplitEnum.TRAIN, SplitEnum.VALIDATION):
        folds = _fold_values(client, hpo_run["run_id"], LevelEnum.FOLD, split)
        aggregated = _metrics(
            client, hpo_run["run_id"], level=LevelEnum.LAST, split=split
        )

        assert len(folds) == HPO_FOLDS, split
        assert len(aggregated) == 1, split
        assert aggregated[0].value == pytest.approx(float(np.mean(folds)))
        assert aggregated[0].std_value == pytest.approx(float(np.std(folds)))


# --------------------------------------------------------------------------- #
# Nested cross-validation
# --------------------------------------------------------------------------- #

OUTER_FOLDS = 2
INNER_FOLDS = 2
NESTED_TRIALS = 2


@pytest.fixture(scope="module", name="nested_run")
def run_a_nested_search(client: TestClient, dataset_1: Dataset) -> dict:
    session_id = _make_session(
        client,
        dataset_1.id,
        "CvSessionNested",
        _kfold_splits(n_splits=OUTER_FOLDS, test_size=0.2),
    )
    run_id = _make_run(
        client,
        session_id,
        model_name="TunableCvModel",
        parameters={
            "n_estimators": {
                "optimize": True,
                "lower_bound": 1,
                "upper_bound": 5,
                "fixed_value": 2,
            }
        },
        optimizer_name="OptunaOptimizer",
        optimizer_parameters={
            "n_trials": NESTED_TRIALS,
            "sampler": "TPESampler",
            "pruner": "None",
        },
        goal_metric="MeanPredictionMetric",
        nested={
            "splitter_name": "KFoldSplitter",
            "n_splits": INNER_FOLDS,
            "shuffle": True,
            "random_state": 42,
        },
        name="NestedCvRun",
    )
    fits = _run_job(run_id)
    return {"run_id": run_id, "fits": fits}


def test_a_nested_run_reaches_finished(client: TestClient, nested_run: dict):
    assert _reload(client, nested_run["run_id"]).status == RunStatus.FINISHED


def test_a_nested_run_scores_every_outer_fold(client: TestClient, nested_run: dict):
    rows = _metrics(client, nested_run["run_id"], level=LevelEnum.OUTER_FOLD)

    by_split = {}
    for row in rows:
        by_split.setdefault(row.split, []).append(row)

    assert set(by_split) == {SplitEnum.TRAIN, SplitEnum.VALIDATION}
    for split, split_rows in by_split.items():
        assert sorted(row.fold_index for row in split_rows) == [0, 1], split


def test_a_nested_run_aggregates_its_outer_folds_apart_from_the_inner_ones(
    client: TestClient, nested_run: dict
):
    """``LAST_OUTER`` is the unbiased estimate; ``LAST`` summarises the plain folds."""
    for split in (SplitEnum.TRAIN, SplitEnum.VALIDATION):
        outer = _fold_values(client, nested_run["run_id"], LevelEnum.OUTER_FOLD, split)
        aggregated = _metrics(
            client, nested_run["run_id"], level=LevelEnum.LAST_OUTER, split=split
        )

        assert len(aggregated) == 1, split
        assert aggregated[0].value == pytest.approx(float(np.mean(outer)))
        assert aggregated[0].std_value == pytest.approx(float(np.std(outer)))

    # The ordinary aggregation still happens, at its own level: train and
    # validation from the fold loop, plus the reserved rows.
    assert len(_metrics(client, nested_run["run_id"], level=LevelEnum.LAST)) == 3


def test_a_nested_run_searches_inside_every_outer_fold(nested_run: dict):
    """Three nested loops, counted by the size of the partition each fit saw.

    Outer folds hold 60 pooled rows; splitting one into inner folds leaves 30
    rows to fit on. Those 30 row fits only exist because the search is run
    again, from scratch, inside each outer fold.
    """
    fits = nested_run["fits"]
    inner = [fit for fit in fits if fit["train"] == 30]
    outer = [fit for fit in fits if fit["train"] == 60]
    refits = [fit for fit in fits if fit["train"] == 120]

    assert len(inner) == OUTER_FOLDS * NESTED_TRIALS * INNER_FOLDS
    # One fit per outer fold with the parameters its inner search chose, then
    # the ordinary search and the scoring loop over the outer folds again.
    assert len(outer) == OUTER_FOLDS + NESTED_TRIALS * OUTER_FOLDS + OUTER_FOLDS
    assert len(refits) == 1
    assert len(fits) == len(inner) + len(outer) + len(refits)


# --------------------------------------------------------------------------- #
# Error branches, by the text the user is shown
# --------------------------------------------------------------------------- #


def _failing_run(client: TestClient, dataset_1: Dataset, name: str, **kwargs) -> int:
    session_id = _make_session(
        client,
        dataset_1.id,
        name,
        kwargs.pop("splits"),
        strategy=kwargs.pop("strategy", "CrossValidationEvaluationStrategy"),
    )
    return _make_run(client, session_id, name=name + "Run", **kwargs)


def test_an_unknown_splitter_is_reported_with_the_run_it_belongs_to(
    client: TestClient, dataset_1: Dataset
):
    run_id = _failing_run(
        client,
        dataset_1,
        "UnknownSplitter",
        splits=_kfold_splits(splitter_name="ThereIsNoSuchSplitter"),
    )

    with pytest.raises(JobError) as error:
        ModelJob(run_id=run_id).run()

    assert _squash(str(error.value)) == _squash(
        f"Error preparing dataset and components for run {run_id}: "
        "Unable to find Splitter with name ThereIsNoSuchSplitter in registry."
    )
    assert _reload(client, run_id).status == RunStatus.ERROR


def test_an_unknown_evaluation_strategy_is_reported(
    client: TestClient, dataset_1: Dataset
):
    run_id = _failing_run(
        client,
        dataset_1,
        "UnknownStrategy",
        splits=_kfold_splits(),
        strategy="ThereIsNoSuchStrategy",
    )

    with pytest.raises(JobError) as error:
        ModelJob(run_id=run_id).run()

    assert _squash(str(error.value)) == _squash(
        f"Error preparing dataset and components for run {run_id}: "
        "Unable to find Evaluation Strategy with name "
        "ThereIsNoSuchStrategy in registry."
    )
    assert _reload(client, run_id).status == RunStatus.ERROR


def test_more_folds_than_rows_is_reported_as_a_splitting_failure(
    client: TestClient, dataset_1: Dataset
):
    run_id = _failing_run(
        client,
        dataset_1,
        "TooManyFolds",
        splits=_kfold_splits(n_splits=DATASET_ROWS + 1, test_size=0),
    )

    with pytest.raises(JobError) as error:
        ModelJob(run_id=run_id).run()

    assert _squash(str(error.value)) == _squash(
        f"Error splitting the dataset for run {run_id}: "
        f"Number of splits (n_splits={DATASET_ROWS + 1}) cannot be greater "
        f"than the number of samples ({DATASET_ROWS})."
    )
    assert _reload(client, run_id).status == RunStatus.ERROR


def test_reserving_almost_everything_is_reported_as_a_splitting_failure(
    client: TestClient, dataset_1: Dataset
):
    run_id = _failing_run(
        client,
        dataset_1,
        "TooLargeTestSet",
        splits=_kfold_splits(n_splits=3, test_size=0.99),
    )

    with pytest.raises(JobError) as error:
        ModelJob(run_id=run_id).run()

    message = _squash(str(error.value))
    assert message.startswith(f"Error splitting the dataset for run {run_id}: ")
    assert "leaves too few rows" in message
    assert _reload(client, run_id).status == RunStatus.ERROR


def test_an_unknown_inner_splitter_is_reported_as_a_training_failure(
    client: TestClient, dataset_1: Dataset
):
    """Nested cross-validation resolves its inner splitter while already training.

    So a typo there is not caught with the rest of the configuration: the run
    has already reported that training started, and the message the user sees
    comes from a different branch.
    """
    run_id = _failing_run(
        client,
        dataset_1,
        "UnknownInnerSplitter",
        splits=_kfold_splits(n_splits=2),
        model_name="TunableCvModel",
        parameters={
            "n_estimators": {
                "optimize": True,
                "lower_bound": 1,
                "upper_bound": 5,
                "fixed_value": 2,
            }
        },
        optimizer_name="OptunaOptimizer",
        optimizer_parameters={
            "n_trials": 1,
            "sampler": "TPESampler",
            "pruner": "None",
        },
        goal_metric="MeanPredictionMetric",
        nested={"splitter_name": "ThereIsNoSuchSplitter", "n_splits": 2},
    )

    with pytest.raises(JobError) as error:
        ModelJob(run_id=run_id).run()

    message = _squash(str(error.value))
    assert message.startswith("Model training and evaluation failed ")
    assert "Error configuring inner splitter for nested CV" in message
    assert _reload(client, run_id).status == RunStatus.ERROR
