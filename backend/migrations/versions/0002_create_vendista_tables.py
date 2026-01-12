"""create vendista tables

Revision ID: 0002_create_vendista_tables
Revises: 0001_create_users_table
Create Date: 2026-01-12 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_create_vendista_tables'
down_revision = '0001_create_users_table'
branch_labels = None
depends_on = None


def upgrade():
    # Create vendista_terminals table
    op.create_table(
        'vendista_terminals',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_vendista_terminals_id', 'vendista_terminals', ['id'])

    # Create vendista_tx_raw table
    op.create_table(
        'vendista_tx_raw',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('term_id', sa.BigInteger(), nullable=False),
        sa.Column('vendista_tx_id', sa.BigInteger(), nullable=False),
        sa.Column('tx_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('inserted_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('term_id', 'vendista_tx_id', name='uq_vendista_tx')
    )
    op.create_index('ix_vendista_tx_raw_id', 'vendista_tx_raw', ['id'])
    op.create_index('ix_vendista_tx_raw_term_id', 'vendista_tx_raw', ['term_id'])
    op.create_index('ix_vendista_tx_raw_vendista_tx_id', 'vendista_tx_raw', ['vendista_tx_id'])
    op.create_index('ix_vendista_tx_raw_tx_time', 'vendista_tx_raw', ['tx_time'])

    # Create sync_state table
    op.create_table(
        'sync_state',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('term_id', sa.BigInteger(), nullable=False),
        sa.Column('last_sync_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('last_tx_id', sa.BigInteger(), nullable=True),
        sa.Column('sync_status', sa.Text(), nullable=False, server_default='idle'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('term_id', name='uq_sync_state_term_id')
    )
    op.create_index('ix_sync_state_term_id', 'sync_state', ['term_id'])


def downgrade():
    op.drop_index('ix_sync_state_term_id', table_name='sync_state')
    op.drop_table('sync_state')
    
    op.drop_index('ix_vendista_tx_raw_tx_time', table_name='vendista_tx_raw')
    op.drop_index('ix_vendista_tx_raw_vendista_tx_id', table_name='vendista_tx_raw')
    op.drop_index('ix_vendista_tx_raw_term_id', table_name='vendista_tx_raw')
    op.drop_index('ix_vendista_tx_raw_id', table_name='vendista_tx_raw')
    op.drop_table('vendista_tx_raw')
    
    op.drop_index('ix_vendista_terminals_id', table_name='vendista_terminals')
    op.drop_table('vendista_terminals')
