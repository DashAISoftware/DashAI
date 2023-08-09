"""Initial migration

Revision ID: 80faf11605a2
Revises: 
Create Date: 2023-08-08 09:13:58.794747

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '80faf11605a2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('experiment', 'step')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('experiment', sa.Column('step', sa.VARCHAR(length=19), nullable=False))
    # ### end Alembic commands ###
