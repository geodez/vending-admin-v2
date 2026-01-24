"""
Unit tests for business services.
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.services.ingredient_service import IngredientService
from app.services.recipe_service import RecipeService
from app.services.expense_service import ExpenseService
from app.api.middleware.error_handlers import BusinessLogicError
from app.schemas.business import IngredientCreate, DrinkCreate, DrinkItemCreate, IngredientLoadCreate, VariableExpenseCreate


class TestIngredientService:
    """Test cases for IngredientService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.db = MagicMock(spec=Session)
        self.service = IngredientService(self.db)

    def test_bulk_update_ingredients_success(self):
        """Test successful bulk ingredient update."""
        # Mock ingredient existence check
        mock_ingredient = MagicMock()
        mock_ingredient.ingredient_code = "TEST_001"

        with patch('app.crud.business.get_ingredient', return_value=mock_ingredient), \
             patch('app.crud.business.update_ingredient', return_value=mock_ingredient):

            result = self.service.bulk_update_ingredients(
                ingredient_codes=["TEST_001", "TEST_002"],
                update_data={"is_active": False, "cost_per_unit_rub": 100.0}
            )

            assert result["updated"] == 2
            assert result["total"] == 2
            assert result["errors"] is None

    def test_bulk_update_ingredients_partial_failure(self):
        """Test bulk update with some failures."""
        mock_ingredient = MagicMock()
        mock_ingredient.ingredient_code = "TEST_001"

        with patch('app.crud.business.get_ingredient') as mock_get, \
             patch('app.crud.business.update_ingredient') as mock_update:

            # First ingredient exists, second doesn't
            mock_get.side_effect = [mock_ingredient, None]
            mock_update.return_value = mock_ingredient

            result = self.service.bulk_update_ingredients(
                ingredient_codes=["TEST_001", "TEST_002"],
                update_data={"is_active": False}
            )

            assert result["updated"] == 1
            assert result["total"] == 2
            assert len(result["errors"]) == 1
            assert "TEST_002 not found" in result["errors"][0]

    def test_bulk_update_ingredients_no_codes(self):
        """Test bulk update with empty ingredient codes list."""
        with pytest.raises(BusinessLogicError, match="No ingredient codes provided"):
            self.service.bulk_update_ingredients([], {})

    def test_bulk_update_ingredients_no_fields(self):
        """Test bulk update with no fields to update."""
        with pytest.raises(BusinessLogicError, match="No fields to update provided"):
            self.service.bulk_update_ingredients(["TEST_001"], {})

    def test_validate_ingredient_data_valid(self):
        """Test validation of valid ingredient data."""
        valid_data = {
            'ingredient_code': 'TEST_001',
            'unit': 'kg',
            'cost_per_unit_rub': 100.0,
            'default_load_qty': 10.0
        }

        # Should not raise any exception
        self.service.validate_ingredient_data(valid_data)

    def test_validate_ingredient_data_missing_required(self):
        """Test validation with missing required fields."""
        invalid_data = {'ingredient_code': 'TEST_001'}  # Missing unit

        with pytest.raises(BusinessLogicError, match="Required field 'unit' is missing"):
            self.service.validate_ingredient_data(invalid_data)

    def test_validate_ingredient_data_negative_cost(self):
        """Test validation with negative cost."""
        invalid_data = {
            'ingredient_code': 'TEST_001',
            'unit': 'kg',
            'cost_per_unit_rub': -100.0
        }

        with pytest.raises(BusinessLogicError, match="Cost per unit cannot be negative"):
            self.service.validate_ingredient_data(invalid_data)


