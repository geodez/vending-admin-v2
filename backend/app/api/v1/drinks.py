"""
API endpoints for drink/recipe management.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.business import DrinkResponse, DrinkCreate, DrinkUpdate
from app.crud import business as crud
from app.services.recipe_service import RecipeService
from app.api.middleware.validation import ValidationMiddleware

router = APIRouter()


@router.get("/drinks", response_model=List[DrinkResponse])
def list_drinks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of drinks."""
    return crud.get_drinks(db, skip=skip, limit=limit)


@router.post("/drinks", response_model=DrinkResponse, status_code=status.HTTP_201_CREATED)
def create_drink(
    drink: DrinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new drink with recipe."""
    service = RecipeService(db)
    return service.create_recipe_with_validation(drink)


@router.get("/drinks/{drink_id}", response_model=DrinkResponse)
def get_drink(
    drink_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get drink by ID."""
    return ValidationMiddleware.validate_entity_exists(
        crud.get_drink, drink_id, "Drink", db
    )


@router.put("/drinks/{drink_id}", response_model=DrinkResponse)
def update_drink(
    drink_id: int,
    drink_update: DrinkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update drink and its recipe."""
    service = RecipeService(db)
    return service.update_recipe_with_validation(drink_id, drink_update)


@router.get("/drinks/{drink_id}/cost", response_model=dict)
def get_drink_cost(
    drink_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate and return recipe cost breakdown."""
    service = RecipeService(db)
    return service.calculate_recipe_cost(drink_id)