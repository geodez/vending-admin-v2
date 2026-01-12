"""create business tables

Revision ID: 0003_create_business_tables
Revises: 0002_create_vendista_tables
Create Date: 2026-01-12 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_create_business_tables'
down_revision = '0002_create_vendista_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create locations table
    op.create_table(
        'locations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create products table
    op.create_table(
        'products',
        sa.Column('product_external_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('sale_price_rub', sa.Numeric(10, 2), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('visible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('product_external_id')
    )

    # Create ingredients table
    op.create_table(
        'ingredients',
        sa.Column('ingredient_code', sa.Text(), nullable=False),
        sa.Column('ingredient_group', sa.Text(), nullable=True),
        sa.Column('brand_name', sa.Text(), nullable=True),
        sa.Column('unit', sa.Text(), nullable=False),
        sa.Column('cost_per_unit_rub', sa.Numeric(10, 2), nullable=True),
        sa.Column('default_load_qty', sa.Numeric(10, 2), nullable=True),
        sa.Column('alert_threshold', sa.Numeric(10, 2), nullable=True),
        sa.Column('alert_days_threshold', sa.Integer(), nullable=True, server_default='3'),
        sa.Column('display_name_ru', sa.Text(), nullable=True),
        sa.Column('unit_ru', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('expense_kind', sa.Text(), nullable=False, server_default='stock_tracked'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('ingredient_code')
    )

    # Create drinks table
    op.create_table(
        'drinks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create drink_items table
    op.create_table(
        'drink_items',
        sa.Column('drink_id', sa.Integer(), nullable=False),
        sa.Column('ingredient_code', sa.Text(), nullable=False),
        sa.Column('qty_per_unit', sa.Numeric(10, 2), nullable=False),
        sa.Column('unit', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['drink_id'], ['drinks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ingredient_code'], ['ingredients.ingredient_code'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('drink_id', 'ingredient_code')
    )

    # Create machine_matrix table
    op.create_table(
        'machine_matrix',
        sa.Column('vendista_term_id', sa.BigInteger(), nullable=False),
        sa.Column('machine_item_id', sa.Integer(), nullable=False),
        sa.Column('product_external_id', sa.Integer(), nullable=True),
        sa.Column('drink_id', sa.Integer(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['vendista_term_id'], ['vendista_terminals.id']),
        sa.ForeignKeyConstraint(['product_external_id'], ['products.product_external_id']),
        sa.ForeignKeyConstraint(['drink_id'], ['drinks.id']),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id']),
        sa.PrimaryKeyConstraint('vendista_term_id', 'machine_item_id')
    )

    # Create ingredient_loads table
    op.create_table(
        'ingredient_loads',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ingredient_code', sa.Text(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('load_date', sa.Date(), nullable=False),
        sa.Column('qty', sa.Numeric(10, 2), nullable=False),
        sa.Column('unit', sa.Text(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['ingredient_code'], ['ingredients.ingredient_code']),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id']),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ingredient_loads_ingredient_code', 'ingredient_loads', ['ingredient_code'])
    op.create_index('ix_ingredient_loads_location_id', 'ingredient_loads', ['location_id'])
    op.create_index('ix_ingredient_loads_load_date', 'ingredient_loads', ['load_date'])

    # Create variable_expenses table
    op.create_table(
        'variable_expenses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('expense_date', sa.Date(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('vendista_term_id', sa.BigInteger(), nullable=True),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('amount_rub', sa.Numeric(10, 2), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id']),
        sa.ForeignKeyConstraint(['vendista_term_id'], ['vendista_terminals.id']),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_variable_expenses_expense_date', 'variable_expenses', ['expense_date'])
    op.create_index('ix_variable_expenses_location_id', 'variable_expenses', ['location_id'])
    op.create_index('ix_variable_expenses_category', 'variable_expenses', ['category'])


def downgrade():
    op.drop_index('ix_variable_expenses_category', table_name='variable_expenses')
    op.drop_index('ix_variable_expenses_location_id', table_name='variable_expenses')
    op.drop_index('ix_variable_expenses_expense_date', table_name='variable_expenses')
    op.drop_table('variable_expenses')
    
    op.drop_index('ix_ingredient_loads_load_date', table_name='ingredient_loads')
    op.drop_index('ix_ingredient_loads_location_id', table_name='ingredient_loads')
    op.drop_index('ix_ingredient_loads_ingredient_code', table_name='ingredient_loads')
    op.drop_table('ingredient_loads')
    
    op.drop_table('machine_matrix')
    op.drop_table('drink_items')
    op.drop_table('drinks')
    op.drop_table('ingredients')
    op.drop_table('products')
    op.drop_table('locations')