class TestRecipeService:
    """Test cases for RecipeService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.db = MagicMock(spec=Session)
        self.service = RecipeService(self.db)

    def test_calculate_recipe_cost(self):
        """Test recipe cost calculation."""
        # Mock drink with items
        mock_drink = MagicMock()
        mock_drink.id = 1
        mock_drink.name = "Test Drink"

        # Mock drink items
        mock_item1 = MagicMock()
        mock_item1.ingredient_code = "ING_001"
        mock_item1.qty_per_unit = 10.0

        mock_item2 = MagicMock()
        mock_item2.ingredient_code = "ING_002"
        mock_item2.qty_per_unit = 5.0

        mock_drink.items = [mock_item1, mock_item2]

        # Mock ingredients
        mock_ing1 = MagicMock()
        mock_ing1.cost_per_unit_rub = 50.0

        mock_ing2 = MagicMock()
        mock_ing2.cost_per_unit_rub = 20.0

        with patch('app.crud.business.get_drink', return_value=mock_drink), \
             patch('app.crud.business.get_ingredient') as mock_get_ing:

            mock_get_ing.side_effect = [mock_ing1, mock_ing2]

            result = self.service.calculate_recipe_cost(1)

            assert result['drink_id'] == 1
            assert result['drink_name'] == "Test Drink"
            assert result['total_cost'] == 600.0  # (10*50) + (5*20) = 500 + 100
            assert len(result['item_costs']) == 2

    def test_validate_recipe_data_valid(self):
        """Test validation of valid recipe data."""
        valid_data = DrinkCreate(
            name="Test Drink",
            items=[
                DrinkItemCreate(ingredient_code="ING_001", qty_per_unit=10.0, unit="g"),
                DrinkItemCreate(ingredient_code="ING_002", qty_per_unit=5.0, unit="ml")
            ]
        )

        # Mock ingredient existence
        mock_ing = MagicMock()

        with patch('app.crud.business.get_ingredient', return_value=mock_ing):
            # Should not raise any exception
            self.service._validate_recipe_data(valid_data)

    def test_validate_recipe_data_duplicate_ingredients(self):
        """Test validation with duplicate ingredients."""
        invalid_data = DrinkCreate(
            name="Test Drink",
            items=[
                DrinkItemCreate(ingredient_code="ING_001", qty_per_unit=10.0, unit="g"),
                DrinkItemCreate(ingredient_code="ING_001", qty_per_unit=5.0, unit="g")  # Duplicate
            ]
        )

        with pytest.raises(BusinessLogicError, match="Duplicate ingredient"):
            self.service._validate_recipe_data(invalid_data)


class TestExpenseService:
    """Test cases for ExpenseService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.db = MagicMock(spec=Session)
        self.service = ExpenseService(self.db)

    def test_validate_ingredient_load_data_valid(self):
        """Test validation of valid ingredient load data."""
        valid_data = IngredientLoadCreate(
            ingredient_code="ING_001",
            location_id=1,
            qty=10.0,
            unit="kg",
            load_date="2024-01-01"
        )

        # Mock existence checks
        mock_ing = MagicMock()
        mock_loc = MagicMock()

        with patch('app.crud.business.get_ingredient', return_value=mock_ing), \
             patch('app.crud.business.get_location', return_value=mock_loc):

            # Should not raise any exception
            self.service._validate_ingredient_load_data(valid_data)

    def test_validate_ingredient_load_data_invalid_ingredient(self):
        """Test validation with non-existent ingredient."""
        invalid_data = IngredientLoadCreate(
            ingredient_code="INVALID_ING",
            location_id=1,
            qty=10.0,
            unit="kg",
            load_date="2024-01-01"
        )

        with patch('app.crud.business.get_ingredient', return_value=None):
            with pytest.raises(BusinessLogicError, match="Ingredient not found"):
                self.service._validate_ingredient_load_data(invalid_data)

    def test_validate_variable_expense_data_valid(self):
        """Test validation of valid variable expense data."""
        valid_data = VariableExpenseCreate(
            description="Test expense",
            amount_rub=1000.0,
            location_id=1,
            category="utilities",
            expense_date="2024-01-01"
        )

        # Mock location existence
        mock_loc = MagicMock()

        with patch('app.crud.business.get_location', return_value=mock_loc):
            # Should not raise any exception
            self.service._validate_variable_expense_data(valid_data)

    def test_validate_variable_expense_data_invalid_category(self):
        """Test validation with invalid expense category."""
        invalid_data = VariableExpenseCreate(
            description="Test expense",
            amount_rub=1000.0,
            location_id=1,
            category="invalid_category",
            expense_date="2024-01-01"
        )

        mock_loc = MagicMock()

        with patch('app.crud.business.get_location', return_value=mock_loc):
            with pytest.raises(BusinessLogicError, match="Invalid category"):
                self.service._validate_variable_expense_data(invalid_data)