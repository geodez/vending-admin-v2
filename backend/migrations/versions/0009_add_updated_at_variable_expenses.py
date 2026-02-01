"""Add updated_at to variable_expenses

Revision ID: 0009
Revises: 0008
Create Date: 2026-02-01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'variable_expenses',
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False)
    )


def downgrade():
    op.drop_column('variable_expenses', 'updated_at')
