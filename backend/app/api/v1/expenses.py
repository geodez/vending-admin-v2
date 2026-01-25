"""
API endpoints for Expenses (variable_expenses table CRUD).
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, date, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class ExpenseCreate(BaseModel):
    expense_date: date
    vendista_term_id: int = Field(..., gt=0)
    location_id: Optional[int] = None  # deprecated, kept for backward compatibility
    category: str = Field(..., min_length=1, max_length=50)
    amount_rub: float = Field(..., gt=0)
    comment: Optional[str] = None


class ExpenseUpdate(BaseModel):
    expense_date: Optional[date] = None
    vendista_term_id: Optional[int] = None
    location_id: Optional[int] = None  # deprecated, kept for backward compatibility
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    amount_rub: Optional[float] = Field(None, gt=0)
    comment: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: int
    expense_date: date
    vendista_term_id: Optional[int]
    location_id: Optional[int]  # May be NULL since locations don't exist as entities
    category: str
    amount_rub: float
    comment: Optional[str]
    created_at: datetime
    updated_at: datetime


@router.get("", response_model=List[ExpenseResponse])
@router.get("/", response_model=List[ExpenseResponse])
async def get_expenses(
    period_start: Optional[date] = Query(None),
    period_end: Optional[date] = Query(None),
    location_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of expenses with optional filters.
    
    Owner-only access.
    """
    # Check permission
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can view expenses"
        )
    
    # Default period
    today = datetime.utcnow().date()
    if period_end is None:
        period_end = today
    if period_start is None:
        period_start = today.replace(day=1)
    
    # Build WHERE clause
    where_clauses = [
        "expense_date >= :period_start",
        "expense_date <= :period_end"
    ]
    params = {
        "period_start": period_start,
        "period_end": period_end
    }
    
    if location_id is not None:
        where_clauses.append("location_id = :location_id")
        params["location_id"] = location_id
    
    if category:
        where_clauses.append("category = :category")
        params["category"] = category
    
    where_sql = " AND ".join(where_clauses)
    
    query = text(f"""
        SELECT id, expense_date, vendista_term_id, location_id, category, amount_rub, comment, created_at, updated_at
        FROM variable_expenses
        WHERE {where_sql}
        ORDER BY expense_date DESC, created_at DESC
    """)
    
    result = db.execute(query, params)
    rows = result.fetchall()
    
    expenses = []
    for row in rows:
        expenses.append({
            "id": row[0],
            "expense_date": row[1],
            "vendista_term_id": row[2],
            "location_id": row[3] if row[3] is not None else None,  # Handle NULL location_id
            "category": row[4],
            "amount_rub": float(row[5]),
            "comment": row[6],
            "created_at": row[7],
            "updated_at": row[8]
        })
    
    return expenses


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new expense record.
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can create expenses"
        )
    
    vendista_term_id = expense.vendista_term_id
    terminal_exists = db.execute(
        text("SELECT 1 FROM vendista_terminals WHERE id = :id LIMIT 1"),
        {"id": vendista_term_id},
    ).fetchone()
    if not terminal_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Terminal id={vendista_term_id} not found"
        )
    
    # Use explicit NULL for location_id in SQL, don't pass it in parameters
    query = text("""
        INSERT INTO variable_expenses (expense_date, location_id, vendista_term_id, category, amount_rub, comment, created_at, updated_at, created_by_user_id)
        VALUES (:expense_date, NULL, :vendista_term_id, :category, :amount_rub, :comment, NOW(), NOW(), :created_by_user_id)
        RETURNING id, expense_date, vendista_term_id, location_id, category, amount_rub, comment, created_at, updated_at
    """)
    
    # Don't include location_id in params - it's set to NULL in SQL
    result = db.execute(query, {
        "expense_date": expense.expense_date,
        "vendista_term_id": vendista_term_id,  # Use terminal id
        "category": expense.category,
        "amount_rub": expense.amount_rub,
        "comment": expense.comment,
        "created_by_user_id": current_user.id
    })
    db.commit()
    
    row = result.fetchone()
    
    return {
        "id": row[0],
        "expense_date": row[1],
        "vendista_term_id": row[2],
        "location_id": row[3] if row[3] is not None else None,  # Handle NULL location_id
        "category": row[4],
        "amount_rub": float(row[5]),
        "comment": row[6],
        "created_at": row[7],
        "updated_at": row[8]
    }


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    expense: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing expense record.
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can update expenses"
        )
    
    # Build SET clause dynamically
    updates = []
    params = {"expense_id": expense_id}
    
    if expense.expense_date is not None:
        updates.append("expense_date = :expense_date")
        params["expense_date"] = expense.expense_date
    
    if expense.vendista_term_id is not None:
        terminal_exists = db.execute(
            text("SELECT 1 FROM vendista_terminals WHERE id = :id LIMIT 1"),
            {"id": expense.vendista_term_id},
        ).fetchone()
        if not terminal_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Terminal id={expense.vendista_term_id} not found"
            )
        updates.append("vendista_term_id = :vendista_term_id")
        params["vendista_term_id"] = expense.vendista_term_id
        # Set location_id to NULL since locations don't exist as entities
        updates.append("location_id = NULL")
    
    if expense.category is not None:
        updates.append("category = :category")
        params["category"] = expense.category
    
    if expense.amount_rub is not None:
        updates.append("amount_rub = :amount_rub")
        params["amount_rub"] = expense.amount_rub
    
    if expense.comment is not None:
        updates.append("comment = :comment")
        params["comment"] = expense.comment
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields to update"
        )
    
    updates.append("updated_at = NOW()")
    set_sql = ", ".join(updates)
    
    query = text(f"""
        UPDATE variable_expenses
        SET {set_sql}
        WHERE id = :expense_id
        RETURNING id, expense_date, vendista_term_id, location_id, category, amount_rub, comment, created_at, updated_at
    """)
    
    result = db.execute(query, params)
    db.commit()
    
    row = result.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    return {
        "id": row[0],
        "expense_date": row[1],
        "vendista_term_id": row[2],
        "location_id": row[3],
        "category": row[4],
        "amount_rub": float(row[5]),
        "comment": row[6],
        "created_at": row[7],
        "updated_at": row[8]
    }


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an expense record.
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can delete expenses"
        )
    
    query = text("DELETE FROM variable_expenses WHERE id = :expense_id")
    result = db.execute(query, {"expense_id": expense_id})
    db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    return None


