"""merge the RAG retrieval-model and process-progress heads

``feat/adaptive-retrievers`` added ``rag_retrieval_model`` while
``feat/rag-query-transformation`` added ``generative_process.progress``. Both
branch from ``c5d1a9e74f28`` and touch unrelated tables, so this empty merge
point gives Alembic a single head again.

Revision ID: p9q0r1s2t3u4
Revises: e7f8a9b0c1d2, n7o8p9q1r2s3
Create Date: 2026-10-19
"""

from typing import Sequence, Union

revision: str = "p9q0r1s2t3u4"
down_revision: Union[str, Sequence[str], None] = ("e7f8a9b0c1d2", "n7o8p9q1r2s3")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
