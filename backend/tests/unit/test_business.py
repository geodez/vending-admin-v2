"""
Unit tests for business entities.
"""
import pytest


def test_create_location(client, auth_headers_owner):
    """Test creating a location."""
    location_data = {"name": "Test Location"}
    response = client.post("/api/v1/business/locations", json=location_data, headers=auth_headers_owner)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Location"


def test_list_locations(client, auth_headers_operator):
    """Test listing locations."""
    response = client.get("/api/v1/business/locations", headers=auth_headers_operator)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_product(client, auth_headers_owner):
    """Test creating a product."""
    product_data = {
        "product_external_id": "TEST_PROD_001",
        "name": "Test Product",
        "sale_price_rub": 150.0,
        "enabled": True,
        "visible": True
    }
    response = client.post("/api/v1/business/products", json=product_data, headers=auth_headers_owner)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"


def test_create_ingredient(client, auth_headers_owner):
    """Test creating an ingredient."""
    ingredient_data = {
        "ingredient_code": "TEST_ING_001",
        "ingredient_group": "coffee",
        "brand_name": "Test Brand",
        "unit": "kg",
        "cost_per_unit_rub": 1500.0,
        "expense_kind": "stock_tracked",
        "is_stock_tracked": True
    }
    response = client.post("/api/v1/business/ingredients", json=ingredient_data, headers=auth_headers_owner)
    assert response.status_code == 201
    data = response.json()
    assert data["ingredient_code"] == "TEST_ING_001"


def test_create_drink(client, auth_headers_owner):
    """Test creating a drink."""
    drink_data = {
        "name": "Test Cappuccino",
        "is_active": True
    }
    response = client.post("/api/v1/business/drinks", json=drink_data, headers=auth_headers_owner)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Cappuccino"
