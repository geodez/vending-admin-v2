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
from app.crud import vendista as crud_vendista
from app.schemas.vendista import VendistaTerminalResponse
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
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(20, ge=1, le=100, description="Number of runs to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get sync run history with optional date filtering.
    
    Returns recent sync runs with stats and status.
    
    Parameters:
    - date_from: Optional start date (YYYY-MM-DD) to filter runs
    - date_to: Optional end date (YYYY-MM-DD) to filter runs
    - limit: Max number of runs (default 20, max 100)
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can view sync history"
        )
    
    # Parse and validate dates
    where_conditions = []
    params = {"limit": limit}
    
    if date_from:
        try:
            parsed_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            where_conditions.append("started_at >= :date_from")
            params["date_from"] = parsed_date
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date_from format: {date_from}. Use YYYY-MM-DD"
            )
    
    if date_to:
        try:
            parsed_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            where_conditions.append("started_at < :date_to + interval '1 day'")
            params["date_to"] = parsed_date
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date_to format: {date_to}. Use YYYY-MM-DD"
            )
    
    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    query = text(f"""
        SELECT
            id, started_at, completed_at, period_start, period_end,
            fetched, inserted, skipped_duplicates, expected_total,
            pages_fetched, items_per_page, last_page, ok, message
        FROM sync_runs
        {where_clause}
        ORDER BY started_at DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, params)
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


@router.get("/terminals", response_model=List[VendistaTerminalResponse])
async def get_vendista_terminals(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(1000, ge=1, le=10000, description="Limit records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of Vendista terminals from vendista_terminals table.
    
    Returns terminals with id, title, comment, and is_active status.
    """
    terminals = crud_vendista.get_terminals(db, skip=skip, limit=limit, is_active=is_active)
    return terminals


@router.post("/runs/{run_id}/rerun")
async def rerun_sync(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Re-run a previous sync operation using the same parameters.
    
    Fetches the original run's parameters (period_start, period_end, items_per_page, order_desc)
    and re-executes the sync.
    
    Owner-only access.
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can rerun sync operations"
        )
    
    # Get original sync run parameters
    fetch_query = text("""
        SELECT period_start, period_end, items_per_page
        FROM sync_runs
        WHERE id = :run_id
    """)
    
    result = db.execute(fetch_query, {"run_id": run_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sync run with id {run_id} not found"
        )
    
    period_start = row[0]
    period_end = row[1]
    items_per_page = row[2] or 50
    
    if not period_start or not period_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Original sync run missing period_start or period_end"
        )
    
    # Re-run sync with original parameters
    logger.info(
        "User %s triggered rerun of sync run %d (period_start=%s, period_end=%s, items_per_page=%d)",
        current_user.telegram_user_id,
        run_id,
        period_start,
        period_end,
        items_per_page
    )
    
    started_at = datetime.utcnow()
    
    try:
        result = await sync_service.sync_all_from_vendista(
            db=db,
            period_start=period_start,
            period_end=period_end,
            items_per_page=items_per_page,
            order_desc=True
        )
        
        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()
        
        # Record rerun in database
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
                "message": result.error_message or "Rerun completed successfully"
            })
            db.commit()
        except Exception as record_error:
            logger.warning(f"Failed to record rerun: {record_error}")
        
        return {
            "ok": result.success,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": duration,
            "fetched": result.fetched,
            "inserted": result.inserted,
            "skipped_duplicates": result.skipped_duplicates,
            "expected_total": result.expected_total,
            "items_per_page": items_per_page,
            "pages_fetched": result.pages_fetched,
            "last_page": result.last_page,
            "message": result.error_message or "Rerun completed successfully"
        }
    
    except Exception as e:
        logger.error(f"Rerun failed: {e}")
        
        # Try to record failed rerun
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
                "message": f"Rerun failed: {str(e)}"
            })
            db.commit()
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rerun failed: {str(e)}"
        )
