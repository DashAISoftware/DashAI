"""merge rag data documents and develop heads

Revision ID: 4981a6250c8f
Revises: 1ec528017fa9, c5d1a9e74f28
Create Date: 2026-10-20 12:12:32.212685

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "4981a6250c8f"
down_revision: Union[str, None] = ("1ec528017fa9", "c5d1a9e74f28")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
