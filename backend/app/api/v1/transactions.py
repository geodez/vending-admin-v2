"""
API endpoints for Transactions (detailed list from vendista_tx_raw).
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from datetime import datetime, date
from typing import List, Optional
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_transactions(
    period_start: Optional[date] = Query(None),
    period_end: Optional[date] = Query(None),
    term_id: Optional[int] = Query(None, description="Filter by terminal ID"),
    only_positive: bool = Query(True, description="Show only transactions with sum > 0"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page (max 200)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of transactions from vendista_tx_raw.
    
    Returns items with extracted fields from JSON payload.
    """
    # Default period
    today = datetime.utcnow().date()
    if period_end is None:
        period_end = today
    if period_start is None:
        period_start = today.replace(day=1)
    
    # Build WHERE clause
    where_clauses = [
        "tx_time >= :period_start",
        "tx_time < :period_end + interval '1 day'"
    ]
    params = {
        "period_start": period_start,
        "period_end": period_end,
        "limit": page_size,
        "offset": (page - 1) * page_size
    }
    
    if term_id is not None:
        where_clauses.append("term_id = :term_id")
        params["term_id"] = term_id
    
    if only_positive:
        where_clauses.append("(payload->>'sum')::numeric > 0")
    
    where_sql = " AND ".join(where_clauses)
    
    # Count query
    count_query = text(f"""
        SELECT COUNT(*) FROM vendista_tx_raw
        WHERE {where_sql}
    """)
    
    total = db.execute(count_query, params).scalar_one()
    
    # Data query with pagination
    data_query = text(f"""
        SELECT
            id,
            term_id,
            vendista_tx_id,
            tx_time,
            (payload->>'sum')::numeric / 100.0 as sum_rub,
            (payload->'machine_item'->0->>'machine_item_id')::int as machine_item_id,
            payload->>'terminal_comment' as terminal_comment,
            (payload->>'status')::int as status,
            payload
        FROM vendista_tx_raw
        WHERE {where_sql}
        ORDER BY tx_time DESC
        LIMIT :limit OFFSET :offset
    """)
    
    result = db.execute(data_query, params)
    rows = result.fetchall()
    
    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "term_id": row[1],
            "vendista_tx_id": row[2],
            "tx_time": row[3].isoformat() if row[3] else None,
            "sum_rub": float(row[4]) if row[4] else 0.0,
            "machine_item_id": row[5],
            "terminal_comment": row[6],
            "status": row[7],
            "location_id": None  # TODO: can be enriched from vw_tx_cogs if exists
        })
    
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total
    }