@router.get("/analytics")
async def get_expenses_analytics(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    location_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get expenses analytics:
    - Daily expenses chart
    - Comparison between categories
    - Expense trends
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can view expense analytics"
        )
    
    # Default period
    today = datetime.utcnow().date()
    if to_date is None:
        to_date = today
    if from_date is None:
        from_date = today.replace(day=1)
    
    params = {
        "from_date": from_date,
        "to_date": to_date
    }
    
    # Daily expenses
    daily_query = """
        SELECT
            expense_date,
            SUM(amount_rub) as total_amount,
            COUNT(*) as expense_count
        FROM variable_expenses
        WHERE expense_date >= :from_date AND expense_date <= :to_date
    """
    if location_id is not None:
        daily_query += " AND location_id = :location_id"
        params["location_id"] = location_id
    daily_query += " GROUP BY expense_date ORDER BY expense_date"
    
    daily_results = db.execute(text(daily_query), params).fetchall()
    daily_data = [
        {
            "date": row[0].isoformat() if row[0] else None,
            "total_amount": float(row[1] or 0),
            "expense_count": int(row[2] or 0)
        }
        for row in daily_results
    ]
    
    # Expenses by category
    category_query = """
        SELECT
            category,
            SUM(amount_rub) as total_amount,
            COUNT(*) as expense_count,
            AVG(amount_rub) as avg_amount
        FROM variable_expenses
        WHERE expense_date >= :from_date AND expense_date <= :to_date
    """
    if location_id is not None:
        category_query += " AND location_id = :location_id"
    category_query += " GROUP BY category ORDER BY SUM(amount_rub) DESC"
    
    category_results = db.execute(text(category_query), params).fetchall()
    category_data = [
        {
            "category": row[0],
            "total_amount": float(row[1] or 0),
            "expense_count": int(row[2] or 0),
            "avg_amount": float(row[3] or 0)
        }
        for row in category_results
    ]
    
    # Trends: compare current period with previous period
    period_days = (to_date - from_date).days + 1
    prev_from_date = from_date - timedelta(days=period_days)
    prev_to_date = from_date - timedelta(days=1)
    
    prev_params = params.copy()
    prev_params["from_date"] = prev_from_date
    prev_params["to_date"] = prev_to_date
    
    prev_total_query = """
        SELECT COALESCE(SUM(amount_rub), 0) as total_amount
        FROM variable_expenses
        WHERE expense_date >= :from_date AND expense_date <= :to_date
    """
    if location_id is not None:
        prev_total_query += " AND location_id = :location_id"
    
    prev_total_result = db.execute(text(prev_total_query), prev_params).fetchone()
    prev_total = float(prev_total_result[0] or 0) if prev_total_result else 0.0
    
    current_total = sum(item["total_amount"] for item in daily_data)
    trend_pct = ((current_total - prev_total) / prev_total * 100) if prev_total > 0 else 0.0
    
    return {
        "period": {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat()
        },
        "daily_data": daily_data,
        "by_category": category_data,
        "summary": {
            "total_amount": current_total,
            "total_count": sum(item["expense_count"] for item in daily_data),
            "avg_daily": current_total / period_days if period_days > 0 else 0.0,
            "prev_period_total": prev_total,
            "trend_pct": round(trend_pct, 2)
        }
    }


