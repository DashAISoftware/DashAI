"""Merge the pipeline tracking and cross-validation heads.

Two lines of work reached the database at the same time and neither knew about
the other, so the revision graph ended with two heads and ``upgrade head``
refused to pick one:

``e7b4d1a9c206`` added the pipeline run tracking tables (``pipeline_run``,
``pipeline_node_run``, ``pipeline_node_artifact``); ``b7e4d2a19c63`` is the tip
of the branch that brought cross-validation and the evaluation reports, which
added ``model_session.evaluation_strategy``, ``run.nested``, the fold columns on
``metric`` and the ``report`` table.

There is nothing to do here. The two sides touch disjoint tables and disjoint
columns, so joining the graph is the whole of the change: this revision exists
to give the two heads a single successor.

Revision ID: 82fb7a6b8ac2
Revises: b7e4d2a19c63, e7b4d1a9c206
Create Date: 2026-09-10 13:03:45.322840

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "82fb7a6b8ac2"
down_revision: Union[str, None] = ("b7e4d2a19c63", "e7b4d1a9c206")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Join the two revision lines. Neither side needs anything applied."""


def downgrade() -> None:
    """Split them again, which is likewise nothing to undo."""
