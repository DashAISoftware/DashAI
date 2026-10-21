"""merge document notebooks and develop heads

Revision ID: 1ec528017fa9
Revises: 49d7035ce11f, a4c9d2e7f1b3
Create Date: 2026-10-19 17:36:29.733372

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "1ec528017fa9"
down_revision: Union[str, None] = ("49d7035ce11f", "a4c9d2e7f1b3")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
