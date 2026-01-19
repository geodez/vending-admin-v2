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
    # Drop existing view first (PostgreSQL doesn't allow changing column types)
    op.execute("DROP VIEW IF EXISTS vw_tx_cogs CASCADE")
    op.execute("DROP VIEW IF EXISTS vw_kpi_daily CASCADE")
    op.execute("DROP VIEW IF EXISTS vw_kpi_product CASCADE")
    op.execute("DROP VIEW IF EXISTS vw_inventory_balance CASCADE")
    op.execute("DROP VIEW IF EXISTS vw_owner_report_daily CASCADE")
    
    # Update vw_tx_cogs to use button_matrix system
    # New logic: terminal_matrix_map -> button_matrix_items -> drinks
    op.execute("""
        CREATE VIEW vw_tx_cogs AS
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
                (SELECT SUM(
                    CASE 
                        -- Если единицы совпадают, просто умножаем
                        WHEN di.unit = i.unit THEN di.qty_per_unit * i.cost_per_unit_rub
                        -- Конвертация: рецепт в граммах, ингредиент в килограммах
                        WHEN di.unit = 'g' AND i.unit = 'kg' THEN di.qty_per_unit * (i.cost_per_unit_rub / 1000.0)
                        -- Конвертация: рецепт в миллилитрах, ингредиент в литрах
                        WHEN di.unit = 'ml' AND i.unit = 'l' THEN di.qty_per_unit * (i.cost_per_unit_rub / 1000.0)
                        -- Конвертация: рецепт в граммах, ингредиент в граммах (но цена за кг, если цена > 100)
                        WHEN di.unit = 'g' AND i.unit = 'g' AND i.cost_per_unit_rub > 100 THEN di.qty_per_unit * (i.cost_per_unit_rub / 1000.0)
                        -- Остальные случаи - просто умножаем (предполагаем одинаковые единицы)
                        ELSE di.qty_per_unit * i.cost_per_unit_rub
                    END
                )
                 FROM drink_items di
                 JOIN ingredients i ON i.ingredient_code = di.ingredient_code
                 WHERE di.drink_id = bmi.drink_id
                   AND i.expense_kind = 'stock_tracked'
                   AND i.cost_per_unit_rub IS NOT NULL),
                0
            ) as cogs,
            (t.payload->>'sum')::numeric / 100.0 - COALESCE(
                (SELECT SUM(
                    CASE 
                        WHEN di.unit = i.unit THEN di.qty_per_unit * i.cost_per_unit_rub
                        WHEN di.unit = 'g' AND i.unit = 'kg' THEN di.qty_per_unit * (i.cost_per_unit_rub / 1000.0)
                        WHEN di.unit = 'ml' AND i.unit = 'l' THEN di.qty_per_unit * (i.cost_per_unit_rub / 1000.0)
                        WHEN di.unit = 'g' AND i.unit = 'g' AND i.cost_per_unit_rub > 100 THEN di.qty_per_unit * (i.cost_per_unit_rub / 1000.0)
                        ELSE di.qty_per_unit * i.cost_per_unit_rub
                    END
                )
                 FROM drink_items di
                 JOIN ingredients i ON i.ingredient_code = di.ingredient_code
                 WHERE di.drink_id = bmi.drink_id
                   AND i.expense_kind = 'stock_tracked'
                   AND i.cost_per_unit_rub IS NOT NULL),
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
    
    # Create view for daily KPIs
    op.execute("""
        CREATE VIEW vw_kpi_daily AS
        SELECT
            tx_date,
            location_id,
            COUNT(*) as sales_count,
            SUM(revenue) as revenue,
            SUM(cogs) as cogs,
            SUM(gross_profit) as gross_profit,
            CASE 
                WHEN SUM(revenue) > 0 
                THEN (SUM(gross_profit) / SUM(revenue) * 100)::numeric(5,2)
                ELSE 0 
            END as gross_margin_pct
        FROM vw_tx_cogs
        GROUP BY tx_date, location_id;
    """)
    
    # Create view for product KPIs
    op.execute("""
        CREATE VIEW vw_kpi_product AS
        SELECT
            drink_id,
            drink_name,
            location_id,
            COUNT(*) as sales_count,
            SUM(revenue) as revenue,
            SUM(cogs) as cogs,
            SUM(gross_profit) as gross_profit,
            CASE 
                WHEN SUM(revenue) > 0 
                THEN (SUM(gross_profit) / SUM(revenue) * 100)::numeric(5,2)
                ELSE 0 
            END as gross_margin_pct,
            AVG(revenue) as avg_price
        FROM vw_tx_cogs
        WHERE drink_id IS NOT NULL
        GROUP BY drink_id, drink_name, location_id;
    """)
    
    # Create view for inventory balance
    op.execute("""
        CREATE VIEW vw_inventory_balance AS
        SELECT
            i.ingredient_code,
            i.display_name_ru,
            i.unit,
            i.unit_ru,
            i.cost_per_unit_rub,
            i.alert_threshold,
            i.alert_days_threshold,
            il.location_id,
            l.name as location_name,
            COALESCE(SUM(il.qty), 0) as total_loaded,
            COALESCE(
                (SELECT SUM(di.qty_per_unit)
                 FROM vw_tx_cogs t
                 JOIN drink_items di ON di.drink_id = t.drink_id
                 WHERE di.ingredient_code = i.ingredient_code
                   AND t.location_id = il.location_id),
                0
            ) as total_used,
            COALESCE(SUM(il.qty), 0) - COALESCE(
                (SELECT SUM(di.qty_per_unit)
                 FROM vw_tx_cogs t
                 JOIN drink_items di ON di.drink_id = t.drink_id
                 WHERE di.ingredient_code = i.ingredient_code
                   AND t.location_id = il.location_id),
                0
            ) as balance
        FROM ingredients i
        LEFT JOIN ingredient_loads il ON il.ingredient_code = i.ingredient_code
        LEFT JOIN locations l ON l.id = il.location_id
        WHERE i.expense_kind = 'stock_tracked'
        GROUP BY i.ingredient_code, i.display_name_ru, i.unit, i.unit_ru, 
                 i.cost_per_unit_rub, i.alert_threshold, i.alert_days_threshold,
                 il.location_id, l.name;
    """)
    
    # Create view for owner report
    op.execute("""
        CREATE VIEW vw_owner_report_daily AS
        SELECT
            k.tx_date,
            k.location_id,
            k.sales_count,
            k.revenue,
            k.cogs,
            k.gross_profit,
            k.gross_margin_pct,
            COALESCE(ve.variable_expenses, 0) as variable_expenses,
            k.gross_profit - COALESCE(ve.variable_expenses, 0) as net_profit,
            CASE 
                WHEN k.revenue > 0 
                THEN ((k.gross_profit - COALESCE(ve.variable_expenses, 0)) / k.revenue * 100)::numeric(5,2)
                ELSE 0 
            END as net_margin_pct
        FROM vw_kpi_daily k
        LEFT JOIN (
            SELECT
                expense_date,
                location_id,
                SUM(amount_rub) as variable_expenses
            FROM variable_expenses
            GROUP BY expense_date, location_id
        ) ve ON ve.expense_date = k.tx_date AND ve.location_id = k.location_id;
    """)
    
    # Drop machine_matrix table (replaced by button_matrices system)
    op.execute("DROP TABLE IF EXISTS machine_matrix")


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
