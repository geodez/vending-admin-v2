"""
API endpoints for Terminals (aggregated stats from vendista_tx_raw).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, date
from typing import List, Optional
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_terminals(
    period_start: Optional[date] = Query(None, description="Start date (YYYY-MM-DD), default: first day of month"),
    period_end: Optional[date] = Query(None, description="End date (YYYY-MM-DD), default: today"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get terminals statistics aggregated from vendista_tx_raw.
    
    Returns list of terminals with tx_count, revenue, and last transaction time.
    Only counts transactions with sum > 0 (actual sales).
    """
    # Default period
    today = datetime.utcnow().date()
    if period_end is None:
        period_end = today
    if period_start is None:
        period_start = today.replace(day=1)
    
    # Build SQL query
    # We parse JSON payload to extract sum and count only positive transactions
    query = text("""
        SELECT
            t.term_id,
            COUNT(*) FILTER (WHERE (t.payload->>'sum')::numeric > 0) as tx_count,
            COALESCE(SUM((t.payload->>'sum')::numeric) FILTER (WHERE (t.payload->>'sum')::numeric > 0), 0) / 100.0 as revenue_gross,
            MAX(t.tx_time) FILTER (WHERE (t.payload->>'sum')::numeric > 0) as last_tx_time
        FROM vendista_tx_raw t
        LEFT JOIN vendista_terminals vt ON vt.id = t.term_id
        WHERE t.tx_time >= :period_start
          AND t.tx_time < :period_end + interval '1 day'
          AND vt.is_active IS DISTINCT FROM false
        GROUP BY t.term_id
        HAVING COUNT(*) FILTER (WHERE (t.payload->>'sum')::numeric > 0) > 0
        ORDER BY revenue_gross DESC
    """)
    
    result = db.execute(
        query,
        {"period_start": period_start, "period_end": period_end}
    )
    
    rows = result.fetchall()
    
    terminals = []
    for row in rows:
        terminals.append({
            "term_id": row[0],
            "tx_count": row[1],
            "revenue_gross": float(row[2]) if row[2] else 0.0,
            "last_tx_time": row[3].isoformat() if row[3] else None
        })
    
    return terminals
