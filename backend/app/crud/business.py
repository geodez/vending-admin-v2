"""
CRUD operations for business entities.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.models.business import (
    Location, Product, Ingredient, Drink, DrinkItem,
    ButtonMatrix, ButtonMatrixItem, TerminalMatrixMap,
    VendistaTxRaw
)
from app.models.inventory import IngredientLoad, VariableExpense
from app.schemas.business import *
from sqlalchemy import text


# ============================================================================
# Location CRUD
# ============================================================================

def get_location(db: Session, location_id: int) -> Optional[Location]:
    return db.query(Location).filter(Location.id == location_id).first()


def get_locations(db: Session, skip: int = 0, limit: int = 100) -> List[Location]:
    return db.query(Location).offset(skip).limit(limit).all()


def create_location(db: Session, location: LocationCreate) -> Location:
    db_location = Location(**location.model_dump())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


def update_location(db: Session, location_id: int, location_update: LocationUpdate) -> Optional[Location]:
    db_location = get_location(db, location_id)
    if not db_location:
        return None
    for field, value in location_update.model_dump(exclude_unset=True).items():
        setattr(db_location, field, value)
    db.commit()
    db.refresh(db_location)
    return db_location


# ============================================================================
# Product CRUD
# ============================================================================

def get_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.product_external_id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    return db.query(Product).offset(skip).limit(limit).all()


def create_product(db: Session, product: ProductCreate) -> Product:
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


# ============================================================================
# Ingredient CRUD
# ============================================================================

def get_ingredient(db: Session, ingredient_code: str) -> Optional[Ingredient]:
    return db.query(Ingredient).filter(Ingredient.ingredient_code == ingredient_code).first()


def get_ingredients(db: Session, skip: int = 0, limit: int = 100) -> List[Ingredient]:
    return db.query(Ingredient).order_by(Ingredient.sort_order.asc().nulls_last(), Ingredient.ingredient_code.asc()).offset(skip).limit(limit).all()


def create_ingredient(db: Session, ingredient: IngredientCreate) -> Ingredient:
    db_ingredient = Ingredient(**ingredient.model_dump())
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient


def update_ingredient(db: Session, ingredient_code: str, ingredient_update: IngredientUpdate) -> Optional[Ingredient]:
    db_ingredient = get_ingredient(db, ingredient_code)
    if not db_ingredient:
        return None
    # Обновляем только те поля, которые явно установлены (не None и не пропущены)
    update_dict = ingredient_update.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_dict.items():
        setattr(db_ingredient, field, value)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient


def delete_ingredient(db: Session, ingredient_code: str) -> bool:
    """Delete ingredient. Returns True if deleted, False if not found."""
    db_ingredient = get_ingredient(db, ingredient_code)
    if not db_ingredient:
        return False
    
    # Проверяем, используется ли ингредиент в рецептах
    from app.models.business import DrinkItem
    usage_count = db.query(DrinkItem).filter(DrinkItem.ingredient_code == ingredient_code).count()
    if usage_count > 0:
        raise ValueError(f"Cannot delete ingredient: it is used in {usage_count} recipe(s)")
    
    db.delete(db_ingredient)
    db.commit()
    return True


# ============================================================================
# Drink CRUD
# ============================================================================

def get_drink(db: Session, drink_id: int) -> Optional[Drink]:
    return db.query(Drink).filter(Drink.id == drink_id).first()


def get_drinks(db: Session, skip: int = 0, limit: int = 100) -> List[Drink]:
    return db.query(Drink).offset(skip).limit(limit).all()


def create_drink(db: Session, drink: DrinkCreate) -> Drink:
    # Create drink
    db_drink = Drink(name=drink.name, is_active=drink.is_active)
    db.add(db_drink)
    db.commit()
    db.refresh(db_drink)
    
    # Create drink items
    for item in drink.items:
        db_item = DrinkItem(
            drink_id=db_drink.id,
            **item.model_dump()
        )
        db.add(db_item)
    db.commit()
    db.refresh(db_drink)
    return db_drink


def update_drink(db: Session, drink_id: int, drink_update: DrinkUpdate) -> Optional[Drink]:
    db_drink = get_drink(db, drink_id)
    if not db_drink:
        return None
    
    # Update basic fields
    if drink_update.name is not None:
        db_drink.name = drink_update.name
    if drink_update.is_active is not None:
        db_drink.is_active = drink_update.is_active
    
    # Update items if provided
    if drink_update.items is not None:
        # Delete existing items
        db.query(DrinkItem).filter(DrinkItem.drink_id == drink_id).delete()
        # Create new items
        for item in drink_update.items:
            db_item = DrinkItem(drink_id=drink_id, **item.model_dump())
            db.add(db_item)
    
    db.commit()
    db.refresh(db_drink)
    return db_drink


# ============================================================================
# Machine Matrix CRUD
# ============================================================================

# ============================================================================
# Button Matrix CRUD (New Template System)
# ============================================================================

def get_button_matrix(db: Session, matrix_id: int) -> Optional[ButtonMatrix]:
    return db.query(ButtonMatrix).filter(ButtonMatrix.id == matrix_id).first()


def get_button_matrices(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[ButtonMatrix]:
    query = db.query(ButtonMatrix)
    if is_active is not None:
        query = query.filter(ButtonMatrix.is_active == is_active)
    return query.order_by(ButtonMatrix.name).offset(skip).limit(limit).all()


def create_button_matrix(db: Session, matrix: ButtonMatrixCreate) -> ButtonMatrix:
    db_matrix = ButtonMatrix(**matrix.model_dump())
    db.add(db_matrix)
    db.commit()
    db.refresh(db_matrix)
    return db_matrix


def update_button_matrix(
    db: Session, 
    matrix_id: int, 
    matrix_update: ButtonMatrixUpdate
) -> Optional[ButtonMatrix]:
    db_matrix = get_button_matrix(db, matrix_id)
    if db_matrix is None:
        return None
    
    update_data = matrix_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_matrix, field, value)
    
    db.commit()
    db.refresh(db_matrix)
    return db_matrix


def delete_button_matrix(db: Session, matrix_id: int) -> bool:
    db_matrix = get_button_matrix(db, matrix_id)
    if db_matrix is None:
        return False
    
    db.delete(db_matrix)
    db.commit()
    return True


def get_button_matrix_items(
    db: Session, 
    matrix_id: int
) -> List[ButtonMatrixItem]:
    return db.query(ButtonMatrixItem).filter(
        ButtonMatrixItem.matrix_id == matrix_id
    ).order_by(ButtonMatrixItem.machine_item_id).all()


def create_button_matrix_item(
    db: Session, 
    matrix_id: int, 
    item: ButtonMatrixItemCreate
) -> ButtonMatrixItem:
    db_item = ButtonMatrixItem(matrix_id=matrix_id, **item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_button_matrix_item(
    db: Session,
    matrix_id: int,
    machine_item_id: int,
    item_update: ButtonMatrixItemUpdate
) -> Optional[ButtonMatrixItem]:
    db_item = db.query(ButtonMatrixItem).filter(
        ButtonMatrixItem.matrix_id == matrix_id,
        ButtonMatrixItem.machine_item_id == machine_item_id
    ).first()
    
    if db_item is None:
        return None
    
    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_button_matrix_item(
    db: Session, 
    matrix_id: int, 
    machine_item_id: int
) -> bool:
    db_item = db.query(ButtonMatrixItem).filter(
        ButtonMatrixItem.matrix_id == matrix_id,
        ButtonMatrixItem.machine_item_id == machine_item_id
    ).first()
    
    if db_item is None:
        return False
    
    db.delete(db_item)
    db.commit()
    return True


def get_terminal_matrix_maps(
    db: Session,
    matrix_id: Optional[int] = None,
    term_id: Optional[int] = None
) -> List[TerminalMatrixMap]:
    query = db.query(TerminalMatrixMap)
    if matrix_id:
        query = query.filter(TerminalMatrixMap.matrix_id == matrix_id)
    if term_id:
        query = query.filter(TerminalMatrixMap.vendista_term_id == term_id)
    return query.all()


def assign_terminals_to_matrix(
    db: Session,
    matrix_id: int,
    term_ids: List[int]
) -> List[TerminalMatrixMap]:
    # Remove existing assignments for this matrix
    db.query(TerminalMatrixMap).filter(
        TerminalMatrixMap.matrix_id == matrix_id
    ).delete()
    
    # Create new assignments
    assignments = []
    for term_id in term_ids:
        assignment = TerminalMatrixMap(
            matrix_id=matrix_id,
            vendista_term_id=term_id,
            is_active=True
        )
        db.add(assignment)
        assignments.append(assignment)
    
    db.commit()
    for assignment in assignments:
        db.refresh(assignment)
    
    return assignments


def remove_terminal_from_matrix(
    db: Session,
    matrix_id: int,
    term_id: int
) -> bool:
    assignment = db.query(TerminalMatrixMap).filter(
        TerminalMatrixMap.matrix_id == matrix_id,
        TerminalMatrixMap.vendista_term_id == term_id
    ).first()
    
    if assignment is None:
        return False
    
    db.delete(assignment)
    db.commit()
    return True


def get_unmapped_transactions(db: Session) -> List[dict]:
    """
    Get list of unique (term_id, machine_item_id) that are present in transactions
    but missing from the assigned button matrix.
    """
    query = text("""
        SELECT DISTINCT
            t.term_id,
            (t.payload->'machine_item'->0->>'machine_item_id')::int as machine_item_id,
            vt.comment as term_name,
            tmm.matrix_id
        FROM vendista_tx_raw t
        JOIN vendista_terminals vt ON vt.id = t.term_id
        LEFT JOIN terminal_matrix_map tmm 
            ON tmm.vendista_term_id = t.term_id 
            AND tmm.is_active = true
        LEFT JOIN button_matrix_items bmi 
            ON bmi.matrix_id = tmm.matrix_id 
            AND bmi.machine_item_id = (t.payload->'machine_item'->0->>'machine_item_id')::int
        WHERE 
            (t.payload->'machine_item'->0->>'machine_item_id') IS NOT NULL
            AND bmi.id IS NULL
        ORDER BY t.term_id, machine_item_id
    """)
    
    results = db.execute(query).fetchall()
    
    unmapped = []
    for row in results:
        unmapped.append({
            "term_id": row[0],
            "machine_item_id": row[1],
            "term_name": row[2],
            "matrix_id": row[3]
        })
    
    return unmapped


# ============================================================================
# Ingredient Load CRUD
# ============================================================================

def get_ingredient_load(db: Session, load_id: int) -> Optional[IngredientLoad]:
    return db.query(IngredientLoad).filter(IngredientLoad.id == load_id).first()


def get_ingredient_loads(
    db: Session,
    ingredient_code: Optional[str] = None,
    location_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> List[IngredientLoad]:
    query = db.query(IngredientLoad)
    if ingredient_code:
        query = query.filter(IngredientLoad.ingredient_code == ingredient_code)
    if location_id:
        query = query.filter(IngredientLoad.location_id == location_id)
    if from_date:
        query = query.filter(IngredientLoad.load_date >= from_date)
    if to_date:
        query = query.filter(IngredientLoad.load_date <= to_date)
    return query.order_by(IngredientLoad.load_date.desc()).offset(skip).limit(limit).all()


def create_ingredient_load(db: Session, load: IngredientLoadCreate, user_id: Optional[int] = None) -> IngredientLoad:
    db_load = IngredientLoad(**load.model_dump(), created_by_user_id=user_id)
    db.add(db_load)
    db.commit()
    db.refresh(db_load)
    return db_load


# ============================================================================
# Variable Expense CRUD
# ============================================================================

def get_variable_expense(db: Session, expense_id: int) -> Optional[VariableExpense]:
    return db.query(VariableExpense).filter(VariableExpense.id == expense_id).first()


def get_variable_expenses(
    db: Session,
    location_id: Optional[int] = None,
    category: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> List[VariableExpense]:
    query = db.query(VariableExpense)
    if location_id:
        query = query.filter(VariableExpense.location_id == location_id)
    if category:
        query = query.filter(VariableExpense.category == category)
    if from_date:
        query = query.filter(VariableExpense.expense_date >= from_date)
    if to_date:
        query = query.filter(VariableExpense.expense_date <= to_date)
    return query.order_by(VariableExpense.expense_date.desc()).offset(skip).limit(limit).all()


def create_variable_expense(db: Session, expense: VariableExpenseCreate, user_id: Optional[int] = None) -> VariableExpense:
    db_expense = VariableExpense(**expense.model_dump(), created_by_user_id=user_id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense
