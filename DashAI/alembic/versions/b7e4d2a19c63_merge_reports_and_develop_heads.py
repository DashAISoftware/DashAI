"""merge reports and develop heads

Revision ID: b7e4d2a19c63
Revises: a5f2c71e9d40, e6c3b91a7d48
Create Date: 2026-09-07 12:00:00.000000

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "b7e4d2a19c63"
down_revision: Union[str, Sequence[str], None] = ("a5f2c71e9d40", "e6c3b91a7d48")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
