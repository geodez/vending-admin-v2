"""
API endpoints for inventory management (ingredient loads, stock tracking).
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.business import IngredientLoadResponse, IngredientLoadCreate
from app.crud import business as crud
from app.services.expense_service import ExpenseService

router = APIRouter()


@router.get("/ingredient-loads", response_model=List[IngredientLoadResponse])
def list_ingredient_loads(
    ingredient_code: Optional[str] = None,
    location_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of ingredient loads with optional filtering."""
    return crud.get_ingredient_loads(
        db,
        ingredient_code=ingredient_code,
        location_id=location_id,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit
    )


@router.post("/ingredient-loads", response_model=IngredientLoadResponse, status_code=status.HTTP_201_CREATED)
def create_ingredient_load(
    load: IngredientLoadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create ingredient load."""
    service = ExpenseService(db)
    return service.create_ingredient_load_with_validation(load, current_user.id)


@router.get("/inventory/status", response_model=dict)
def get_inventory_status(
    ingredient_code: Optional[str] = None,
    location_id: Optional[int] = None,
    days_back: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get inventory status report.

    Shows total loaded quantities, load counts, and activity for specified period.
    """
    service = ExpenseService(db)
    return service.get_inventory_status_report(
        ingredient_code=ingredient_code,
        location_id=location_id,
        days_back=days_back
    )