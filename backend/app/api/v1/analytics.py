"""
API endpoints for analytics and reports.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date
from app.db.session import get_db
from app.api.deps import get_current_user, require_owner
from app.models.user import User
from app.services.alert_service import AlertService, AlertType, AlertSeverity
from app.services.kpi_calculator import KPICalculator

router = APIRouter()


@router.get("/overview")
def get_overview(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get overview KPIs (for dashboard).
    Returns aggregated metrics for the specified period.
    """
    calculator = KPICalculator(db)
    return calculator.calculate_overview_kpis(from_date, to_date, location_id)


@router.get("/sales/daily")
def get_daily_sales(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get daily sales KPIs."""
    query = """
        SELECT
            tx_date,
            location_id,
            sales_count,
            revenue,
            cogs,
            gross_profit,
            gross_margin_pct
        FROM vw_kpi_daily
        WHERE 1=1
    """
    
    params = {}
    if from_date:
        query += " AND tx_date >= :from_date"
        params['from_date'] = from_date
    if to_date:
        query += " AND tx_date <= :to_date"
        params['to_date'] = to_date
    if location_id:
        query += " AND location_id = :location_id"
        params['location_id'] = location_id
    
    calculator = KPICalculator(db)
    return calculator.calculate_daily_kpis(from_date, to_date, location_id)


@router.get("/sales/by-product")
def get_sales_by_product(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sales grouped by product."""
    query = """
        SELECT
            t.drink_id,
            t.drink_name,
            t.location_id,
            COUNT(*) as sales_count,
            SUM(t.revenue) as revenue,
            SUM(t.cogs) as cogs,
            SUM(t.gross_profit) as gross_profit,
            CASE 
                WHEN SUM(t.revenue) > 0 
                THEN (SUM(t.gross_profit) / SUM(t.revenue) * 100)::numeric(5,2)
                ELSE 0 
            END as gross_margin_pct
        FROM vw_tx_cogs t
        WHERE drink_id IS NOT NULL
    """
    
    params = {}
    if from_date:
        query += " AND tx_date >= :from_date"
        params['from_date'] = from_date
    if to_date:
        query += " AND tx_date <= :to_date"
        params['to_date'] = to_date
    if location_id:
        query += " AND location_id = :location_id"
        params['location_id'] = location_id
    
    query += " GROUP BY t.drink_id, t.drink_name, t.location_id ORDER BY SUM(t.revenue) DESC"
    
    results = db.execute(text(query), params).fetchall()
    
    return [
        {
            "drink_id": row[0],
            "drink_name": row[1],
            "location_id": row[2],
            "sales_count": row[3],
            "revenue": float(row[4]),
            "cogs": float(row[5]),
            "gross_profit": float(row[6]),
            "gross_margin_pct": float(row[7])
        }
        for row in results
    ]


@router.get("/inventory/balance")
def get_inventory_balance(
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current inventory balance."""
    query = """
        SELECT
            ingredient_code,
            display_name_ru,
            unit,
            unit_ru,
            cost_per_unit_rub,
            alert_threshold,
            alert_days_threshold,
            location_id,
            location_name,
            total_loaded,
            total_used,
            balance
        FROM vw_inventory_balance
        WHERE 1=1
    """
    
    params = {}
    if location_id:
        query += " AND location_id = :location_id"
        params['location_id'] = location_id
    
    results = db.execute(text(query), params).fetchall()
    
    return [
        {
            "ingredient_code": row[0],
            "display_name_ru": row[1],
            "unit": row[2],
            "unit_ru": row[3],
            "cost_per_unit_rub": float(row[4]) if row[4] else None,
            "alert_threshold": float(row[5]) if row[5] else None,
            "alert_days_threshold": row[6],
            "location_id": row[7],
            "location_name": row[8],
            "total_loaded": float(row[9]),
            "total_used": float(row[10]),
            "balance": float(row[11]),
            "is_low_stock": float(row[11]) <= float(row[5]) if row[5] else False
        }
        for row in results
    ]


@router.get("/owner-report")
def get_owner_report(
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    """
    Get owner report (Owner only).
    Returns aggregated financial metrics for the period.
    
    Query params:
      period_start: YYYY-MM-DD (default: first day of current month)
      period_end:   YYYY-MM-DD (default: today)
    
    Requires: role='owner'
    Returns: 403 if accessed by non-owner, 422 if period_end < period_start
    """
    from datetime import datetime, timezone
    
    # Нормализация периода (по умолчанию: текущий месяц)
    if not period_start:
        now = datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
    if not period_end:
        period_end = datetime.now(timezone.utc).date()
    
    # Валидация периода
    if period_end < period_start:
        raise HTTPException(
            status_code=422,
            detail="period_end must be >= period_start"
        )
    
    # Агрегированный запрос из view vw_owner_report_daily
    query = """
        SELECT
            COALESCE(SUM(sales_count), 0) as transactions_count,
            COALESCE(SUM(revenue), 0) as revenue_gross,
            COALESCE(SUM(cogs), 0) as cogs_total,
            COALESCE(SUM(variable_expenses), 0) as expenses_total,
            COALESCE(SUM(net_profit), 0) as net_profit
        FROM vw_owner_report_daily
        WHERE tx_date >= :from_date AND tx_date <= :to_date
    """
    
    params = {'from_date': period_start, 'to_date': period_end}
    if location_id:
        query += " AND location_id = :location_id"
        params['location_id'] = location_id
    
    result = db.execute(text(query), params).fetchone()
    
    # Агрегированные значения
    transactions_count = int(result[0]) if result[0] else 0
    revenue_gross = float(result[1]) if result[1] else 0.0
    cogs_total = float(result[2]) if result[2] else 0.0
    expenses_total = float(result[3]) if result[3] else 0.0
    net_profit = float(result[4]) if result[4] else 0.0
    
    # FALLBACK: если vw_owner_report_daily пустая, используем vw_kpi_daily
    if transactions_count == 0 and revenue_gross == 0.0:
        fallback_query = """
            SELECT
                COALESCE(SUM(sales_count), 0) as transactions_count,
                COALESCE(SUM(revenue), 0) as revenue_gross,
                COALESCE(SUM(cogs), 0) as cogs_total
            FROM vw_kpi_daily
            WHERE tx_date >= :from_date AND tx_date <= :to_date
        """
        if location_id:
            fallback_query += " AND location_id = :location_id"
        
        fallback_result = db.execute(text(fallback_query), params).fetchone()
        
        if fallback_result and fallback_result[0] and fallback_result[0] > 0:
            transactions_count = int(fallback_result[0])
            revenue_gross = float(fallback_result[1]) if fallback_result[1] else 0.0
            cogs_total = float(fallback_result[2]) if fallback_result[2] else 0.0
            
            # Расходы из variable_expenses (через vendista_term_id, location_id может быть NULL)
            expense_query = """
                SELECT COALESCE(SUM(ve.amount_rub), 0)
                FROM variable_expenses ve
                LEFT JOIN vendista_terminals vt ON vt.id = ve.vendista_term_id
                WHERE ve.expense_date >= :from_date AND ve.expense_date <= :to_date
            """
            if location_id:
                expense_query += " AND COALESCE(vt.location_id, -1) = :location_id"
            
            exp_result = db.execute(text(expense_query), params).fetchone()
            expenses_total = float(exp_result[0]) if exp_result else 0.0
        else:
            # Если и vw_kpi_daily пустая, пробуем vw_tx_cogs
            tx_cogs_query = """
                SELECT
                    COUNT(*) as transactions_count,
                    COALESCE(SUM(revenue), 0) as revenue_gross,
                    COALESCE(SUM(cogs), 0) as cogs_total
                FROM vw_tx_cogs
                WHERE tx_date >= :from_date AND tx_date <= :to_date
            """
            if location_id:
                tx_cogs_query += " AND location_id = :location_id"
            
            tx_cogs_result = db.execute(text(tx_cogs_query), params).fetchone()
            
            if tx_cogs_result and tx_cogs_result[0] > 0:
                transactions_count = int(tx_cogs_result[0])
                revenue_gross = float(tx_cogs_result[1]) if tx_cogs_result[1] else 0.0
                cogs_total = float(tx_cogs_result[2]) if tx_cogs_result[2] else 0.0
                
                # Расходы из variable_expenses (через vendista_term_id, location_id может быть NULL)
                if expenses_total == 0.0:
                    expense_query = """
                        SELECT COALESCE(SUM(ve.amount_rub), 0)
                        FROM variable_expenses ve
                        LEFT JOIN vendista_terminals vt ON vt.id = ve.vendista_term_id
                        WHERE ve.expense_date >= :from_date AND ve.expense_date <= :to_date
                    """
                    if location_id:
                        expense_query += " AND COALESCE(vt.location_id, -1) = :location_id"
                    
                    exp_result = db.execute(text(expense_query), params).fetchone()
                    expenses_total = float(exp_result[0]) if exp_result else 0.0
    
    # Комиссии: 8.95% от выручки
    fees_total = round(revenue_gross * 0.0895, 2)
    
    # Чистая прибыль: выручка - COGS - комиссии - переменные расходы
    # Если net_profit уже рассчитан из view (с учетом переменных расходов), используем его
    # Иначе считаем: gross_profit - комиссии - переменные расходы
    if net_profit != 0.0 or (transactions_count > 0 and revenue_gross > 0):
        # Если есть данные из view, используем их, но вычитаем комиссии
        gross_profit = revenue_gross - cogs_total
        final_net_profit = gross_profit - fees_total - expenses_total
    else:
        # Если данных нет, возвращаем 0
        final_net_profit = 0.0
    
    # Дополнительные метрики
    avg_check = revenue_gross / transactions_count if transactions_count > 0 else 0.0
    gross_profit = revenue_gross - cogs_total
    gross_margin_pct = (gross_profit / revenue_gross * 100) if revenue_gross > 0 else 0.0
    net_margin_pct = (final_net_profit / revenue_gross * 100) if revenue_gross > 0 else 0.0
    
    # Топ продукты за период
    top_products_query = """
        SELECT
            drink_id,
            drink_name,
            COUNT(*) as sales_count,
            SUM(revenue) as revenue,
            SUM(cogs) as cogs,
            SUM(gross_profit) as gross_profit
        FROM vw_tx_cogs
        WHERE tx_date >= :from_date AND tx_date <= :to_date
    """
    if location_id:
        top_products_query += " AND location_id = :location_id"
    top_products_query += """
        GROUP BY drink_id, drink_name
        ORDER BY SUM(revenue) DESC
        LIMIT 10
    """
    top_products_result = db.execute(text(top_products_query), params).fetchall()
    top_products = [
        {
            "drink_id": row[0],
            "drink_name": row[1],
            "sales_count": int(row[2]),
            "revenue": float(row[3]),
            "cogs": float(row[4]),
            "gross_profit": float(row[5])
        }
        for row in top_products_result
    ]
    
    return {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "revenue_gross": revenue_gross,
        "fees_total": fees_total,
        "expenses_total": expenses_total,
        "net_profit": final_net_profit,
        "transactions_count": transactions_count,
        "avg_check": round(avg_check, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin_pct": round(gross_margin_pct, 2),
        "net_margin_pct": round(net_margin_pct, 2),
        "cogs_total": round(cogs_total, 2),
        "top_products": top_products
    }


@router.get("/sales/summary")
def get_sales_summary(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get sales summary with aggregated metrics.
    """
    calculator = KPICalculator(db)
    return calculator.calculate_sales_summary(from_date, to_date, location_id)


@router.get("/sales/summary-old")
def get_sales_summary(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get sales summary (aggregated statistics).
    Returns overall metrics for the period.
    """
    query = """
        SELECT
            COUNT(*) as total_sales,
            SUM(revenue) as total_revenue,
            SUM(cogs) as total_cogs,
            SUM(gross_profit) as total_gross_profit,
            CASE 
                WHEN SUM(revenue) > 0 
                THEN (SUM(gross_profit) / SUM(revenue) * 100)::numeric(5,2)
                ELSE 0 
            END as gross_margin_pct,
            COUNT(DISTINCT drink_id) as unique_drinks,
            COUNT(DISTINCT term_id) as active_terminals,
            COUNT(DISTINCT location_id) as active_locations,
            AVG(revenue) as avg_transaction_value
        FROM vw_tx_cogs
        WHERE 1=1
    """
    
    params = {}
    if from_date:
        query += " AND tx_date >= :from_date"
        params['from_date'] = from_date
    if to_date:
        query += " AND tx_date <= :to_date"
        params['to_date'] = to_date
    if location_id:
        query += " AND location_id = :location_id"
        params['location_id'] = location_id
    
    result = db.execute(text(query), params).fetchone()
    
    return {
        "total_sales": result[0] or 0,
        "total_revenue": float(result[1] or 0),
        "total_cogs": float(result[2] or 0),
        "total_gross_profit": float(result[3] or 0),
        "gross_margin_pct": float(result[4] or 0),
        "unique_drinks": result[5] or 0,
        "active_terminals": result[6] or 0,
        "active_locations": result[7] or 0,
        "avg_transaction_value": float(result[8] or 0)
    }


@router.get("/sales/margin")
def get_sales_margin(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    location_id: Optional[int] = None,
    min_margin: Optional[float] = Query(None, description="Minimum margin threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed margin analysis by products.
    """
    calculator = KPICalculator(db)
    return calculator.calculate_margin_analysis(from_date, to_date, location_id, min_margin)


@router.get("/sales/margin-old")
def get_sales_margin(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    location_id: Optional[int] = None,
    compare_from_date: Optional[date] = None,
    compare_to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed margin analysis by products.
    Optionally compares margins between two periods.
    """
    # Main period query
    query = """
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
            END as margin_pct,
            AVG(revenue) as avg_price
        FROM vw_tx_cogs
        WHERE drink_id IS NOT NULL
    """
    
    params = {}
    if from_date:
        query += " AND tx_date >= :from_date"
        params['from_date'] = from_date
    if to_date:
        query += " AND tx_date <= :to_date"
        params['to_date'] = to_date
    if location_id:
        query += " AND location_id = :location_id"
        params['location_id'] = location_id
    
    query += " GROUP BY drink_id, drink_name, location_id ORDER BY SUM(revenue) DESC"
    
    results = db.execute(text(query), params).fetchall()
    
    products = [
        {
            "drink_id": row[0],
            "drink_name": row[1],
            "location_id": row[2],
            "sales_count": int(row[3]),
            "revenue": float(row[4]),
            "cogs": float(row[5]),
            "gross_profit": float(row[6]),
            "margin_pct": float(row[7]),
            "avg_price": float(row[8] or 0)
        }
        for row in results
    ]
    
    # Comparison period (if provided)
    comparison = None
    if compare_from_date and compare_to_date:
        compare_query = query.replace(":from_date", ":compare_from_date").replace(":to_date", ":compare_to_date")
        compare_params = params.copy()
        compare_params['compare_from_date'] = compare_from_date
        compare_params['compare_to_date'] = compare_to_date
        if 'from_date' in compare_params:
            del compare_params['from_date']
        if 'to_date' in compare_params:
            del compare_params['to_date']
        
        compare_results = db.execute(text(compare_query), compare_params).fetchall()
        
        comparison = [
            {
                "drink_id": row[0],
                "drink_name": row[1],
                "location_id": row[2],
                "sales_count": int(row[3]),
                "revenue": float(row[4]),
                "cogs": float(row[5]),
                "gross_profit": float(row[6]),
                "margin_pct": float(row[7]),
                "avg_price": float(row[8] or 0)
            }
            for row in compare_results
        ]
    
    return {
        "period": {
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None
        },
        "products": products,
        "comparison": comparison,
        "comparison_period": {
            "from_date": compare_from_date.isoformat() if compare_from_date else None,
            "to_date": compare_to_date.isoformat() if compare_to_date else None
        } if comparison else None
    }


@router.get("/owner-report/daily")
def get_owner_report_daily(
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    """
    Get detailed owner report by days (Owner only).
    Returns daily breakdown of financial metrics.
    """
    from datetime import datetime, timezone
    
    # Normalize period
    if not period_start:
        now = datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
    if not period_end:
        period_end = datetime.now(timezone.utc).date()
    
    if period_end < period_start:
        raise HTTPException(status_code=422, detail="period_end must be >= period_start")
    
    # Query daily data from vw_owner_report_daily
    query = """
        SELECT
            tx_date,
            location_id,
            sales_count,
            revenue,
            cogs,
            variable_expenses,
            net_profit,
            CASE 
                WHEN revenue > 0 
                THEN ((revenue - cogs) / revenue * 100)::numeric(5,2)
                ELSE 0 
            END as gross_margin_pct,
            CASE 
                WHEN revenue > 0 
                THEN (net_profit / revenue * 100)::numeric(5,2)
                ELSE 0 
            END as net_margin_pct
        FROM vw_owner_report_daily
        WHERE tx_date >= :from_date AND tx_date <= :to_date
    """
    
    params = {'from_date': period_start, 'to_date': period_end}
    if location_id:
        query += " AND location_id = :location_id"
        params['location_id'] = location_id
    
    query += " ORDER BY tx_date DESC"
    
    results = db.execute(text(query), params).fetchall()
    
    # If vw_owner_report_daily is empty, fallback to vw_kpi_daily
    if not results:
        fallback_query = """
            SELECT
                tx_date,
                location_id,
                sales_count,
                revenue,
                cogs,
                0 as variable_expenses,
                revenue - cogs as net_profit,
                gross_margin_pct,
                0 as net_margin_pct
            FROM vw_kpi_daily
            WHERE tx_date >= :from_date AND tx_date <= :to_date
        """
        if location_id:
            fallback_query += " AND location_id = :location_id"
        fallback_query += " ORDER BY tx_date DESC"
        
        results = db.execute(text(fallback_query), params).fetchall()
    
    daily_data = [
        {
            "date": row[0].isoformat() if row[0] else None,
            "location_id": row[1],
            "sales_count": int(row[2] or 0),
            "revenue": float(row[3] or 0),
            "cogs": float(row[4] or 0),
            "variable_expenses": float(row[5] or 0),
            "net_profit": float(row[6] or 0),
            "gross_margin_pct": float(row[7] or 0),
            "net_margin_pct": float(row[8] or 0)
        }
        for row in results
    ]
    
    return {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "daily_data": daily_data
    }


@router.get("/owner-report/issues")
def get_owner_report_issues(
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    """
    Get list of issues and alerts (Owner only).
    Returns:
    - Critical stock levels (low inventory)
    - Low margin products (< 30%)
    - Sync errors (from sync_runs)
    """
    issues = []
    
    # 1. Critical stock levels
    stock_query = """
        SELECT
            ingredient_code,
            display_name_ru,
            location_id,
            location_name,
            balance,
            alert_threshold,
            unit
        FROM vw_inventory_balance
        WHERE alert_threshold IS NOT NULL 
          AND balance <= alert_threshold
    """
    params = {}
    if location_id:
        stock_query += " AND location_id = :location_id"
        params['location_id'] = location_id
    
    stock_results = db.execute(text(stock_query), params).fetchall()
    for row in stock_results:
        issues.append({
            "type": "low_stock",
            "severity": "critical",
            "ingredient_code": row[0],
            "ingredient_name": row[1],
            "location_id": row[2],
            "location_name": row[3],
            "balance": float(row[4]),
            "threshold": float(row[5]) if row[5] else None,
            "unit": row[6],
            "message": f"Low stock: {row[1]} at {row[3]} ({row[4]} {row[6]} <= {row[5]} {row[6]})"
        })
    
    # 2. Low margin products (< 30%)
    margin_query = """
        SELECT
            drink_id,
            drink_name,
            location_id,
            gross_margin_pct,
            revenue,
            sales_count
        FROM vw_kpi_product
        WHERE gross_margin_pct < 30 AND revenue > 0
    """
    if location_id:
        margin_query += " AND location_id = :location_id"
    margin_query += " ORDER BY revenue DESC LIMIT 20"
    
    margin_results = db.execute(text(margin_query), params).fetchall()
    for row in margin_results:
        issues.append({
            "type": "low_margin",
            "severity": "warning",
            "drink_id": row[0],
            "drink_name": row[1],
            "location_id": row[2],
            "margin_pct": float(row[3]),
            "revenue": float(row[4]),
            "sales_count": int(row[5]),
            "message": f"Low margin: {row[1]} ({row[3]:.1f}% margin)"
        })
    
    # 3. Sync errors (from sync_runs)
    sync_query = """
        SELECT
            id,
            started_at,
            completed_at,
            period_start,
            period_end,
            message,
            ok
        FROM sync_runs
        WHERE ok = false
        ORDER BY started_at DESC
        LIMIT 10
    """
    sync_results = db.execute(text(sync_query)).fetchall()
    for row in sync_results:
        issues.append({
            "type": "sync_error",
            "severity": "error",
            "sync_run_id": row[0],
            "started_at": row[1].isoformat() if row[1] else None,
            "completed_at": row[2].isoformat() if row[2] else None,
            "period_start": row[3].isoformat() if row[3] else None,
            "period_end": row[4].isoformat() if row[4] else None,
            "message": row[5] or "Sync failed",
            "ok": row[6]
        })
    
    return {
        "total_issues": len(issues),
        "by_type": {
            "low_stock": len([i for i in issues if i["type"] == "low_stock"]),
            "low_margin": len([i for i in issues if i["type"] == "low_margin"]),
            "sync_error": len([i for i in issues if i["type"] == "sync_error"])
        },
        "issues": issues
    }


@router.get("/alerts")
def get_alerts(
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type (low_stock, low_margin, sync_error, expiring_stock)"),
    severity: Optional[str] = Query(None, description="Filter by severity (critical, warning, info)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of active alerts.
    
    Returns alerts for:
    - Low stock levels (based on alert_threshold)
    - Low margin products (< 30%)
    - Sync errors (from last 7 days)
    - Expiring stock (based on alert_days_threshold)
    
    Filters:
    - location_id: Filter alerts by location
    - alert_type: Filter by type (low_stock, low_margin, sync_error, expiring_stock)
    - severity: Filter by severity (critical, warning, info)
    """
    service = AlertService(db)
    
    # Convert string parameters to enums if provided
    alert_type_enum = None
    if alert_type:
        try:
            alert_type_enum = AlertType(alert_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid alert_type: {alert_type}")
    
    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    
    alerts = service.get_all_alerts(
        location_id=location_id,
        alert_type=alert_type_enum,
        severity=severity_enum
    )
    
    summary = service.get_alert_summary(location_id=location_id)
    
    return {
        "alerts": alerts,
        "summary": summary
    }
