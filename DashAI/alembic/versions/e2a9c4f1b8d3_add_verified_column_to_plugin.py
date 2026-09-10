"""Add verified column to plugin

Revision ID: e2a9c4f1b8d3
Revises: 3db684f4090a
Create Date: 2026-06-08 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2a9c4f1b8d3"
down_revision: Union[str, None] = "3db684f4090a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "plugin",
        sa.Column(
            "verified",
            sa.Boolean(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("plugin", "verified")
