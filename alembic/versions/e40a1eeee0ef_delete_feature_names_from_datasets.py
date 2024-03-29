"""Delete feature_names from datasets

Revision ID: e40a1eeee0ef
Revises: 4bce47006c88
Create Date: 2023-11-28 15:58:18.913263

"""
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

from alembic import op

# revision identifiers, used by Alembic.
revision = "e40a1eeee0ef"
down_revision = "4bce47006c88"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("dataset", "feature_names")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("dataset", sa.Column("feature_names", sqlite.JSON(), nullable=False))
    # ### end Alembic commands ###
