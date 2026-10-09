"""drop class_name+parameters unique constraints from RAG tables

These constraints are replaced by parameters_hash UNIQUE (added in a7b3c9d1e5f2).
The old (class_name, parameters) constraint is unreliable on SQLite JSON columns
because JSON serialisation order is not guaranteed. The hash-based constraint
provides deterministic deduplication.

Revision ID: c8d4e0f2a6b3
Revises: a7b3c9d1e5f2
Create Date: 2026-08-10 00:00:00

"""

from typing import Sequence, Union

from alembic import op

revision: str = "c8d4e0f2a6b3"
down_revision: Union[str, None] = "a7b3c9d1e5f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("rag_generation_model", schema=None) as batch_op:
        batch_op.drop_constraint("uix_rag_gen_model_class_params", type_="unique")

    with op.batch_alter_table("rag_prompt", schema=None) as batch_op:
        batch_op.drop_constraint("uix_rag_prompt_class_params", type_="unique")


def downgrade() -> None:
    with op.batch_alter_table("rag_prompt", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uix_rag_prompt_class_params",
            ["class_name", "parameters"],
        )

    with op.batch_alter_table("rag_generation_model", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uix_rag_gen_model_class_params",
            ["class_name", "parameters"],
        )
