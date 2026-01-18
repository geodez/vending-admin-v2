"""create sync_runs table

Revision ID: 0005_create_sync_runs_table
Revises: 0004_create_kpi_views
Create Date: 2026-01-15 21:15:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0005_create_sync_runs_table'
down_revision = '0004_create_kpi_views'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sync_runs table to track synchronization history
    op.create_table(
        'sync_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_start', sa.Date(), nullable=True),
        sa.Column('period_end', sa.Date(), nullable=True),
        sa.Column('fetched', sa.Integer(), default=0),
        sa.Column('inserted', sa.Integer(), default=0),
        sa.Column('skipped_duplicates', sa.Integer(), default=0),
        sa.Column('expected_total', sa.Integer(), nullable=True),
        sa.Column('pages_fetched', sa.Integer(), nullable=True),
        sa.Column('items_per_page', sa.Integer(), nullable=True),
        sa.Column('last_page', sa.Integer(), nullable=True),
        sa.Column('ok', sa.Boolean(), default=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on started_at for faster queries
    op.create_index('idx_sync_runs_started_at', 'sync_runs', ['started_at'])


def downgrade() -> None:
    op.drop_index('idx_sync_runs_started_at', table_name='sync_runs')
    op.drop_table('sync_runs')
