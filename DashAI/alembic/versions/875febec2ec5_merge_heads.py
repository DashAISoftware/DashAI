"""merge heads

Revision ID: 875febec2ec5
Revises: 3db684f4090a, d00fc87daabd
Create Date: 2026-06-08 20:59:51.593764

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '875febec2ec5'
down_revision: Union[str, None] = ('3db684f4090a', 'd00fc87daabd')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
