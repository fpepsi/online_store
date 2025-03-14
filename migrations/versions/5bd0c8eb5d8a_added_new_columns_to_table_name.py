"""Added new columns to <table_name>

Revision ID: 5bd0c8eb5d8a
Revises: a98e6af27e85
Create Date: 2025-03-10 13:27:23.748490

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5bd0c8eb5d8a'
down_revision = 'a98e6af27e85'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stripe_product_code', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('stripe_price_code', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('stripe_price_code')
        batch_op.drop_column('stripe_product_code')

    # ### end Alembic commands ###
