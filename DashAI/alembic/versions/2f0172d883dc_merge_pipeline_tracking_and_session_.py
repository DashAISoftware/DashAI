"""merge pipeline tracking and session preprocessing heads

Revision ID: 2f0172d883dc
Revises: 2e1b3462553d, f4a91c62d8e7
Create Date: 2026-09-28 13:05:21.850781

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "2f0172d883dc"
down_revision: Union[str, None] = ("2e1b3462553d", "f4a91c62d8e7")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
