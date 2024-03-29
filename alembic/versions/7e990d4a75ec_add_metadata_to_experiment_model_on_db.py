"""Add metadata to Experiment model on DB

Revision ID: 7e990d4a75ec
Revises: 8307d4c14824
Create Date: 2023-09-22 22:45:34.448464

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "7e990d4a75ec"
down_revision = "8307d4c14824"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("experiment", sa.Column("input_columns", sa.JSON(), nullable=False))
    op.add_column("experiment", sa.Column("output_columns", sa.JSON(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("experiment", "output_columns")
    op.drop_column("experiment", "input_columns")
    # ### end Alembic commands ###
