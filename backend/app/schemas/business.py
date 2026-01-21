"""
Pydantic schemas for business entities.
"""
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal


# ============================================================================
# Location Schemas
# ============================================================================

class LocationBase(BaseModel):
    name: str
    is_active: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class LocationResponse(LocationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Product Schemas
# ============================================================================

class ProductBase(BaseModel):
    name: str
    sale_price_rub: Optional[Decimal] = None
    enabled: bool = True
    visible: bool = True


class ProductCreate(ProductBase):
    product_external_id: int


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sale_price_rub: Optional[Decimal] = None
    enabled: Optional[bool] = None
    visible: Optional[bool] = None


class ProductResponse(ProductBase):
    product_external_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Ingredient Schemas
# ============================================================================

class IngredientBase(BaseModel):
    ingredient_group: Optional[str] = None
    brand_name: Optional[str] = None
    unit: str
    cost_per_unit_rub: Optional[Decimal] = None
    default_load_qty: Optional[Decimal] = None
    alert_threshold: Optional[Decimal] = None
    alert_days_threshold: Optional[int] = 3
    display_name_ru: Optional[str] = None
    unit_ru: Optional[str] = None
    sort_order: Optional[int] = 0
    expense_kind: str = 'stock_tracked'
    is_active: bool = True


class IngredientCreate(IngredientBase):
    ingredient_code: str


class IngredientUpdate(BaseModel):
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
    expense_kind: Optional[str] = None
    is_active: Optional[bool] = None


class IngredientResponse(IngredientBase):
    ingredient_code: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Drink Schemas
# ============================================================================

class DrinkItemBase(BaseModel):
    ingredient_code: str
    qty_per_unit: Decimal
    unit: str


class DrinkItemCreate(DrinkItemBase):
    pass


class DrinkItemResponse(DrinkItemBase):
    display_name_ru: Optional[str] = None
    cost_per_unit_rub: Optional[float] = None
    item_cost_rub: Optional[float] = None  # Стоимость этого ингредиента в рецепте
    
    class Config:
        from_attributes = True


class DrinkBase(BaseModel):
    name: str
    is_active: bool = True


class DrinkCreate(DrinkBase):
    items: List[DrinkItemCreate] = []


class DrinkUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    items: Optional[List[DrinkItemCreate]] = None


class DrinkResponse(DrinkBase):
    id: int
    created_at: datetime
    items: List[DrinkItemResponse] = []
    cogs_rub: Optional[float] = None  # Себестоимость напитка (COGS)

    class Config:
        from_attributes = True


# ============================================================================
# Machine Matrix Schemas
# ============================================================================

class MachineMatrixBase(BaseModel):
    product_external_id: Optional[int] = None
    drink_id: Optional[int] = None
    location_id: Optional[int] = None
    is_active: bool = True


class MachineMatrixCreate(MachineMatrixBase):
    vendista_term_id: int
    machine_item_id: int


class MachineMatrixUpdate(BaseModel):
    product_external_id: Optional[int] = None
    drink_id: Optional[int] = None
    location_id: Optional[int] = None
    is_active: Optional[bool] = None


class MachineMatrixResponse(MachineMatrixBase):
    vendista_term_id: int
    machine_item_id: int
    created_at: datetime
    term_name: Optional[str] = None
    drink_name: Optional[str] = None
    location_name: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Button Matrix Schemas (New Template System)
# ============================================================================

class ButtonMatrixBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class ButtonMatrixCreate(ButtonMatrixBase):
    pass


class ButtonMatrixUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ButtonMatrixResponse(ButtonMatrixBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ButtonMatrixItemBase(BaseModel):
    machine_item_id: int
    drink_id: Optional[int] = None
    sale_price_rub: Optional[float] = None
    is_active: bool = True


class ButtonMatrixItemCreate(ButtonMatrixItemBase):
    pass


class ButtonMatrixItemUpdate(BaseModel):
    drink_id: Optional[int] = None
    sale_price_rub: Optional[float] = None
    is_active: Optional[bool] = None


class ButtonMatrixItemResponse(ButtonMatrixItemBase):
    drink_name: Optional[str] = None
    cogs_rub: Optional[float] = None  # Себестоимость напитка из рецепта

    class Config:
        from_attributes = True


class ButtonMatrixWithItems(ButtonMatrixResponse):
    items: List[ButtonMatrixItemResponse] = []


class TerminalMatrixMapCreate(BaseModel):
    vendista_term_ids: List[int]  # List of terminal IDs to assign


class TerminalMatrixMapResponse(BaseModel):
    matrix_id: int
    matrix_name: str
    vendista_term_id: int
    term_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Ingredient Load Schemas
# ============================================================================

class IngredientLoadBase(BaseModel):
    ingredient_code: str
    location_id: int
    load_date: date
    qty: Decimal
    unit: str
    comment: Optional[str] = None


class IngredientLoadCreate(IngredientLoadBase):
    pass


class IngredientLoadUpdate(BaseModel):
    ingredient_code: Optional[str] = None
    location_id: Optional[int] = None
    load_date: Optional[date] = None
    qty: Optional[Decimal] = None
    unit: Optional[str] = None
    comment: Optional[str] = None


class IngredientLoadResponse(IngredientLoadBase):
    id: int
    created_at: datetime
    created_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# Variable Expense Schemas
# ============================================================================

class VariableExpenseBase(BaseModel):
    expense_date: date
    location_id: Optional[int] = None
    vendista_term_id: Optional[int] = None
    category: str  # 'rent', 'transport', 'maintenance', 'supplies', 'other'
    amount_rub: Decimal
    comment: Optional[str] = None


class VariableExpenseCreate(VariableExpenseBase):
    pass


class VariableExpenseUpdate(BaseModel):
    expense_date: Optional[date] = None
    location_id: Optional[int] = None
    vendista_term_id: Optional[int] = None
    category: Optional[str] = None
    amount_rub: Optional[Decimal] = None
    comment: Optional[str] = None


class VariableExpenseResponse(VariableExpenseBase):
    id: int
    created_at: datetime
    created_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True
