"""Add sale_price_rub to button_matrix_items

Revision ID: 0007
Revises: 0006
Create Date: 2026-01-19

Adds sale_price_rub column to button_matrix_items table for storing sale price per drink.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    # Add sale_price_rub column to button_matrix_items
    op.add_column('button_matrix_items', 
        sa.Column('sale_price_rub', sa.Numeric(10, 2), nullable=True)
    )


def downgrade():
    op.drop_column('button_matrix_items', 'sale_price_rub')
