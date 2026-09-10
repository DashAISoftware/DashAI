"""Add credential table

Revision ID: d4e8a2c6f0b1
Revises: f1a2b3c4d5e6
Create Date: 2026-06-15 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e8a2c6f0b1"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "credential",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("encrypted_key", sa.Text(), nullable=False),
        sa.Column(
            "verified",
            sa.Boolean(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("last_modified", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_credential"),
        sa.UniqueConstraint("name", name="uq_credential_name"),
    )


def downgrade() -> None:
    op.drop_table("credential")
