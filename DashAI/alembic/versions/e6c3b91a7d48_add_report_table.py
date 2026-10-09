"""add report table

Revision ID: e6c3b91a7d48
Revises: c4e8a1d20f3b
Create Date: 2026-07-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e6c3b91a7d48"
down_revision: Union[str, None] = "c4e8a1d20f3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the table holding evaluation reports of a run."""
    op.create_table(
        "report",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("huey_id", sa.String(), nullable=True),
        sa.Column("report_name", sa.String(), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("artifacts_path", sa.String(), nullable=True),
        sa.Column("plot_overrides", sa.JSON(), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "NOT_STARTED",
                "DELIVERED",
                "STARTED",
                "FINISHED",
                "ERROR",
                name="reportstatus",
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["run.id"],
            name=op.f("fk_report_run_id_run"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_report")),
    )


def downgrade() -> None:
    """Drop the report table."""
    op.drop_table("report")
