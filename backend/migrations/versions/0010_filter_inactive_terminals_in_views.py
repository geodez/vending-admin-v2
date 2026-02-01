"""Filter inactive terminals in inventory/analytics views

Revision ID: 0010
Revises: 0009
Create Date: 2026-02-01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade():
    # Drop dependent views first
    op.execute("DROP VIEW IF EXISTS vw_tx_cogs CASCADE")
    op.execute("DROP VIEW IF EXISTS vw_kpi_daily CASCADE")
    op.execute("DROP VIEW IF EXISTS vw_kpi_product CASCADE")
    op.execute("DROP VIEW IF EXISTS vw_inventory_balance CASCADE")
    op.execute("DROP VIEW IF EXISTS vw_owner_report_daily CASCADE")

    op.execute("""
        CREATE VIEW vw_tx_cogs AS
        SELECT
            t.id,
            t.term_id,
            t.vendista_tx_id,
            t.tx_time::date as tx_date,
            t.tx_time,
            NULL as product_name,
            NULL as price,
            (t.payload->>'sum')::numeric / 100.0 as revenue,
            (t.payload->'machine_item'->0->>'machine_item_id')::int as machine_item_id,
            vt.location_id,
            bmi.drink_id,
            d.name as drink_name,
            COALESCE(
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
        WHERE (t.payload->>'sum')::numeric > 0
          AND vt.is_active IS DISTINCT FROM false;
    """)

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

    op.execute("""
        CREATE VIEW vw_kpi_product AS
        SELECT
            tx_date,
            location_id,
            drink_id,
            drink_name,
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
        GROUP BY tx_date, location_id, drink_id, drink_name;
    """)

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
                ve.expense_date,
                COALESCE(vt.location_id, NULL) as location_id,
                SUM(ve.amount_rub) as variable_expenses
            FROM variable_expenses ve
            LEFT JOIN vendista_terminals vt ON vt.id = ve.vendista_term_id
            WHERE vt.is_active IS DISTINCT FROM false
            GROUP BY ve.expense_date, COALESCE(vt.location_id, NULL)
        ) ve ON ve.expense_date = k.tx_date AND COALESCE(ve.location_id, -1) = COALESCE(k.location_id, -1);
    """)


def downgrade():
    # Recreate views without filtering inactive terminals
    op.execute("DROP VIEW IF EXISTS vw_tx_cogs CASCADE")
    op.execute("DROP VIEW IF EXISTS vw_kpi_daily CASCADE")
    op.execute("DROP VIEW IF EXISTS vw_kpi_product CASCADE")
    op.execute("DROP VIEW IF EXISTS vw_inventory_balance CASCADE")
    op.execute("DROP VIEW IF EXISTS vw_owner_report_daily CASCADE")

    op.execute("""
        CREATE VIEW vw_tx_cogs AS
        SELECT
            t.id,
            t.term_id,
            t.vendista_tx_id,
            t.tx_time::date as tx_date,
            t.tx_time,
            NULL as product_name,
            NULL as price,
            (t.payload->>'sum')::numeric / 100.0 as revenue,
            (t.payload->'machine_item'->0->>'machine_item_id')::int as machine_item_id,
            vt.location_id,
            bmi.drink_id,
            d.name as drink_name,
            COALESCE(
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

    op.execute("""
        CREATE VIEW vw_kpi_product AS
        SELECT
            tx_date,
            location_id,
            drink_id,
            drink_name,
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
        GROUP BY tx_date, location_id, drink_id, drink_name;
    """)

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
                ve.expense_date,
                COALESCE(vt.location_id, NULL) as location_id,
                SUM(ve.amount_rub) as variable_expenses
            FROM variable_expenses ve
            LEFT JOIN vendista_terminals vt ON vt.id = ve.vendista_term_id
            GROUP BY ve.expense_date, COALESCE(vt.location_id, NULL)
        ) ve ON ve.expense_date = k.tx_date AND COALESCE(ve.location_id, -1) = COALESCE(k.location_id, -1);
    """)
