"""add document source to notebook

Revision ID: a4c9d2e7f1b3
Revises: a7c3e91b5d20
Create Date: 2026-10-07 12:00:00.000000

A notebook works on a copy of either a dataset or a document. dataset_id
becomes nullable, document_id references data_document, and a CHECK keeps
exactly one of them set. Downgrading deletes document notebooks together
with their explorers and converters, because the old schema cannot hold
them; their working directories stay on disk since migrations do no file
I/O.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a4c9d2e7f1b3"
down_revision: Union[str, None] = "a7c3e91b5d20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CHECK_NAME = "ck_notebook_exactly_one_source"
FK_NAME = "fk_notebook_document_id_data_document"
SOURCE_CHECK = (
    "(dataset_id IS NOT NULL AND document_id IS NULL) "
    "OR (dataset_id IS NULL AND document_id IS NOT NULL)"
)
DOCUMENT_NOTEBOOKS = "SELECT id FROM notebook WHERE document_id IS NOT NULL"


def upgrade() -> None:
    """Add notebook.document_id and require exactly one notebook source."""
    with op.batch_alter_table("notebook", schema=None) as batch_op:
        batch_op.alter_column("dataset_id", existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column("document_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            op.f(FK_NAME),
            "data_document",
            ["document_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_check_constraint(op.f(CHECK_NAME), SOURCE_CHECK)


def downgrade() -> None:
    """Delete document notebooks and restore the dataset only notebook table."""
    op.execute(f"DELETE FROM explorer WHERE notebook_id IN ({DOCUMENT_NOTEBOOKS})")
    op.execute(f"DELETE FROM converter WHERE notebook_id IN ({DOCUMENT_NOTEBOOKS})")
    op.execute("DELETE FROM notebook WHERE document_id IS NOT NULL")
    with op.batch_alter_table("notebook", schema=None) as batch_op:
        batch_op.drop_constraint(op.f(CHECK_NAME), type_="check")
        batch_op.drop_constraint(op.f(FK_NAME), type_="foreignkey")
        batch_op.drop_column("document_id")
        batch_op.alter_column("dataset_id", existing_type=sa.Integer(), nullable=False)
