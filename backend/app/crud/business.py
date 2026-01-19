"""
CRUD operations for business entities.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.models.business import Location, Product, Ingredient, Drink, DrinkItem, MachineMatrix
from app.models.inventory import IngredientLoad, VariableExpense
from app.schemas.business import *


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

def get_machine_matrix(db: Session, term_id: int, machine_item_id: int) -> Optional[MachineMatrix]:
    return db.query(MachineMatrix).filter(
        MachineMatrix.vendista_term_id == term_id,
        MachineMatrix.machine_item_id == machine_item_id
    ).first()


def get_machine_matrices(db: Session, term_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[MachineMatrix]:
    query = db.query(MachineMatrix)
    if term_id:
        query = query.filter(MachineMatrix.vendista_term_id == term_id)
    return query.offset(skip).limit(limit).all()


def create_machine_matrix(db: Session, matrix: MachineMatrixCreate) -> MachineMatrix:
    db_matrix = MachineMatrix(**matrix.model_dump())
    db.add(db_matrix)
    db.commit()
    db.refresh(db_matrix)
    return db_matrix


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
