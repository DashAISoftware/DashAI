"""relabel the cross-validation metrics that were stored as test

Revision ID: b7c1d4e9f206
Revises: d033b573e63b
Create Date: 2026-08-24 19:40:00.000000

A fold is scored on rows held out of that fold only, so its result is a
validation estimate obtained by resampling, not a test score. Runs produced
before this distinction existed stored those scores under ``TEST``, and the
readers now ask for ``VALIDATION``, which would leave every existing
cross-validation run without fold charts or statistical tests.

Two things are relabelled:

  * The metrics themselves, at the levels cross-validation produces.
  * ``model_session.validation_metrics``, which stayed empty for
    cross-validation sessions because the wizard used to decide those runs had
    no validation partition. A new run in one of those sessions would compute
    no fold metric at all, and would crash outright under hyperparameter
    optimization.

Holdout sessions are left alone: their test metrics really are test metrics.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7c1d4e9f206"
down_revision: Union[str, None] = "d033b573e63b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CV_STRATEGY = "CrossValidationEvaluationStrategy"

# SQLAlchemy's Enum stores the member name, not its value.
_CV_RUNS = """
    SELECT run.id FROM run
    JOIN model_session ON model_session.id = run.model_session_id
    WHERE model_session.evaluation_strategy = :strategy
"""


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if not {"metric", "run", "model_session"} <= tables:
        return

    # Fold levels only ever come from cross-validation, so they need no scope.
    bind.execute(
        sa.text(
            "UPDATE metric SET split = 'VALIDATION' "
            "WHERE split = 'TEST' AND level IN ('FOLD', 'OUTER_FOLD')"
        )
    )

    # The aggregated and per-trial scores are the mean of those same folds.
    # Here the scope matters: a holdout run's test metric must stay a test
    # metric.
    bind.execute(
        sa.text(
            "UPDATE metric SET split = 'VALIDATION' "
            "WHERE split = 'TEST' AND level IN ('LAST', 'LAST_OUTER', 'TRIAL') "
            f"AND run_id IN ({_CV_RUNS})"
        ),
        {"strategy": _CV_STRATEGY},
    )

    # Give those sessions the metric list their runs are about to be scored
    # with. The three lists always held the same metric names, so copying the
    # test one restores what the wizard would write today.
    bind.execute(
        sa.text(
            "UPDATE model_session SET validation_metrics = test_metrics "
            "WHERE evaluation_strategy = :strategy "
            "AND test_metrics IS NOT NULL "
            "AND (validation_metrics IS NULL OR validation_metrics IN ('[]', 'null'))"
        ),
        {"strategy": _CV_STRATEGY},
    )


def downgrade() -> None:
    """No-op: the relabelling is not reversible.

    After the upgrade a cross-validation run's validation metrics are
    indistinguishable from the ones a later run wrote as validation on purpose,
    so moving them back to test would corrupt the newer runs.
    """
