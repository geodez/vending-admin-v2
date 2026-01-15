"""
API endpoints for Vendista synchronization.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
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
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger synchronization of transactions from Vendista DEFEN API.
    
    This fetches all transactions and inserts them into vendista_tx_raw table.
    Only users with owner role can trigger sync.
    
    Query parameters:
    - from_date: Optional start date filter (ISO format)
    - to_date: Optional end date filter (ISO format)
    """
    # Check if user has permission (only owners can sync)
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can trigger sync operations"
        )

    started_at = datetime.utcnow()
    logger.info(f"User {current_user.telegram_user_id} triggered full sync")

    try:
        result = await sync_service.sync_all_from_vendista(
            db=db,
            from_date=from_date,
            to_date=to_date
        )

        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()

        return {
            "ok": result.success,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": duration,
            "transactions_synced": result.transactions_synced,
            "message": result.error_message or "Sync completed successfully"
        }

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )
