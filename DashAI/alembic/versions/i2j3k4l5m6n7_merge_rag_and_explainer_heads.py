"""Merge RAG and explainer heads

Revision ID: i2j3k4l5m6n7
Revises: h1i2j3k4l5m6, c4e8a1d20f3b
Create Date: 2026-08-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i2j3k4l5m6n7'
down_revision: Union[str, None] = ('h1i2j3k4l5m6', 'c4e8a1d20f3b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
