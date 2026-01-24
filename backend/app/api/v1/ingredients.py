"""
API endpoints for ingredient management.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.business import IngredientResponse, IngredientCreate, IngredientUpdate
from app.crud import business as crud
from app.services.ingredient_service import IngredientService
from app.api.middleware.validation import ValidationMiddleware

router = APIRouter()


class BulkUpdateRequest(BaseModel):
    """Request model for bulk ingredient updates."""
    ingredient_codes: List[str]
    expense_kind: Optional[str] = None
    is_active: Optional[bool] = None
    ingredient_group: Optional[str] = None
    brand_name: Optional[str] = None
    unit: Optional[str] = None
    cost_per_unit_rub: Optional[Decimal] = None
    default_load_qty: Optional[Decimal] = None
    alert_threshold: Optional[Decimal] = None
    alert_days_threshold: Optional[int] = None
    display_name_ru: Optional[str] = None
    unit_ru: Optional[str] = None
    sort_order: Optional[int] = None


@router.get("/ingredients", response_model=List[IngredientResponse])
def list_ingredients(
    skip: int = 0,
    limit: int = 1000,  # Увеличен лимит для получения всех ингредиентов
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of ingredients."""
    service = IngredientService(db)
    return service.get_ingredients_paginated(skip=skip, limit=limit)


@router.post("/ingredients", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
def create_ingredient(
    ingredient: IngredientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new ingredient."""
    service = IngredientService(db)
    service.validate_ingredient_data(ingredient.model_dump())
    return crud.create_ingredient(db, ingredient)


@router.put("/ingredients/bulk/update", response_model=dict)
@router.put("/ingredients/bulk-update", response_model=dict)  # Backward compatibility
def bulk_update_ingredients(
    request: BulkUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk update multiple ingredients with the same values.

    This endpoint allows updating multiple ingredients at once with shared values,
    which is useful for mass operations like changing expense categories or
    updating costs for multiple items.
    """
    service = IngredientService(db)

    # Extract update fields from request (exclude ingredient_codes)
    update_data = request.model_dump(exclude={'ingredient_codes'}, exclude_none=True)

    return ValidationMiddleware.handle_db_operation(
        lambda: service.bulk_update_ingredients(request.ingredient_codes, update_data),
        error_msg="Bulk ingredient update failed"
    )


@router.delete("/ingredients/{ingredient_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingredient(
    ingredient_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete ingredient with dependency checks."""
    service = IngredientService(db)
    service.delete_ingredient_safe(ingredient_code)


@router.get("/ingredients/{ingredient_code}", response_model=IngredientResponse)
def get_ingredient(
    ingredient_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ingredient by code."""
    return ValidationMiddleware.validate_entity_exists(
        crud.get_ingredient, ingredient_code, "Ingredient", db
    )


@router.put("/ingredients/{ingredient_code}", response_model=IngredientResponse)
def update_ingredient(
    ingredient_code: str,
    ingredient_update: IngredientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update ingredient."""
    ValidationMiddleware.validate_entity_exists(
        crud.get_ingredient, ingredient_code, "Ingredient", db
    )

    service = IngredientService(db)
    service.validate_ingredient_data({
        'ingredient_code': ingredient_code,
        **ingredient_update.model_dump(exclude_unset=True)
    })

    return crud.update_ingredient(db, ingredient_code, ingredient_update)