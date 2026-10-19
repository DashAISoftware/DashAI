"""Add pipeline run tracking tables.

Separates the definition of a graph from its executions. ``Pipeline`` keeps the
definition, which changes as the user edits it; ``pipeline_run`` freezes the
steps and edges of one execution, ``pipeline_node_run`` tracks each node of it,
and ``pipeline_node_artifact`` holds what a node emitted, keyed by a key from
the unit's PROVIDES rather than by a column per node type.

The three JSON result columns on ``pipeline`` (exploration, train, prediction)
are deliberately left in place: the pipelines endpoints and the front's results
view still read them, so removing them belongs with rewriting those.

Revision ID: e7b4d1a9c206
Revises: d5b3c8f2a041
Create Date: 2026-08-20 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "e7b4d1a9c206"
down_revision: Union[str, None] = "d5b3c8f2a041"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pipeline_run",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pipeline_id", sa.Integer(), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=True),
        sa.Column("edges", sa.JSON(), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("last_modified", sa.DateTime(), nullable=False),
        sa.Column("delivery_time", sa.DateTime(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "NOT_STARTED",
                "DELIVERED",
                "STARTED",
                "FINISHED",
                "ERROR",
                name="pipelinerunstatus",
            ),
            nullable=False,
        ),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["pipeline_id"],
            ["pipeline.id"],
            name=op.f("fk_pipeline_run_pipeline_id_pipeline"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pipeline_run")),
    )

    op.create_table(
        "pipeline_node_run",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pipeline_run_id", sa.Integer(), nullable=False),
        sa.Column("node_id", sa.String(), nullable=False),
        sa.Column("block_id", sa.String(), nullable=False),
        sa.Column("node_type", sa.String(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("input", sa.JSON(), nullable=True),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("last_modified", sa.DateTime(), nullable=False),
        sa.Column("delivery_time", sa.DateTime(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "NOT_STARTED",
                "DELIVERED",
                "STARTED",
                "FINISHED",
                "ERROR",
                "CANCELLED",
                name="noderunstatus",
            ),
            nullable=False,
        ),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["pipeline_run_id"],
            ["pipeline_run.id"],
            name=op.f("fk_pipeline_node_run_pipeline_run_id_pipeline_run"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pipeline_node_run")),
    )

    op.create_table(
        "pipeline_node_artifact",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("node_run_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["node_run_id"],
            ["pipeline_node_run.id"],
            name=op.f("fk_pipeline_node_artifact_node_run_id_pipeline_node_run"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pipeline_node_artifact")),
    )


def downgrade() -> None:
    op.drop_table("pipeline_node_artifact")
    op.drop_table("pipeline_node_run")
    op.drop_table("pipeline_run")
