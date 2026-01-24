"""
API endpoints for location management.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.business import LocationResponse, LocationCreate, LocationUpdate
from app.crud import business as crud
from app.api.middleware.validation import ValidationMiddleware

router = APIRouter()


@router.get("/locations", response_model=List[LocationResponse])
def list_locations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of locations."""
    return crud.get_locations(db, skip=skip, limit=limit)


@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    location: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new location."""
    return crud.create_location(db, location)


@router.get("/locations/{location_id}", response_model=LocationResponse)
def get_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get location by ID."""
    return ValidationMiddleware.validate_entity_exists(
        crud.get_location, location_id, "Location", db
    )


@router.put("/locations/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: int,
    location_update: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update location."""
    ValidationMiddleware.validate_entity_exists(
        crud.get_location, location_id, "Location", db
    )
    return crud.update_location(db, location_id, location_update)