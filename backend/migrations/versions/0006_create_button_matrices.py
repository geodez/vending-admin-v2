"""Create button matrices and terminal matrix mapping

Revision ID: 0006
Revises: 0005
Create Date: 2026-01-19

This migration creates:
1. button_matrices - templates for button-to-drink mappings
2. button_matrix_items - items in each matrix (button -> drink + location)
3. terminal_matrix_map - assignment of terminals to matrices
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005_create_sync_runs_table'
branch_labels = None
depends_on = None


def upgrade():
    # Add location_id to vendista_terminals (terminal belongs to one location)
    op.add_column('vendista_terminals', sa.Column('location_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_vendista_terminals_location', 'vendista_terminals', 'locations', ['location_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_vendista_terminals_location_id', 'vendista_terminals', ['location_id'])
    
    # Create button_matrices table (templates)
    op.create_table(
        'button_matrices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_button_matrices_name', 'button_matrices', ['name'], unique=True)
    
    # Create button_matrix_items table (button mappings in a matrix)
    op.create_table(
        'button_matrix_items',
        sa.Column('matrix_id', sa.Integer(), nullable=False),
        sa.Column('machine_item_id', sa.Integer(), nullable=False),  # Button ID
        sa.Column('drink_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['matrix_id'], ['button_matrices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['drink_id'], ['drinks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('matrix_id', 'machine_item_id')
    )
    op.create_index('ix_button_matrix_items_matrix_id', 'button_matrix_items', ['matrix_id'])
    
    # Create terminal_matrix_map table (assign terminals to matrices)
    op.create_table(
        'terminal_matrix_map',
        sa.Column('matrix_id', sa.Integer(), nullable=False),
        sa.Column('vendista_term_id', sa.BigInteger(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['matrix_id'], ['button_matrices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vendista_term_id'], ['vendista_terminals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('matrix_id', 'vendista_term_id')
    )
    op.create_index('ix_terminal_matrix_map_term_id', 'terminal_matrix_map', ['vendista_term_id'])
    op.create_index('ix_terminal_matrix_map_matrix_id', 'terminal_matrix_map', ['matrix_id'])


def downgrade():
    op.drop_table('terminal_matrix_map')
    op.drop_table('button_matrix_items')
    op.drop_table('button_matrices')
    op.drop_index('ix_vendista_terminals_location_id', table_name='vendista_terminals')
    op.drop_constraint('fk_vendista_terminals_location', 'vendista_terminals', type_='foreignkey')
    op.drop_column('vendista_terminals', 'location_id')
