"""
API endpoints for Vendista synchronization.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.vendista import (
    SyncRequest,
    SyncResponse,
    SyncResult,
    SyncStateResponse,
    VendistaTerminalResponse,
    VendistaTxRawResponse
)
from app.services.vendista_sync import sync_service
from app.crud import vendista as crud_vendista
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sync", response_model=SyncResponse)
async def trigger_sync(
    sync_request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger manual synchronization of Vendista transactions.
    
    This endpoint starts a sync job that runs in the background.
    Only users with owner role can trigger sync.
    """
    # Check if user has permission (only owners can sync)
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can trigger sync operations"
        )

    started_at = datetime.utcnow()
    
    logger.info(
        f"User {current_user.telegram_user_id} triggered sync: "
        f"term_ids={sync_request.term_ids}, force={sync_request.force}"
    )

    try:
        # Run sync synchronously (we can move to background if needed)
        results = await sync_service.sync_all_terminals(
            db=db,
            term_ids=sync_request.term_ids,
            from_date=sync_request.from_date,
            to_date=sync_request.to_date,
            force=sync_request.force
        )

        completed_at = datetime.utcnow()
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)

        return SyncResponse(
            started_at=started_at,
            completed_at=completed_at,
            total_terminals=len(results),
            successful=successful,
            failed=failed,
            results=results
        )

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/sync/status", response_model=List[SyncStateResponse])
def get_sync_status(
    term_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get synchronization status for terminals.
    
    Returns sync state for all terminals or a specific terminal.
    """
    sync_states = sync_service.get_sync_status(db, term_id=term_id)
    return sync_states


@router.get("/terminals", response_model=List[VendistaTerminalResponse])
def get_terminals(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of Vendista terminals.
    """
    terminals = crud_vendista.get_terminals(db, skip=skip, limit=limit, is_active=is_active)
    return terminals


@router.get("/terminals/{term_id}", response_model=VendistaTerminalResponse)
def get_terminal(
    term_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific terminal by ID.
    """
    terminal = crud_vendista.get_terminal(db, term_id=term_id)
    if terminal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Terminal {term_id} not found"
        )
    return terminal


@router.get("/transactions", response_model=List[VendistaTxRawResponse])
def get_transactions(
    term_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of transactions with filters.
    
    Query parameters:
    - term_id: Filter by terminal ID
    - from_date: Filter transactions from this date
    - to_date: Filter transactions until this date
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return (max: 1000)
    """
    if limit > 1000:
        limit = 1000

    transactions = crud_vendista.get_transactions(
        db,
        term_id=term_id,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit
    )
    return transactions


@router.get("/transactions/count")
def count_transactions(
    term_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Count transactions with filters.
    """
    count = crud_vendista.count_transactions(
        db,
        term_id=term_id,
        from_date=from_date,
        to_date=to_date
    )
    return {"count": count}
