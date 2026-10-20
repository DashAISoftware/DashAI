"""merge rag vectorizer converters and rag data documents heads

Revision ID: 3ef0449e8309
Revises: 4981a6250c8f, d8f3a1c6e2b9
Create Date: 2026-10-20 12:40:00.000000

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "3ef0449e8309"
down_revision: Union[str, None] = ("4981a6250c8f", "d8f3a1c6e2b9")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