@router.get("/categories")
async def get_expenses_categories(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    location_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get expense categories directory with statistics.
    Returns all categories with aggregated stats.
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can view expense categories"
        )
    
    # Default period (all time if not specified)
    params = {}
    where_clause = "1=1"
    
    if from_date:
        where_clause += " AND expense_date >= :from_date"
        params["from_date"] = from_date
    if to_date:
        where_clause += " AND expense_date <= :to_date"
        params["to_date"] = to_date
    if location_id is not None:
        where_clause += " AND location_id = :location_id"
        params["location_id"] = location_id
    
    query = text(f"""
        SELECT
            category,
            COUNT(*) as expense_count,
            SUM(amount_rub) as total_amount,
            AVG(amount_rub) as avg_amount,
            MIN(amount_rub) as min_amount,
            MAX(amount_rub) as max_amount,
            MIN(expense_date) as first_expense_date,
            MAX(expense_date) as last_expense_date
        FROM variable_expenses
        WHERE {where_clause}
        GROUP BY category
        ORDER BY SUM(amount_rub) DESC
    """)
    
    results = db.execute(query, params).fetchall()
    
    categories = [
        {
            "category": row[0],
            "expense_count": int(row[1] or 0),
            "total_amount": float(row[2] or 0),
            "avg_amount": float(row[3] or 0),
            "min_amount": float(row[4] or 0),
            "max_amount": float(row[5] or 0),
            "first_expense_date": row[6].isoformat() if row[6] else None,
            "last_expense_date": row[7].isoformat() if row[7] else None
        }
        for row in results
    ]
    
    # Calculate total for percentage calculation
    total_all = sum(cat["total_amount"] for cat in categories)
    
    # Add percentage for each category
    for cat in categories:
        cat["percentage"] = round((cat["total_amount"] / total_all * 100) if total_all > 0 else 0.0, 2)
    
    return {
        "categories": categories,
        "total_categories": len(categories),
        "total_amount": total_all
    }
