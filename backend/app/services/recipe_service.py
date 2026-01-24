"""
Business logic service for recipe (drink) operations.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from app.crud import business as crud
from app.schemas.business import DrinkCreate, DrinkUpdate
from app.api.middleware.error_handlers import BusinessLogicError
import logging

logger = logging.getLogger(__name__)


class RecipeService:
    """Service for recipe business logic operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_recipe_with_validation(self, drink_data: DrinkCreate) -> Any:
        """
        Create a recipe with comprehensive validation.

        Args:
            drink_data: Recipe creation data

        Returns:
            Created drink object

        Raises:
            BusinessLogicError: If validation fails
        """
        self._validate_recipe_data(drink_data)
        return crud.create_drink(self.db, drink_data)

    def update_recipe_with_validation(self, drink_id: int, drink_update: DrinkUpdate) -> Any:
        """
        Update a recipe with validation.

        Args:
            drink_id: ID of drink to update
            drink_update: Update data

        Returns:
            Updated drink object

        Raises:
            BusinessLogicError: If validation fails or drink not found
        """
        # Validate drink exists
        existing_drink = crud.get_drink(self.db, drink_id)
        if not existing_drink:
            raise BusinessLogicError("Recipe not found", 404)

        # Validate update data
        if drink_update.items is not None:
            self._validate_recipe_items(drink_update.items)

        return crud.update_drink(self.db, drink_id, drink_update)

    def calculate_recipe_cost(self, drink_id: int) -> Dict[str, Any]:
        """
        Calculate total cost of a recipe.

        Args:
            drink_id: ID of drink to calculate cost for

        Returns:
            Dict with cost breakdown

        Raises:
            BusinessLogicError: If drink not found
        """
        drink = crud.get_drink(self.db, drink_id)
        if not drink:
            raise BusinessLogicError("Recipe not found", 404)

        total_cost = 0.0
        item_costs = []

        for item in drink.items:
            ingredient = crud.get_ingredient(self.db, item.ingredient_code)
            if not ingredient:
                logger.warning(f"Ingredient {item.ingredient_code} not found for cost calculation")
                continue

            # Calculate cost for this item
            item_cost = float(item.qty_per_unit) * float(ingredient.cost_per_unit_rub or 0)
            total_cost += item_cost

            item_costs.append({
                'ingredient_code': item.ingredient_code,
                'qty_per_unit': float(item.qty_per_unit),
                'cost_per_unit': float(ingredient.cost_per_unit_rub or 0),
                'item_cost': item_cost
            })

        return {
            'drink_id': drink_id,
            'drink_name': drink.name,
            'total_cost': total_cost,
            'item_costs': item_costs
        }

    def _validate_recipe_data(self, drink_data: DrinkCreate) -> None:
        """
        Validate recipe creation data.

        Args:
            drink_data: Recipe data to validate

        Raises:
            BusinessLogicError: If validation fails
        """
        if not drink_data.name or not drink_data.name.strip():
            raise BusinessLogicError("Recipe name is required")

        if drink_data.items:
            self._validate_recipe_items(drink_data.items)

    def _validate_recipe_items(self, items: List) -> None:
        """
        Validate recipe items.

        Args:
            items: List of recipe items to validate

        Raises:
            BusinessLogicError: If validation fails
        """
        if not items:
            return  # Empty recipe is allowed

        ingredient_codes = set()

        for item in items:
            # Check for duplicate ingredients
            if item.ingredient_code in ingredient_codes:
                raise BusinessLogicError(f"Duplicate ingredient: {item.ingredient_code}")

            ingredient_codes.add(item.ingredient_code)

            # Validate ingredient exists
            ingredient = crud.get_ingredient(self.db, item.ingredient_code)
            if not ingredient:
                raise BusinessLogicError(f"Ingredient not found: {item.ingredient_code}")

            # Validate quantity
            if item.qty_per_unit <= 0:
                raise BusinessLogicError(f"Invalid quantity for {item.ingredient_code}: must be positive")

            # Validate unit consistency
            if item.unit != ingredient.unit:
                logger.warning(f"Unit mismatch for {item.ingredient_code}: recipe uses {item.unit}, ingredient has {ingredient.unit}")

    def get_recipes_with_costs(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recipes with calculated costs.

        Args:
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of recipes with cost information
        """
        drinks = crud.get_drinks(self.db, skip=skip, limit=limit)
        recipes_with_costs = []

        for drink in drinks:
            try:
                cost_info = self.calculate_recipe_cost(drink.id)
                recipes_with_costs.append({
                    'id': drink.id,
                    'name': drink.name,
                    'is_active': drink.is_active,
                    'cost_info': cost_info
                })
            except Exception as e:
                logger.error(f"Error calculating cost for drink {drink.id}: {str(e)}")
                recipes_with_costs.append({
                    'id': drink.id,
                    'name': drink.name,
                    'is_active': drink.is_active,
                    'cost_info': None
                })

        return recipes_with_costs