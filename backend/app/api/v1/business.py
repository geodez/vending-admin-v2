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
    limit: int = 100,
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
# Machine Matrix (Button Mappings)
# ============================================================================

@router.get("/machine-matrix", response_model=List[MachineMatrixResponse])
def list_machine_matrices(
    term_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of button mappings."""
    return crud.get_machine_matrices(db, term_id=term_id, skip=skip, limit=limit)


@router.post("/machine-matrix", response_model=MachineMatrixResponse, status_code=status.HTTP_201_CREATED)
def create_machine_matrix(
    matrix: MachineMatrixCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create button mapping."""
    return crud.create_machine_matrix(db, matrix)


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
