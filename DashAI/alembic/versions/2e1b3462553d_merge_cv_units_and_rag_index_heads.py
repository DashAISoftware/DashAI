"""merge cv units and rag index heads

Revision ID: 2e1b3462553d
Revises: 82fb7a6b8ac2, m6n7o8p9q0r1
Create Date: 2026-09-20 23:07:57.181448

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "2e1b3462553d"
down_revision: Union[str, Sequence[str], None] = ("82fb7a6b8ac2", "m6n7o8p9q0r1")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
