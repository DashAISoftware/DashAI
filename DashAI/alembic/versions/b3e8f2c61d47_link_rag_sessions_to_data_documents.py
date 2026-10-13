"""link RAG sessions to Data module documents

Creates ``rag_session_document``, the link between RAG sessions and the
``data_document`` rows they use, gives ``rag_chunk_set`` an owning
``session_id`` and ``generative_session`` a ``needs_reindex`` flag, and points
the ``document_id`` foreign keys of ``chunk``, ``rag_chunk_set_document`` and
``rag_embedding_matrix`` at ``data_document``.

Existing chunk sets keep ``session_id`` NULL: they were built over the legacy
``document`` table and the startup backfill deletes them together with their
files. This migration performs no filesystem I/O.

Revision ID: b3e8f2c61d47
Revises: a4c9d2e7f1b3
Create Date: 2026-10-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3e8f2c61d47"
down_revision: Union[str, None] = "a4c9d2e7f1b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DATA_DOCUMENT_FKS = {
    "chunk": "fk_chunk_document_id_data_document",
    "rag_chunk_set_document": "fk_rag_chunk_set_document_document_id_data_document",
    "rag_embedding_matrix": "fk_rag_embedding_matrix_document_id_data_document",
}
_LEGACY_DOCUMENT_FKS = {
    "chunk": "fk_chunk_document_id_document",
    "rag_chunk_set_document": "fk_chunk_set_doc_document",
    "rag_embedding_matrix": "fk_rag_embedding_matrix_document_id_document",
}


def _document_fk_name(table: str, referred_table: str) -> str:
    """Return the name of the foreign key from ``table.document_id``.

    Parameters
    ----------
    table : str
        Table holding the ``document_id`` column.
    referred_table : str
        Table the key currently references.

    Returns
    -------
    str
        The constraint name, needed by batch mode to drop it.

    Raises
    ------
    RuntimeError
        If no named key from ``table.document_id`` to ``referred_table`` exists.
    """
    for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys(table):
        if (
            foreign_key["constrained_columns"] == ["document_id"]
            and foreign_key["referred_table"] == referred_table
            and foreign_key["name"]
        ):
            return foreign_key["name"]
    raise RuntimeError(
        f"No named foreign key from {table}.document_id to {referred_table}."
    )


def _retarget(table: str, old_table: str, new_table: str, new_name: str) -> None:
    """Point ``table.document_id`` at ``new_table.id``.

    Parameters
    ----------
    table : str
        Table holding the ``document_id`` column.
    old_table : str
        Table the key references now.
    new_table : str
        Table the key references afterwards.
    new_name : str
        Name of the new constraint.
    """
    old_name = _document_fk_name(table, old_table)
    with op.batch_alter_table(table) as batch_op:
        batch_op.drop_constraint(old_name, type_="foreignkey")
        batch_op.create_foreign_key(
            new_name, new_table, ["document_id"], ["id"], ondelete="CASCADE"
        )


def upgrade() -> None:
    op.create_table(
        "rag_session_document",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("data_document_id", sa.Integer(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["generative_session.id"],
            name="fk_rag_session_document_session_id_generative_session",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["data_document_id"],
            ["data_document.id"],
            name="fk_rag_session_document_data_document_id_data_document",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_rag_session_document"),
        sa.UniqueConstraint(
            "session_id", "data_document_id", name="uq_rag_session_document_pair"
        ),
    )
    with op.batch_alter_table("rag_chunk_set") as batch_op:
        batch_op.add_column(sa.Column("session_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_rag_chunk_set_session_id_generative_session",
            "generative_session",
            ["session_id"],
            ["id"],
            ondelete="CASCADE",
        )
    with op.batch_alter_table("generative_session") as batch_op:
        batch_op.add_column(
            sa.Column(
                "needs_reindex", sa.Boolean(), nullable=False, server_default="0"
            )
        )
    for table, new_name in _DATA_DOCUMENT_FKS.items():
        _retarget(table, "document", "data_document", new_name)


def downgrade() -> None:
    for table, legacy_name in _LEGACY_DOCUMENT_FKS.items():
        _retarget(table, "data_document", "document", legacy_name)
    with op.batch_alter_table("generative_session") as batch_op:
        batch_op.drop_column("needs_reindex")
    with op.batch_alter_table("rag_chunk_set") as batch_op:
        batch_op.drop_constraint(
            "fk_rag_chunk_set_session_id_generative_session", type_="foreignkey"
        )
        batch_op.drop_column("session_id")
    op.drop_table("rag_session_document")
