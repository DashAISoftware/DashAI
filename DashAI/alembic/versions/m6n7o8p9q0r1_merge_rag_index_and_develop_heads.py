"""merge the RAG indexing head with develop

``feat/rag-uiv2`` and ``develop`` both branch from ``b7c1d4e9f206``: the RAG
line scoped documents to a session and added the indexing job pointer, while
develop added the report table and the prediction split. Neither side touches
the other's tables, so this is an empty merge point whose only job is to give
Alembic a single head again.

Revision ID: m6n7o8p9q0r1
Revises: l5m6n7o8p9q0, b7e4d2a19c63
Create Date: 2026-09-09
"""

from typing import Sequence, Union

revision: str = "m6n7o8p9q0r1"
down_revision: Union[str, Sequence[str], None] = ("l5m6n7o8p9q0", "b7e4d2a19c63")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
