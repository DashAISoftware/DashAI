"""Add folder system for datasets

Revision ID: f1a2b3c4d5e6
Revises: e2a9c4f1b8d3
Create Date: 2026-06-09 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e2a9c4f1b8d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "folder",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("last_modified", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_folder")),
        sa.UniqueConstraint("name", name=op.f("uq_folder_name")),
    )

    with op.batch_alter_table("dataset", schema=None) as batch_op:
        batch_op.add_column(sa.Column("folder_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_dataset_folder_id_folder",
            "folder",
            ["folder_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("dataset", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_dataset_folder_id_folder", type_="foreignkey"
        )
        batch_op.drop_column("folder_id")

    op.drop_table("folder")
