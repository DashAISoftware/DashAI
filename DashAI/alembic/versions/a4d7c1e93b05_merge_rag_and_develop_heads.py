"""merge RAG and develop heads

Revision ID: a4d7c1e93b05
Revises: 6de3122e9948, cf029e1c7ea6
Create Date: 2026-08-20 10:00:00.000000

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "a4d7c1e93b05"
down_revision: Union[str, Sequence[str], None] = ("6de3122e9948", "cf029e1c7ea6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
