"""add parameters_hash to rag_prompt and rag_generation_model

Revision ID: a7b3c9d1e5f2
Revises: e9f8a7b6c5d4
Create Date: 2026-08-10 00:00:00

"""
from typing import Sequence, Union
import json
import hashlib

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = 'a7b3c9d1e5f2'
down_revision: Union[str, None] = 'e9f8a7b6c5d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── rag_prompt ──
    with op.batch_alter_table('rag_prompt', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parameters_hash', sa.String(), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(text("SELECT id, parameters FROM rag_prompt")).fetchall()
    for row in rows:
        if row.parameters is not None:
            payload = json.dumps(row.parameters, sort_keys=True)
            h = hashlib.sha256(payload.encode()).hexdigest()
            conn.execute(
                text("UPDATE rag_prompt SET parameters_hash = :h WHERE id = :id"),
                {"h": h, "id": row.id},
            )

    with op.batch_alter_table('rag_prompt', schema=None) as batch_op:
        batch_op.alter_column('parameters_hash', nullable=False)
        batch_op.create_unique_constraint('uq_rag_prompt_params_hash', ['parameters_hash'])

    # ── rag_generation_model ──
    with op.batch_alter_table('rag_generation_model', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parameters_hash', sa.String(), nullable=True))

    rows = conn.execute(text("SELECT id, parameters FROM rag_generation_model")).fetchall()
    for row in rows:
        if row.parameters is not None:
            payload = json.dumps(row.parameters, sort_keys=True)
            h = hashlib.sha256(payload.encode()).hexdigest()
            conn.execute(
                text("UPDATE rag_generation_model SET parameters_hash = :h WHERE id = :id"),
                {"h": h, "id": row.id},
            )

    with op.batch_alter_table('rag_generation_model', schema=None) as batch_op:
        batch_op.alter_column('parameters_hash', nullable=False)
        batch_op.create_unique_constraint('uq_rag_gen_model_params_hash', ['parameters_hash'])


def downgrade() -> None:
    with op.batch_alter_table('rag_generation_model', schema=None) as batch_op:
        batch_op.drop_constraint('uq_rag_gen_model_params_hash', type_='unique')
        batch_op.drop_column('parameters_hash')

    with op.batch_alter_table('rag_prompt', schema=None) as batch_op:
        batch_op.drop_constraint('uq_rag_prompt_params_hash', type_='unique')
        batch_op.drop_column('parameters_hash')
