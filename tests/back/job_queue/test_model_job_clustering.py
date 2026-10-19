"""Regression tests for how ``ModelJob`` writes the scores of a task without a target.

Clustering runs take a different route through the job than every other task:
no splitter, no optimiser, no evaluation strategy, and metrics scored over the
whole dataset by ``ScoreClustersUnit``, which only returns the numbers. Writing
them is the job's, and these cover that write: one LAST row per metric over the
full dataset, upserted so a re-train replaces values instead of adding rows.

What used to be tested here moved with the code it tested: the scaling to
``tests/back/units/test_prepare_without_target_unit.py``, the fit to
``tests/back/units/test_fit_without_target_unit.py``, and the degenerate
clusterings to ``tests/back/units/test_score_clusters_unit.py``.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.dependencies.database.models import Base, Metric
from DashAI.back.job.model_job import ModelJob

SCORES = {"Silhouette": 0.75, "CalinskiHarabasz": 120.0, "DaviesBouldin": 0.4}


@pytest.fixture(name="db")
def fixture_db():
    """A throwaway session. Only the metric writes are exercised here, so the
    run is a stand in for its id rather than a real row."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        yield session


def test_every_score_is_one_full_last_row(db):
    ModelJob._write_full_metrics(db, 1, SCORES)

    rows = db.query(Metric).all()

    assert {row.name: row.value for row in rows} == SCORES
    assert all(row.run_id == 1 for row in rows)
    assert all(row.split == SplitEnum.FULL for row in rows)
    assert all(row.level == LevelEnum.LAST for row in rows)
    assert all(row.step == 0 for row in rows)


def test_training_again_replaces_the_previous_values_rather_than_adding_rows(db):
    ModelJob._write_full_metrics(db, 1, SCORES)
    ModelJob._write_full_metrics(db, 1, dict.fromkeys(SCORES, -1.0))

    rows = db.query(Metric).all()

    assert len(rows) == len(SCORES)
    assert {row.name: row.value for row in rows} == dict.fromkeys(SCORES, -1.0)
    assert all(row.step == 0 for row in rows)


def test_two_runs_of_the_same_session_keep_their_own_rows(db):
    for run_id in (1, 2):
        ModelJob._write_full_metrics(db, run_id, SCORES)

    assert db.query(Metric).count() == 2 * len(SCORES)


def test_nothing_scored_writes_nothing(db):
    ModelJob._write_full_metrics(db, 1, {})

    assert db.query(Metric).count() == 0
