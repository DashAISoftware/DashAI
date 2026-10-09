"""track a RAG session's in-flight indexing job

Indexing used to happen inside the chat job, so there was nothing to track: the
chat process *was* the index run. Now that a session can be indexed eagerly by
a job of its own, the session needs to point at that job so the API can tell
"already indexing" from "not indexed yet", coalesce duplicate requests, and
cancel the run before invalidating what it is writing.

``index_job_id`` is a pointer, never the truth. The job queue's ``task_copy``
table stays authoritative for whether the job is alive; a stale pointer simply
resolves to nothing and is overwritten by the next indexing request.

Revision ID: l5m6n7o8p9q0
Revises: k4l5m6n7o8p9
Create Date: 2026-09-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "l5m6n7o8p9q0"
down_revision: Union[str, None] = "k4l5m6n7o8p9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("generative_session") as batch_op:
        batch_op.add_column(sa.Column("index_job_id", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("generative_session") as batch_op:
        batch_op.drop_column("index_job_id")
