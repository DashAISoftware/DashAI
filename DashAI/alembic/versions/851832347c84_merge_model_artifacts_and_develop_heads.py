"""merge model artifacts and develop heads

Revision ID: 851832347c84
Revises: a5f2c71e9d40, d5b1c8a30f24
Create Date: 2026-09-08 15:52:53.659105

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '851832347c84'
down_revision: Union[str, None] = ('a5f2c71e9d40', 'd5b1c8a30f24')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
