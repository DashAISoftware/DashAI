"""merge migration heads from develop

Revision ID: cf029e1c7ea6
Revises: 237170dfd527, d5b3c8f2a041
Create Date: 2026-08-12 14:43:42.158617

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf029e1c7ea6'
down_revision: Union[str, None] = ('237170dfd527', 'd5b3c8f2a041')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
