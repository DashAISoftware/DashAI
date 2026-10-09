"""merge explorer artifacts and processed document content heads

Revision ID: 6de3122e9948
Revises: d5b3c8f2a041, j3k4l5m6n7o8
Create Date: 2026-08-14 16:56:31.505347

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "6de3122e9948"
down_revision: Union[str, Sequence[str], None] = ("d5b3c8f2a041", "j3k4l5m6n7o8")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
