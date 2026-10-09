"""merge explainer and parameter history heads

Revision ID: e0f00f71ba44
Revises: a7d2c9e4f1b0, d1c2b3a4f5e6
Create Date: 2026-07-22 11:13:21.127590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0f00f71ba44'
down_revision: Union[str, None] = ('a7d2c9e4f1b0', 'd1c2b3a4f5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
