"""Merge RAG and production heads

Revision ID: 8d5416cac8f1
Revises: d4e5f6a7b8c9, f1a2b3c4d5e6
Create Date: 2026-07-06 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d5416cac8f1'
down_revision: Union[str, None] = ('d4e5f6a7b8c9', 'f1a2b3c4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
