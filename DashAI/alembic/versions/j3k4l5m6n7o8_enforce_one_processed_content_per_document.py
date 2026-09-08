"""enforce one processed_document_content row per document (1:1)

Revision ID: j3k4l5m6n7o8
Revises: i2j3k4l5m6n7
Create Date: 2026-08-14 12:00:00.000000

Changes ``processed_document_content`` so that a document has exactly one
extracted content row:
  * Drops the UNIQUE(document_id, signature) constraint.
  * Adds a UNIQUE(document_id) constraint.
  * Keeps ``signature`` as a nullable tracking field.

Existing duplicate rows are collapsed (one row per document_id, keeping the
most recently inserted one) before the new constraint is applied.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "j3k4l5m6n7o8"
down_revision: Union[str, None] = "i2j3k4l5m6n7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_UNIQUE = "uix_processed_document_content_signature"
_NEW_UNIQUE = "uq_processed_document_content_document"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "processed_document_content" not in inspector.get_table_names():
        return

    # Collapse duplicates: keep the single most recent row per document_id.
    bind.execute(
        sa.text(
            "DELETE FROM processed_document_content WHERE id NOT IN ("
            "  SELECT MAX(id) FROM processed_document_content GROUP BY document_id"
            ")"
        )
    )

    with op.batch_alter_table("processed_document_content", schema=None) as batch_op:
        batch_op.drop_constraint(_OLD_UNIQUE, type_="unique")
        batch_op.alter_column("signature", nullable=True)
        batch_op.create_unique_constraint(_NEW_UNIQUE, ["document_id"])


def downgrade() -> None:
    with op.batch_alter_table("processed_document_content", schema=None) as batch_op:
        batch_op.drop_constraint(_NEW_UNIQUE, type_="unique")
        batch_op.alter_column("signature", nullable=False)
        batch_op.create_unique_constraint(_OLD_UNIQUE, ["document_id", "signature"])
