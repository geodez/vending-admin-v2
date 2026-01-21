"""
Business models for locations, products, ingredients, drinks, and recipes.
"""
from sqlalchemy import Column, Integer, BigInteger, Text, Boolean, TIMESTAMP, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Location(Base):
    """Physical locations where terminals are installed."""
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Location(id={self.id}, name={self.name})>"


class Product(Base):
    """Products from Vendista (drinks that can be sold)."""
    __tablename__ = "products"

    product_external_id = Column(Integer, primary_key=True)  # External ID from Vendista
    name = Column(Text, nullable=False)
    sale_price_rub = Column(Numeric(10, 2), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    visible = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Product(id={self.product_external_id}, name={self.name})>"


class Ingredient(Base):
    """Ingredients used in drink recipes."""
    __tablename__ = "ingredients"

    ingredient_code = Column(Text, primary_key=True)  # e.g., 'COFFEE_BEANS'
    ingredient_group = Column(Text, nullable=True)  # e.g., 'Coffee', 'Milk', 'Syrups'
    brand_name = Column(Text, nullable=True)
    unit = Column(Text, nullable=False)  # g, ml, pcs
    cost_per_unit_rub = Column(Numeric(10, 2), nullable=True)  # Cost per unit in rubles
    default_load_qty = Column(Numeric(10, 2), nullable=True)  # Default quantity when loading stock
    alert_threshold = Column(Numeric(10, 2), nullable=True)  # Minimum stock alert threshold
    alert_days_threshold = Column(Integer, nullable=True, default=3)  # Days left alert threshold
    display_name_ru = Column(Text, nullable=True)
    unit_ru = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=True, default=0)
    expense_kind = Column(Text, nullable=False, default='stock_tracked')  # 'stock_tracked' or 'not_tracked'
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Ingredient(code={self.ingredient_code}, name={self.display_name_ru})>"


class Drink(Base):
    """Global catalog of drinks (recipes)."""
    __tablename__ = "drinks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Drink(id={self.id}, name={self.name})>"


class DrinkItem(Base):
    """Recipe composition - ingredients in a drink."""
    __tablename__ = "drink_items"

    drink_id = Column(Integer, ForeignKey('drinks.id', ondelete='CASCADE'), primary_key=True)
    ingredient_code = Column(Text, ForeignKey('ingredients.ingredient_code', ondelete='CASCADE'), primary_key=True)
    qty_per_unit = Column(Numeric(10, 2), nullable=False)  # Quantity per one serving
    unit = Column(Text, nullable=False)  # g, ml, pcs

    def __repr__(self):
        return f"<DrinkItem(drink_id={self.drink_id}, ingredient={self.ingredient_code}, qty={self.qty_per_unit})>"


class MachineMatrix(Base):
    """Mapping between terminal buttons and recipes."""
    __tablename__ = "machine_matrix"

    vendista_term_id = Column(BigInteger, ForeignKey('vendista_terminals.id'), primary_key=True)
    machine_item_id = Column(Integer, primary_key=True)  # Button ID on terminal
    product_external_id = Column(Integer, ForeignKey('products.product_external_id'), nullable=True)
    drink_id = Column(Integer, ForeignKey('drinks.id'), nullable=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<MachineMatrix(term={self.vendista_term_id}, button={self.machine_item_id})>"


class ButtonMatrix(Base):
    """Template for button-to-drink mappings (matrix template)."""
    __tablename__ = "button_matrices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ButtonMatrix(id={self.id}, name={self.name})>"


class ButtonMatrixItem(Base):
    """Button mapping item in a matrix template.
    
    Maps button ID to drink. Location is determined by terminal's location_id.
    """
    __tablename__ = "button_matrix_items"

    matrix_id = Column(Integer, ForeignKey('button_matrices.id', ondelete='CASCADE'), primary_key=True)
    machine_item_id = Column(Integer, primary_key=True)  # Button ID
    drink_id = Column(Integer, ForeignKey('drinks.id', ondelete='SET NULL'), nullable=True)
    sale_price_rub = Column(Numeric(10, 2), nullable=True)  # Sale price in rubles
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ButtonMatrixItem(matrix_id={self.matrix_id}, button={self.machine_item_id}, drink_id={self.drink_id}, price={self.sale_price_rub})>"


class TerminalMatrixMap(Base):
    """Mapping of terminals to button matrices."""
    __tablename__ = "terminal_matrix_map"

    matrix_id = Column(Integer, ForeignKey('button_matrices.id', ondelete='CASCADE'), primary_key=True)
    vendista_term_id = Column(BigInteger, ForeignKey('vendista_terminals.id', ondelete='CASCADE'), primary_key=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<TerminalMatrixMap(matrix_id={self.matrix_id}, term_id={self.vendista_term_id})>"
