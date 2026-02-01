"""
Inventory and expense models.
"""
from sqlalchemy import Column, Integer, Text, TIMESTAMP, Numeric, ForeignKey, Date
from sqlalchemy.sql import func
from app.db.base import Base


class IngredientLoad(Base):
    """Ingredient stock loads (purchases/deliveries)."""
    __tablename__ = "ingredient_loads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ingredient_code = Column(Text, ForeignKey('ingredients.ingredient_code'), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False, index=True)
    load_date = Column(Date, nullable=False, index=True)
    qty = Column(Numeric(10, 2), nullable=False)
    unit = Column(Text, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        return f"<IngredientLoad(id={self.id}, ingredient={self.ingredient_code}, qty={self.qty})>"


class VariableExpense(Base):
    """Variable expenses (rent, transport, maintenance, etc.)."""
    __tablename__ = "variable_expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_date = Column(Date, nullable=False, index=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=True, index=True)
    vendista_term_id = Column(Integer, ForeignKey('vendista_terminals.id'), nullable=True, index=True)
    category = Column(Text, nullable=False, index=True)  # 'rent', 'transport', 'maintenance', 'supplies', 'other'
    amount_rub = Column(Numeric(10, 2), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        return f"<VariableExpense(id={self.id}, category={self.category}, amount={self.amount_rub})>"
