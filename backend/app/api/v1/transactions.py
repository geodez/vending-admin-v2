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
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    term_id: Optional[int] = Query(None, description="Filter by terminal ID"),
    sum_type: str = Query("positive", description="all|positive|non_positive"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page (max 200)"),
    order_desc: bool = Query(True, description="Order by tx_time DESC"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of transactions from vendista_tx_raw.
    
    Filters:
      - date_from/date_to: Period (YYYY-MM-DD format)
      - term_id: Optional terminal filter
      - sum_type: 'positive' (sum>0), 'non_positive' (sum<=0), 'all'
      - order_desc: Sort by tx_time DESC (default=true)
    
    Returns items with extracted fields from JSON payload.
    """
    # Parse dates
    if date_to is None:
        period_end = datetime.utcnow().date()
    else:
        try:
            period_end = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format (use YYYY-MM-DD)")
    
    if date_from is None:
        period_start = period_end.replace(day=1)
    else:
        try:
            period_start = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format (use YYYY-MM-DD)")
    
    # Validate sum_type
    if sum_type not in ("all", "positive", "non_positive"):
        raise HTTPException(status_code=400, detail="sum_type must be 'all', 'positive', or 'non_positive'")
    
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
        where_clauses.append("(payload->>'term_id')::int = :term_id")
        params["term_id"] = term_id
    
    # Apply sum_type filter
    if sum_type == "positive":
        where_clauses.append("(payload->>'sum')::numeric > 0")
    elif sum_type == "non_positive":
        where_clauses.append("(payload->>'sum')::numeric <= 0")
    # 'all' => no sum filter
    
    where_sql = " AND ".join(where_clauses)
    order_clause = "ORDER BY tx_time DESC" if order_desc else "ORDER BY tx_time ASC"
    
    # Count query
    count_query = text(f"""
        SELECT COUNT(*) FROM vendista_tx_raw
        WHERE {where_sql}
    """)
    
    total = db.execute(count_query, params).scalar_one()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    # Data query with pagination
    data_query = text(f"""
        SELECT
            id,
            (payload->>'term_id')::int as term_id,
            vendista_tx_id,
            tx_time,
            (payload->>'sum')::numeric as sum_kopecks,
            (payload->>'sum')::numeric / 100.0 as sum_rub,
            (payload->'machine_item'->0->>'machine_item_id')::int as machine_item_id,
            payload->>'terminal_comment' as terminal_comment,
            (payload->>'status')::text as status,
            payload
        FROM vendista_tx_raw
        WHERE {where_sql}
        {order_clause}
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
            "sum_kopecks": int(row[4]) if row[4] else 0,
            "sum_rub": float(row[5]) if row[5] else 0.0,
            "machine_item_id": row[6],
            "terminal_comment": row[7],
            "status": row[8],
            "raw_payload": row[9]
        })
    
    logger.info(f"Transactions: period={period_start}..{period_end}, sum_type={sum_type}, term_id={term_id}, total={total}")
    
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages
    }


@router.get("/export")
async def export_transactions(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    term_id: Optional[int] = Query(None, description="Filter by terminal ID"),
    sum_type: str = Query("positive", description="all|positive|non_positive"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export transactions as CSV (text/csv attachment).
    Same filters as GET /transactions endpoint.
    """
    from io import StringIO
    import csv
    from fastapi.responses import StreamingResponse
    
    # Parse dates
    if date_to is None:
        period_end = datetime.utcnow().date()
    else:
        try:
            period_end = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format (use YYYY-MM-DD)")
    
    if date_from is None:
        period_start = period_end.replace(day=1)
    else:
        try:
            period_start = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format (use YYYY-MM-DD)")
    
    # Validate sum_type
    if sum_type not in ("all", "positive", "non_positive"):
        raise HTTPException(status_code=400, detail="sum_type must be 'all', 'positive', or 'non_positive'")
    
    # Build WHERE clause (same as /get_transactions)
    where_clauses = [
        "tx_time >= :period_start",
        "tx_time < :period_end + interval '1 day'"
    ]
    params = {
        "period_start": period_start,
        "period_end": period_end,
    }
    
    if term_id is not None:
        where_clauses.append("(payload->>'term_id')::int = :term_id")
        params["term_id"] = term_id
    
    if sum_type == "positive":
        where_clauses.append("(payload->>'sum')::numeric > 0")
    elif sum_type == "non_positive":
        where_clauses.append("(payload->>'sum')::numeric <= 0")
    
    where_sql = " AND ".join(where_clauses)
    
    # Fetch all data (no pagination for export)
    data_query = text(f"""
        SELECT
            tx_time,
            (payload->>'term_id')::int as term_id,
            vendista_tx_id,
            (payload->>'sum')::numeric / 100.0 as sum_rub,
            (payload->>'sum')::numeric as sum_kopecks,
            (payload->'machine_item'->0->>'machine_item_id')::int as machine_item_id,
            payload->>'terminal_comment' as terminal_comment,
            (payload->>'status')::text as status
        FROM vendista_tx_raw
        WHERE {where_sql}
        ORDER BY tx_time DESC
    """)
    
    result = db.execute(data_query, params)
    rows = result.fetchall()
    
    # Create CSV
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["tx_time", "term_id", "vendista_tx_id", "sum_rub", "sum_kopecks", "machine_item_id", "terminal_comment", "status"]
    )
    writer.writeheader()
    
    for row in rows:
        writer.writerow({
            "tx_time": row[0].isoformat() if row[0] else "",
            "term_id": row[1] or "",
            "vendista_tx_id": row[2] or "",
            "sum_rub": f"{row[3]:.2f}" if row[3] else "",
            "sum_kopecks": int(row[4]) if row[4] else "",
            "machine_item_id": row[5] or "",
            "terminal_comment": row[6] or "",
            "status": row[7] or ""
        })
    
    csv_content = output.getvalue()
    csv_bytes = csv_content.encode('utf-8')
    
    # Log export
    export_count = len(rows)
    logger.info(f"CSV Export: period={period_start}..{period_end}, sum_type={sum_type}, term_id={term_id}, rows={export_count}")
    
    # Return as attachment
    filename = f"transactions_{period_start.strftime('%Y%m%d')}_{period_end.strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )
