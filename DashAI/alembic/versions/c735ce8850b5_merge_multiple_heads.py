"""merge multiple heads

Revision ID: c735ce8850b5
Revises: 885bc158af44, a1b2c3d4
Create Date: 2026-05-05 16:35:34.489723

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c735ce8850b5'
down_revision: Union[str, None] = ('885bc158af44', 'a1b2c3d4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
