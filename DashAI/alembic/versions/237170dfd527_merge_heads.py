"""merge heads

Revision ID: 237170dfd527
Revises: 875febec2ec5, c4e8a1d20f3b
Create Date: 2026-07-29 19:05:47.693363

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '237170dfd527'
down_revision: Union[str, None] = ('875febec2ec5', 'c4e8a1d20f3b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
