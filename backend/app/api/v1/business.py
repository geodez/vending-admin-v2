"""
API endpoints for business entities (locations, products, ingredients, drinks, recipes).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.business import *
from pydantic import BaseModel
from decimal import Decimal
from app.crud import business as crud

router = APIRouter()


# ============================================================================
# Locations
# ============================================================================

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
    location = crud.get_location(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.put("/locations/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: int,
    location_update: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update location."""
    location = crud.update_location(db, location_id, location_update)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


# ============================================================================
# Products
# ============================================================================

@router.get("/products", response_model=List[ProductResponse])
def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of products."""
    return crud.get_products(db, skip=skip, limit=limit)


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new product."""
    return crud.create_product(db, product)


# ============================================================================
# Ingredients
# ============================================================================

@router.get("/ingredients", response_model=List[IngredientResponse])
def list_ingredients(
    skip: int = 0,
    limit: int = 1000,  # Увеличен лимит, чтобы вернуть все ингредиенты
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of ingredients."""
    return crud.get_ingredients(db, skip=skip, limit=limit)


@router.post("/ingredients", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
def create_ingredient(
    ingredient: IngredientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new ingredient."""
    return crud.create_ingredient(db, ingredient)


class BulkUpdateRequest(BaseModel):
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


@router.put("/ingredients/bulk/update", response_model=dict)
@router.put("/ingredients/bulk-update", response_model=dict)  # Старый путь для обратной совместимости
def bulk_update_ingredients(
    request: BulkUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk update multiple ingredients with the same values."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if not request.ingredient_codes:
            raise HTTPException(status_code=400, detail="No ingredient codes provided")
        
        logger.info(f"Bulk update request: {len(request.ingredient_codes)} codes: {request.ingredient_codes}")
        
        # Создаем IngredientUpdate из запроса (только не-None значения)
        # Используем model_dump с exclude_unset=True, чтобы не включать поля, которые не были установлены
        ingredient_update = IngredientUpdate(
            expense_kind=request.expense_kind,
            is_active=request.is_active,
            ingredient_group=request.ingredient_group,
            brand_name=request.brand_name,
            unit=request.unit,
            cost_per_unit_rub=request.cost_per_unit_rub,
            default_load_qty=request.default_load_qty,
            alert_threshold=request.alert_threshold,
            alert_days_threshold=request.alert_days_threshold,
            display_name_ru=request.display_name_ru,
            unit_ru=request.unit_ru,
            sort_order=request.sort_order,
        )
        
        # Проверяем, что есть хотя бы одно поле для обновления
        update_dict = ingredient_update.model_dump(exclude_unset=True, exclude_none=True)
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update provided")
        
        updated_count = 0
        errors = []
        
        for code in request.ingredient_codes:
            try:
                # Проверяем, существует ли ингредиент
                existing = crud.get_ingredient(db, code)
                if not existing:
                    logger.warning(f"Ingredient not found: {code}")
                    errors.append(f"Ingredient {code} not found")
                    continue
                
                ingredient = crud.update_ingredient(db, code, ingredient_update)
                if ingredient:
                    updated_count += 1
                    logger.info(f"Updated ingredient: {code}")
                else:
                    logger.warning(f"Failed to update ingredient: {code}")
                    errors.append(f"Ingredient {code} not found")
            except Exception as e:
                logger.error(f"Error updating {code}: {str(e)}", exc_info=True)
                errors.append(f"Error updating {code}: {str(e)}")
        
        db.commit()
        
        logger.info(f"Bulk update completed: {updated_count}/{len(request.ingredient_codes)} updated")
        
        return {
            "updated": updated_count,
            "total": len(request.ingredient_codes),
            "errors": errors if errors else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in bulk_update_ingredients: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/ingredients/{ingredient_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingredient(
    ingredient_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete ingredient."""
    try:
        deleted = crud.delete_ingredient(db, ingredient_code)
        if not deleted:
            raise HTTPException(status_code=404, detail="Ingredient not found")
    except ValueError as e:
        # Ингредиент используется в рецептах
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ingredients/{ingredient_code}", response_model=IngredientResponse)
def get_ingredient(
    ingredient_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ingredient by code."""
    ingredient = crud.get_ingredient(db, ingredient_code)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return ingredient


@router.put("/ingredients/{ingredient_code}", response_model=IngredientResponse)
def update_ingredient(
    ingredient_code: str,
    ingredient_update: IngredientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update ingredient."""
    ingredient = crud.update_ingredient(db, ingredient_code, ingredient_update)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return ingredient


# ============================================================================
# Drinks (Recipes)
# ============================================================================

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
    return crud.create_drink(db, drink)


@router.get("/drinks/{drink_id}", response_model=DrinkResponse)
def get_drink(
    drink_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get drink by ID."""
    drink = crud.get_drink(db, drink_id)
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found")
    return drink


@router.put("/drinks/{drink_id}", response_model=DrinkResponse)
def update_drink(
    drink_id: int,
    drink_update: DrinkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update drink and its recipe."""
    drink = crud.update_drink(db, drink_id, drink_update)
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found")
    return drink


# ============================================================================
# Ingredient Loads (Stock Management)
# ============================================================================

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
    """Get list of ingredient loads."""
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
    return crud.create_ingredient_load(db, load, user_id=current_user.id)


# ============================================================================
# Variable Expenses
# ============================================================================

@router.get("/expenses", response_model=List[VariableExpenseResponse])
def list_expenses(
    location_id: Optional[int] = None,
    category: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of variable expenses."""
    return crud.get_variable_expenses(
        db,
        location_id=location_id,
        category=category,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit
    )


@router.post("/expenses", response_model=VariableExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: VariableExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create variable expense."""
    return crud.create_variable_expense(db, expense, user_id=current_user.id)
