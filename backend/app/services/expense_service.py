"""
Business logic service for expense operations.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from app.crud import business as crud
from app.schemas.business import IngredientLoadCreate, VariableExpenseCreate
from app.api.middleware.error_handlers import BusinessLogicError
import logging

logger = logging.getLogger(__name__)


class ExpenseService:
    """Service for expense-related business logic operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_ingredient_load_with_validation(
        self,
        load_data: IngredientLoadCreate,
        user_id: Optional[int] = None
    ) -> Any:
        """
        Create ingredient load with business validation.

        Args:
            load_data: Load creation data
            user_id: ID of user creating the load

        Returns:
            Created ingredient load

        Raises:
            BusinessLogicError: If validation fails
        """
        self._validate_ingredient_load_data(load_data)
        return crud.create_ingredient_load(self.db, load_data, user_id)

    def create_variable_expense_with_validation(
        self,
        expense_data: VariableExpenseCreate,
        user_id: Optional[int] = None
    ) -> Any:
        """
        Create variable expense with business validation.

        Args:
            expense_data: Expense creation data
            user_id: ID of user creating the expense

        Returns:
            Created variable expense

        Raises:
            BusinessLogicError: If validation fails
        """
        self._validate_variable_expense_data(expense_data)
        return crud.create_variable_expense(self.db, expense_data, user_id)

    def get_inventory_status_report(
        self,
        ingredient_code: Optional[str] = None,
        location_id: Optional[int] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Generate inventory status report.

        Args:
            ingredient_code: Filter by specific ingredient
            location_id: Filter by location
            days_back: Number of days to look back

        Returns:
            Inventory status report
        """
        from_date = date.today() - timedelta(days=days_back)

        loads = crud.get_ingredient_loads(
            self.db,
            ingredient_code=ingredient_code,
            location_id=location_id,
            from_date=from_date
        )

        # Group by ingredient and calculate totals
        ingredient_totals = {}
        for load in loads:
            code = load.ingredient_code
            if code not in ingredient_totals:
                ingredient_totals[code] = {
                    'total_loaded': 0,
                    'load_count': 0,
                    'last_load_date': None,
                    'locations': set()
                }

            ingredient_totals[code]['total_loaded'] += float(load.qty_loaded)
            ingredient_totals[code]['load_count'] += 1
            ingredient_totals[code]['locations'].add(load.location_id)

            if (ingredient_totals[code]['last_load_date'] is None or
                load.load_date > ingredient_totals[code]['last_load_date']):
                ingredient_totals[code]['last_load_date'] = load.load_date

        # Convert sets to lists for JSON serialization
        for code in ingredient_totals:
            ingredient_totals[code]['locations'] = list(ingredient_totals[code]['locations'])

        return {
            'report_period_days': days_back,
            'total_loads': len(loads),
            'ingredients': ingredient_totals
        }

    def get_expense_summary(
        self,
        location_id: Optional[int] = None,
        category: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate expense summary report.

        Args:
            location_id: Filter by location
            category: Filter by expense category
            from_date: Start date for report
            to_date: End date for report

        Returns:
            Expense summary report
        """
        expenses = crud.get_variable_expenses(
            self.db,
            location_id=location_id,
            category=category,
            from_date=from_date,
            to_date=to_date
        )

        # Calculate totals by category
        category_totals = {}
        total_amount = 0

        for expense in expenses:
            cat = expense.category or 'uncategorized'
            if cat not in category_totals:
                category_totals[cat] = {
                    'count': 0,
                    'total_amount': 0,
                    'expenses': []
                }

            category_totals[cat]['count'] += 1
            category_totals[cat]['total_amount'] += float(expense.amount_rub)
            total_amount += float(expense.amount_rub)

            category_totals[cat]['expenses'].append({
                'id': expense.id,
                'description': expense.description,
                'amount_rub': float(expense.amount_rub),
                'expense_date': expense.expense_date.isoformat(),
                'location_id': expense.location_id
            })

        return {
            'total_expenses': len(expenses),
            'total_amount_rub': total_amount,
            'categories': category_totals,
            'date_range': {
                'from': from_date.isoformat() if from_date else None,
                'to': to_date.isoformat() if to_date else None
            }
        }

    def _validate_ingredient_load_data(self, load_data: IngredientLoadCreate) -> None:
        """
        Validate ingredient load data.

        Args:
            load_data: Load data to validate

        Raises:
            BusinessLogicError: If validation fails
        """
        # Validate ingredient exists
        ingredient = crud.get_ingredient(self.db, load_data.ingredient_code)
        if not ingredient:
            raise BusinessLogicError(f"Ingredient not found: {load_data.ingredient_code}")

        # Validate location exists
        location = crud.get_location(self.db, load_data.location_id)
        if not location:
            raise BusinessLogicError(f"Location not found: {load_data.location_id}")

        # Validate quantity
        if load_data.qty <= 0:
            raise BusinessLogicError("Load quantity must be positive")

        # Validate load date is not in future
        if load_data.load_date > date.today():
            raise BusinessLogicError("Load date cannot be in the future")

    def _validate_variable_expense_data(self, expense_data: VariableExpenseCreate) -> None:
        """
        Validate variable expense data.

        Args:
            expense_data: Expense data to validate

        Raises:
            BusinessLogicError: If validation fails
        """
        # Validate amount
        if expense_data.amount_rub <= 0:
            raise BusinessLogicError("Expense amount must be positive")

        # Validate location exists
        location = crud.get_location(self.db, expense_data.location_id)
        if not location:
            raise BusinessLogicError(f"Location not found: {expense_data.location_id}")

        # Validate expense date
        if expense_data.expense_date > date.today():
            raise BusinessLogicError("Expense date cannot be in the future")

        # Validate category if provided
        valid_categories = ['utilities', 'maintenance', 'supplies', 'marketing', 'other']
        if expense_data.category and expense_data.category not in valid_categories:
            raise BusinessLogicError(f"Invalid category. Must be one of: {', '.join(valid_categories)}")