"""
Integration tests for business API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestLocationsEndpoints:
    """Test cases for location endpoints."""

    def test_create_location(self, client, auth_headers_owner):
        """Test creating a location."""
        location_data = {"name": "Test Location", "is_active": True}

        with patch('app.crud.business.create_location') as mock_create:
            mock_create.return_value = type('Location', (), {
                'id': 1,
                'name': 'Test Location',
                'is_active': True,
                'created_at': '2024-01-01T00:00:00'
            })()

            response = client.post("/api/v1/business/locations", json=location_data, headers=auth_headers_owner)
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Location"
            assert data["is_active"] is True

    def test_get_location_not_found(self, client, auth_headers_operator):
        """Test getting non-existent location."""
        with patch('app.crud.business.get_location', return_value=None):
            response = client.get("/api/v1/business/locations/999", headers=auth_headers_operator)
            assert response.status_code == 404
            assert "Location not found" in response.json()["detail"]


class TestIngredientsEndpoints:
    """Test cases for ingredient endpoints."""

    def test_bulk_update_ingredients_success(self, client, auth_headers_owner):
        """Test successful bulk ingredient update."""
        bulk_data = {
            "ingredient_codes": ["ING_001", "ING_002"],
            "is_active": False,
            "cost_per_unit_rub": 150.0
        }

        # Mock successful bulk update
        with patch('app.services.ingredient_service.IngredientService.bulk_update_ingredients') as mock_bulk:
            mock_bulk.return_value = {
                "updated": 2,
                "total": 2,
                "errors": None
            }

            response = client.put("/api/v1/business/ingredients/bulk/update", json=bulk_data, headers=auth_headers_owner)
            assert response.status_code == 200
            data = response.json()
            assert data["updated"] == 2
            assert data["total"] == 2

    def test_bulk_update_ingredients_validation_error(self, client, auth_headers_owner):
        """Test bulk update with validation error."""
        # Valid ingredient codes but no fields to update
        bulk_data = {
            "ingredient_codes": ["TEST_001"],
            # No update fields provided
        }

        response = client.put("/api/v1/business/ingredients/bulk/update", json=bulk_data, headers=auth_headers_owner)
        assert response.status_code == 400
        assert "No fields to update provided" in response.json()["detail"]

    def test_create_ingredient_validation_error(self, client, auth_headers_owner):
        """Test creating ingredient with validation error."""
        invalid_data = {
            "ingredient_code": "TEST_001"
            # Missing required 'unit' field
        }

        response = client.post("/api/v1/business/ingredients", json=invalid_data, headers=auth_headers_owner)
        assert response.status_code == 422  # Validation error


class TestDrinksEndpoints:
    """Test cases for drink/recipe endpoints."""

    def test_create_drink_success(self, client, auth_headers_owner):
        """Test creating a drink with recipe."""
        drink_data = {
            "name": "Test Cappuccino",
            "is_active": True,
            "items": [
                {
                    "ingredient_code": "COFFEE_001",
                    "qty_per_unit": 10.0,
                    "unit": "g"
                },
                {
                    "ingredient_code": "MILK_001",
                    "qty_per_unit": 100.0,
                    "unit": "ml"
                }
            ]
        }

        # Mock ingredient existence checks
        mock_ing = MagicMock()
        with patch('app.crud.business.get_ingredient', return_value=mock_ing), \
             patch('app.services.recipe_service.RecipeService.create_recipe_with_validation') as mock_create:

            mock_create.return_value = type('Drink', (), {
                'id': 1,
                'name': 'Test Cappuccino',
                'is_active': True,
                'created_at': '2024-01-01T00:00:00',
                'items': []
            })()

            response = client.post("/api/v1/business/drinks", json=drink_data, headers=auth_headers_owner)
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Cappuccino"

    def test_get_drink_cost(self, client, auth_headers_owner):
        """Test getting drink cost calculation."""
        with patch('app.services.recipe_service.RecipeService.calculate_recipe_cost') as mock_cost:
            mock_cost.return_value = {
                "drink_id": 1,
                "drink_name": "Test Drink",
                "total_cost": 250.0,
                "item_costs": []
            }

            response = client.get("/api/v1/business/drinks/1/cost", headers=auth_headers_owner)
            assert response.status_code == 200
            data = response.json()
            assert data["total_cost"] == 250.0


class TestInventoryEndpoints:
    """Test cases for inventory management endpoints."""

    def test_get_inventory_status(self, client, auth_headers_operator):
        """Test getting inventory status report."""
        with patch('app.services.expense_service.ExpenseService.get_inventory_status_report') as mock_status:
            mock_status.return_value = {
                "report_period_days": 30,
                "total_loads": 10,
                "ingredients": {
                    "COFFEE_001": {
                        "total_loaded": 100.0,
                        "load_count": 5,
                        "last_load_date": "2024-01-15",
                        "locations": [1, 2]
                    }
                }
            }

            response = client.get("/api/v1/business/inventory/status", headers=auth_headers_operator)
            assert response.status_code == 200
            data = response.json()
            assert data["total_loads"] == 10
            assert "COFFEE_001" in data["ingredients"]

    def test_create_ingredient_load_validation_error(self, client, auth_headers_owner):
        """Test creating ingredient load with validation error."""
        invalid_load_data = {
            "ingredient_code": "INVALID_ING",  # Non-existent ingredient
            "location_id": 1,
            "qty": 10.0,
            "unit": "kg",
            "load_date": "2024-01-01"
        }

        # Mock ingredient not found
        with patch('app.crud.business.get_ingredient', return_value=None):
            response = client.post("/api/v1/business/ingredient-loads", json=invalid_load_data, headers=auth_headers_owner)
            assert response.status_code == 400
            assert "Ingredient not found" in response.json()["detail"]


class TestErrorHandling:
    """Test cases for error handling across endpoints."""

    def test_database_error_handling(self, client, auth_headers_owner):
        """Test that database errors are properly handled."""
        with patch('app.services.ingredient_service.IngredientService.bulk_update_ingredients') as mock_bulk:
            mock_bulk.side_effect = Exception("Database connection failed")

            bulk_data = {
                "ingredient_codes": ["ING_001"],
                "is_active": False
            }

            response = client.put("/api/v1/business/ingredients/bulk/update", json=bulk_data, headers=auth_headers_owner)
            assert response.status_code == 500
            data = response.json()
            assert "Bulk ingredient update failed" in data["detail"]
            assert data["type"] == "http_error"