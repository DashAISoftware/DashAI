"""merge heads

Revision ID: 896c39f514fe
Revises: 517e2f3084cc, a1f8e3b0c2d9
Create Date: 2026-05-26 21:01:59.063309

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '896c39f514fe'
down_revision: Union[str, None] = ('517e2f3084cc', 'a1f8e3b0c2d9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
