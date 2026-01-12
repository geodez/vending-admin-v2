"""create kpi views

Revision ID: 0004_create_kpi_views
Revises: 0003_create_business_tables
Create Date: 2026-01-12 21:15:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '0004_create_kpi_views'
down_revision = '0003_create_business_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create view for transactions with COGS
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

    # Create view for daily KPIs
    op.execute("""
        CREATE OR REPLACE VIEW vw_kpi_daily AS
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
        CREATE OR REPLACE VIEW vw_kpi_product AS
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
        CREATE OR REPLACE VIEW vw_inventory_balance AS
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
        CREATE OR REPLACE VIEW vw_owner_report_daily AS
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


def downgrade():
    op.execute("DROP VIEW IF EXISTS vw_owner_report_daily")
    op.execute("DROP VIEW IF EXISTS vw_inventory_balance")
    op.execute("DROP VIEW IF EXISTS vw_kpi_product")
    op.execute("DROP VIEW IF EXISTS vw_kpi_daily")
    op.execute("DROP VIEW IF EXISTS vw_tx_cogs")
