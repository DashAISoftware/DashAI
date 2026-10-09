"""merge project/users and develop heads

Revision ID: 341ba60c36de
Revises: 2f0172d883dc, 508c9f7db00a
Create Date: 2026-10-09 01:49:53.497550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '341ba60c36de'
down_revision: Union[str, None] = ('2f0172d883dc', '508c9f7db00a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
