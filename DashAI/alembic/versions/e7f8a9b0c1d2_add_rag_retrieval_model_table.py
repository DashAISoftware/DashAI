"""add rag_retrieval_model table

Revision ID: e7f8a9b0c1d2
Revises: c5d1a9e74f28
Create Date: 2026-10-15 00:00:00

Dedicated table for the LLM used by the LLM-evaluated composite retrievers to
judge retrieval sufficiency. Columns mirror ``rag_generation_model``.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, None] = "c5d1a9e74f28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rag_retrieval_model",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("class_name", sa.String(), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("parameters_hash", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_rag_retrieval_model"),
        sa.UniqueConstraint(
            "parameters_hash",
            name="uq_rag_retrieval_model_params_hash",
        ),
    )


def downgrade() -> None:
    op.drop_table("rag_retrieval_model")
