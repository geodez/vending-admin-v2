"""Update views to use button matrices and remove machine_matrix

Revision ID: 0008
Revises: 0007
Create Date: 2026-01-19

This migration:
1. Updates vw_tx_cogs to use button_matrix system instead of machine_matrix
2. Drops machine_matrix table (replaced by button_matrices system)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    # Update vw_tx_cogs to use button_matrix system
    # New logic: terminal_matrix_map -> button_matrix_items -> drinks
    op.execute("""
        CREATE OR REPLACE VIEW vw_tx_cogs AS
        SELECT
            t.id,
            t.term_id,
            t.vendista_tx_id,
            t.tx_time::date as tx_date,
            t.tx_time,
            NULL as product_name,  -- Not available in new payload structure
            NULL as price,  -- Not available in new payload structure
            (t.payload->>'sum')::numeric / 100.0 as revenue,  -- Convert from kopecks to rubles
            (t.payload->'machine_item'->0->>'machine_item_id')::int as machine_item_id,
            vt.location_id,
            bmi.drink_id,
            d.name as drink_name,
            COALESCE(
                (SELECT SUM(di.qty_per_unit * i.cost_per_unit_rub)
                 FROM drink_items di
                 JOIN ingredients i ON i.ingredient_code = di.ingredient_code
                 WHERE di.drink_id = bmi.drink_id
                   AND i.expense_kind = 'stock_tracked'),
                0
            ) as cogs,
            (t.payload->>'sum')::numeric / 100.0 - COALESCE(
                (SELECT SUM(di.qty_per_unit * i.cost_per_unit_rub)
                 FROM drink_items di
                 JOIN ingredients i ON i.ingredient_code = di.ingredient_code
                 WHERE di.drink_id = bmi.drink_id
                   AND i.expense_kind = 'stock_tracked'),
                0
            ) as gross_profit
        FROM vendista_tx_raw t
        LEFT JOIN vendista_terminals vt ON vt.id = t.term_id
        LEFT JOIN terminal_matrix_map tmm 
            ON tmm.vendista_term_id = t.term_id 
            AND tmm.is_active = true
        LEFT JOIN button_matrix_items bmi 
            ON bmi.matrix_id = tmm.matrix_id 
            AND bmi.machine_item_id = (t.payload->'machine_item'->0->>'machine_item_id')::int
            AND bmi.is_active = true
        LEFT JOIN drinks d ON d.id = bmi.drink_id
        WHERE (t.payload->>'sum')::numeric > 0;
    """)
    
    # Drop machine_matrix table (replaced by button_matrices system)
    op.drop_table('machine_matrix')


def downgrade():
    # Recreate machine_matrix table
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
    
    # Restore old vw_tx_cogs view
    op.execute("""
        CREATE OR REPLACE VIEW vw_tx_cogs AS
        SELECT
            t.id,
            t.term_id,
            t.vendista_tx_id,
            t.tx_time::date as tx_date,
            t.tx_time,
            t.payload->>'product_name' as product_name,
            (t.payload->>'price')::numeric as price,
            (t.payload->>'fact_sum')::numeric as revenue,
            (t.payload->>'MachineItemId')::int as machine_item_id,
            mm.location_id,
            mm.drink_id,
            d.name as drink_name,
            COALESCE(
                (SELECT SUM(di.qty_per_unit * i.cost_per_unit_rub)
                 FROM drink_items di
                 JOIN ingredients i ON i.ingredient_code = di.ingredient_code
                 WHERE di.drink_id = mm.drink_id
                   AND i.expense_kind = 'stock_tracked'),
                0
            ) as cogs,
            (t.payload->>'fact_sum')::numeric - COALESCE(
                (SELECT SUM(di.qty_per_unit * i.cost_per_unit_rub)
                 FROM drink_items di
                 JOIN ingredients i ON i.ingredient_code = di.ingredient_code
                 WHERE di.drink_id = mm.drink_id
                   AND i.expense_kind = 'stock_tracked'),
                0
            ) as gross_profit
        FROM vendista_tx_raw t
        LEFT JOIN machine_matrix mm 
            ON mm.vendista_term_id = t.term_id 
            AND mm.machine_item_id = (t.payload->>'MachineItemId')::int
        LEFT JOIN drinks d ON d.id = mm.drink_id
        WHERE (t.payload->>'fact_sum')::numeric > 0;
    """)
