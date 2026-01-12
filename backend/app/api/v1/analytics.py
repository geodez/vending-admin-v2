"""
API endpoints for analytics and reports.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date
from app.db.session import get_db
from app.api.deps import get_current_user
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
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get owner report (Owner only).
    Includes net profit calculation with variable expenses.
    """
    # Check if user is owner
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can access this report")
    
    query = """
        SELECT
            tx_date,
            location_id,
            sales_count,
            revenue,
            cogs,
            gross_profit,
            gross_margin_pct,
            variable_expenses,
            net_profit,
            net_margin_pct
        FROM vw_owner_report_daily
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
            "gross_margin_pct": float(row[6]),
            "variable_expenses": float(row[7]),
            "net_profit": float(row[8]),
            "net_margin_pct": float(row[9])
        }
        for row in results
    ]
