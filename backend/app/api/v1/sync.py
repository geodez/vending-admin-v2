"""
API endpoints for Vendista synchronization.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, date
from typing import Optional, List
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.vendista_sync import sync_service
from app.services.vendista_client import vendista_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def check_sync_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check connection to Vendista API.
    
    Only users with owner role can check.
    """
    # Check if user has permission (only owners can access)
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can check sync health"
        )

    try:
        is_connected = await vendista_client.test_connection()
        
        if is_connected:
            return {
                "ok": True,
                "status": "Connected to Vendista API",
                "status_code": 200
            }
        else:
            return {
                "ok": False,
                "status": "Failed to connect to Vendista API",
                "status_code": 500
            }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "ok": False,
            "status": f"Error: {str(e)}",
            "status_code": 500
        }


@router.post("/sync")
async def trigger_sync(
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    items_per_page: int = 50,
    order_desc: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger synchronization of transactions from Vendista DEFEN API.
    
    This fetches all transactions and inserts them into vendista_tx_raw table.
    Only users with owner role can trigger sync.
    
    Query parameters:
    - period_start: Optional start date (YYYY-MM-DD), default = first day of current month (UTC)
    - period_end: Optional end date (YYYY-MM-DD), default = today (UTC)
    - items_per_page: Page size for Vendista API (default 50)
    - order_desc: OrderDesc flag for Vendista API (default True)
    """
    # Check if user has permission (only owners can sync)
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can trigger sync operations"
        )

    # Defaults for period
    today = datetime.utcnow().date()
    if period_end is None:
        period_end = today
    if period_start is None:
        period_start = today.replace(day=1)

    if period_end < period_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="period_end must be greater than or equal to period_start"
        )

    started_at = datetime.utcnow()
    logger.info(
        "User %s triggered full sync (period_start=%s, period_end=%s, items_per_page=%s, order_desc=%s)",
        current_user.telegram_user_id,
        period_start,
        period_end,
        items_per_page,
        order_desc,
    )

    try:
        result = await sync_service.sync_all_from_vendista(
            db=db,
            period_start=period_start,
            period_end=period_end,
            items_per_page=items_per_page,
            order_desc=order_desc,
        )

        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()

        # Record sync run in database
        try:
            record_query = text("""
                INSERT INTO sync_runs (
                    started_at, completed_at, period_start, period_end,
                    fetched, inserted, skipped_duplicates, expected_total,
                    pages_fetched, items_per_page, last_page, ok, message
                ) VALUES (
                    :started_at, :completed_at, :period_start, :period_end,
                    :fetched, :inserted, :skipped_duplicates, :expected_total,
                    :pages_fetched, :items_per_page, :last_page, :ok, :message
                )
            """)
            db.execute(record_query, {
                "started_at": started_at,
                "completed_at": completed_at,
                "period_start": period_start,
                "period_end": period_end,
                "fetched": result.fetched,
                "inserted": result.inserted,
                "skipped_duplicates": result.skipped_duplicates,
                "expected_total": result.expected_total,
                "pages_fetched": result.pages_fetched,
                "items_per_page": result.items_per_page,
                "last_page": result.last_page,
                "ok": result.success,
                "message": result.error_message or "Sync completed successfully"
            })
            db.commit()
        except Exception as record_error:
            logger.warning(f"Failed to record sync run: {record_error}")
            # Don't fail the whole request if recording fails

        return {
            "ok": result.success,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": duration,
            "fetched": result.fetched,
            "inserted": result.inserted,
            "skipped_duplicates": result.skipped_duplicates,
            "expected_total": result.expected_total,
            "items_per_page": result.items_per_page,
            "pages_fetched": result.pages_fetched,
            "last_page": result.last_page,
            "transactions_synced": result.transactions_synced,
            "message": result.error_message or "Sync completed successfully"
        }

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        
        # Try to record failed run
        try:
            completed_at = datetime.utcnow()
            record_query = text("""
                INSERT INTO sync_runs (
                    started_at, completed_at, period_start, period_end,
                    ok, message
                ) VALUES (
                    :started_at, :completed_at, :period_start, :period_end,
                    :ok, :message
                )
            """)
            db.execute(record_query, {
                "started_at": started_at,
                "completed_at": completed_at,
                "period_start": period_start,
                "period_end": period_end,
                "ok": False,
                "message": str(e)
            })
            db.commit()
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/runs")
async def get_sync_runs(
    limit: int = Query(20, ge=1, le=100, description="Number of runs to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get sync run history.
    
    Returns recent sync runs with stats and status.
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can view sync history"
        )
    
    query = text("""
        SELECT
            id, started_at, completed_at, period_start, period_end,
            fetched, inserted, skipped_duplicates, expected_total,
            pages_fetched, items_per_page, last_page, ok, message
        FROM sync_runs
        ORDER BY started_at DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {"limit": limit})
    rows = result.fetchall()
    
    runs = []
    for row in rows:
        runs.append({
            "id": row[0],
            "started_at": row[1].isoformat() if row[1] else None,
            "completed_at": row[2].isoformat() if row[2] else None,
            "period_start": row[3].isoformat() if row[3] else None,
            "period_end": row[4].isoformat() if row[4] else None,
            "fetched": row[5],
            "inserted": row[6],
            "skipped_duplicates": row[7],
            "expected_total": row[8],
            "pages_fetched": row[9],
            "items_per_page": row[10],
            "last_page": row[11],
            "ok": row[12],
            "message": row[13]
        })
    
    return runs
