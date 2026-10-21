"""merge data document and develop heads

Revision ID: 49d7035ce11f
Revises: 2f0172d883dc, a7c3e91b5d20
Create Date: 2026-10-14 17:00:05.651532

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "49d7035ce11f"
down_revision: Union[str, None] = ("2f0172d883dc", "a7c3e91b5d20")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
