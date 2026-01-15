"""
API endpoints for Vendista synchronization.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )
