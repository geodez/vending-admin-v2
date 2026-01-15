"""
API endpoints for analytics and reports.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date
from app.db.session import get_db
from app.api.deps import get_current_user, require_owner
from app.models.user import User

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
            COUNT(DISTINCT term_id) as active_terminals
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
    
    # Get variable expenses for same period
    expense_query = """
        SELECT COALESCE(SUM(amount_rub), 0) as total_expenses
        FROM variable_expenses
        WHERE 1=1
    """
    if from_date:
        expense_query += " AND expense_date >= :from_date"
    if to_date:
        expense_query += " AND expense_date <= :to_date"
    if location_id:
        expense_query += " AND location_id = :location_id"
    
    expenses_result = db.execute(text(expense_query), params).fetchone()
    total_expenses = expenses_result[0] if expenses_result else 0
    
    # Calculate net profit
    net_profit = (result[3] or 0) - total_expenses  # gross_profit - expenses
    net_margin_pct = (net_profit / result[1] * 100) if result[1] and result[1] > 0 else 0
    
    return {
        "total_sales": result[0] or 0,
        "total_revenue": float(result[1] or 0),
        "total_cogs": float(result[2] or 0),
        "total_gross_profit": float(result[3] or 0),
        "gross_margin_pct": float(result[4] or 0),
        "unique_drinks": result[5] or 0,
        "active_terminals": result[6] or 0,
        "total_variable_expenses": float(total_expenses),
        "net_profit": float(net_profit),
        "net_margin_pct": float(net_margin_pct)
    }


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
    
    query += " ORDER BY tx_date DESC"
    
    results = db.execute(text(query), params).fetchall()
    
    return [
        {
            "date": row[0],
            "location_id": row[1],
            "sales_count": row[2],
            "revenue": float(row[3]),
            "cogs": float(row[4]),
            "gross_profit": float(row[5]),
            "gross_margin_pct": float(row[6])
        }
        for row in results
    ]


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
    expenses_total = float(result[3]) if result[3] else 0.0
    net_profit = float(result[4]) if result[4] else 0.0
    
    # FALLBACK: если vw_owner_report_daily пустая, считаем из vendista_tx_raw
    if transactions_count == 0 and revenue_gross == 0.0:
        fallback_query = """
            SELECT
                COUNT(*) as tx_count,
                COALESCE(SUM((payload->>'sum')::numeric), 0) as sum_kopecks
            FROM vendista_tx_raw
            WHERE tx_time::date >= :from_date AND tx_time::date <= :to_date
              AND (payload->>'sum') IS NOT NULL
              AND (payload->>'sum')::numeric > 0
        """
        fallback_result = db.execute(text(fallback_query), params).fetchone()
        
        if fallback_result and fallback_result[0] > 0:
            transactions_count = int(fallback_result[0])
            # Vendista sum в копейках, конвертируем в рубли
            revenue_gross = round(float(fallback_result[1]) / 100, 2)
            
            # Расходы из variable_expenses
            expense_query = """
                SELECT COALESCE(SUM(amount_rub), 0)
                FROM variable_expenses
                WHERE expense_date >= :from_date AND expense_date <= :to_date
            """
            exp_result = db.execute(text(expense_query), params).fetchone()
            expenses_total = float(exp_result[0]) if exp_result else 0.0
    
    # Комиссии: 8.95% от выручки
    fees_total = round(revenue_gross * 0.0895, 2)
    
    # Чистая прибыль
    if revenue_gross > 0:
        final_net_profit = revenue_gross - fees_total - expenses_total
    else:
        final_net_profit = net_profit - fees_total
    
    return {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "revenue_gross": revenue_gross,
        "fees_total": fees_total,
        "expenses_total": expenses_total,
        "net_profit": final_net_profit,
        "transactions_count": transactions_count
    }
