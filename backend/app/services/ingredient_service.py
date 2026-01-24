"""
Business logic service for ingredient operations.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.crud import business as crud
from app.schemas.business import IngredientUpdate, IngredientCreate
from app.api.middleware.error_handlers import BusinessLogicError
import logging

logger = logging.getLogger(__name__)


class IngredientService:
    """Service for ingredient business logic operations."""

    def __init__(self, db: Session):
        self.db = db

    def bulk_update_ingredients(
        self,
        ingredient_codes: List[str],
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform bulk update of ingredients with validation and error handling.

        Args:
            ingredient_codes: List of ingredient codes to update
            update_data: Dictionary of fields to update

        Returns:
            Dict with update results and errors

        Raises:
            BusinessLogicError: If validation fails
        """
        if not ingredient_codes:
            raise BusinessLogicError("No ingredient codes provided")

        logger.info(f"Bulk update request: {len(ingredient_codes)} codes")

        # Validate that we have fields to update
        if not update_data:
            raise BusinessLogicError("No fields to update provided")

        # Create IngredientUpdate from provided data
        ingredient_update = IngredientUpdate(**update_data)

        updated_count = 0
        errors = []

        for code in ingredient_codes:
            try:
                # Validate ingredient exists
                existing = crud.get_ingredient(self.db, code)
                if not existing:
                    logger.warning(f"Ingredient not found: {code}")
                    errors.append(f"Ingredient {code} not found")
                    continue

                # Perform update
                ingredient = crud.update_ingredient(self.db, code, ingredient_update)
                if ingredient:
                    updated_count += 1
                    logger.info(f"Updated ingredient: {code}")
                else:
                    errors.append(f"Failed to update ingredient {code}")

            except Exception as e:
                logger.error(f"Error updating {code}: {str(e)}")
                errors.append(f"Error updating {code}: {str(e)}")

        # Commit all changes
        self.db.commit()

        logger.info(f"Bulk update completed: {updated_count}/{len(ingredient_codes)} updated")

        return {
            "updated": updated_count,
            "total": len(ingredient_codes),
            "errors": errors if errors else None
        }

    def delete_ingredient_safe(self, ingredient_code: str) -> None:
        """
        Safely delete an ingredient with dependency checks.

        Args:
            ingredient_code: Code of ingredient to delete

        Raises:
            BusinessLogicError: If ingredient is in use or not found
        """
        try:
            crud.delete_ingredient(self.db, ingredient_code)
        except ValueError as e:
            # Ingredient is used in recipes
            raise BusinessLogicError(str(e), 400)

    def get_ingredients_paginated(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """
        Get paginated list of ingredients with optimized query.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of ingredients
        """
        return crud.get_ingredients(self.db, skip=skip, limit=limit)

    def validate_ingredient_data(self, ingredient_data: Dict[str, Any]) -> None:
        """
        Validate ingredient data before creation/update.

        Args:
            ingredient_data: Ingredient data to validate

        Raises:
            BusinessLogicError: If validation fails
        """
        # Check required fields
        required_fields = ['ingredient_code', 'unit']
        for field in required_fields:
            if field not in ingredient_data or not ingredient_data[field]:
                raise BusinessLogicError(f"Required field '{field}' is missing or empty")

        # Validate ingredient_code format (if needed)
        code = ingredient_data['ingredient_code']
        if not isinstance(code, str) or len(code.strip()) == 0:
            raise BusinessLogicError("Ingredient code must be a non-empty string")

        # Validate numeric fields
        if 'cost_per_unit_rub' in ingredient_data:
            cost = ingredient_data['cost_per_unit_rub']
            if cost is not None and cost < 0:
                raise BusinessLogicError("Cost per unit cannot be negative")

        if 'default_load_qty' in ingredient_data:
            qty = ingredient_data['default_load_qty']
            if qty is not None and qty <= 0:
                raise BusinessLogicError("Default load quantity must be positive")