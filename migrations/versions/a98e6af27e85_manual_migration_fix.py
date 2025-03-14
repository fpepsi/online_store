"""Manual migration fix

Revision ID: a98e6af27e85
Revises: c89d83b59291
Create Date: 2025-03-07 10:42:17.515848

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a98e6af27e85'
down_revision = 'c89d83b59291'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_voided', sa.Boolean(), nullable=False, server_default=sa.text("0")))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_column('is_voided')

    # ### end Alembic commands ###
