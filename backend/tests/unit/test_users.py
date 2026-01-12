"""
Unit tests for user management.
"""
import pytest


def test_list_users_as_owner(client, owner_user, auth_headers_owner):
    """Test listing users as owner."""
    response = client.get("/api/v1/users", headers=auth_headers_owner)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) >= 1


def test_list_users_as_operator_forbidden(client, operator_user, auth_headers_operator):
    """Test that operators cannot list users."""
    response = client.get("/api/v1/users", headers=auth_headers_operator)
    assert response.status_code == 403


def test_create_user_as_owner(client, auth_headers_owner):
    """Test creating a user as owner."""
    user_data = {
        "telegram_user_id": 999888777,
        "username": "newuser",
        "first_name": "New",
        "last_name": "User",
        "role": "operator"
    }
    response = client.post("/api/v1/users", json=user_data, headers=auth_headers_owner)
    assert response.status_code == 201
    data = response.json()
    assert data["telegram_user_id"] == user_data["telegram_user_id"]
    assert data["role"] == "operator"


def test_get_user_by_id(client, owner_user, auth_headers_owner):
    """Test getting user by ID."""
    response = client.get(f"/api/v1/users/{owner_user.id}", headers=auth_headers_owner)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == owner_user.id


def test_update_user_role(client, operator_user, auth_headers_owner):
    """Test updating user role."""
    update_data = {"role": "owner"}
    response = client.put(
        f"/api/v1/users/{operator_user.id}",
        json=update_data,
        headers=auth_headers_owner
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "owner"


def test_delete_user(client, operator_user, auth_headers_owner):
    """Test deleting a user."""
    response = client.delete(
        f"/api/v1/users/{operator_user.id}",
        headers=auth_headers_owner
    )
    assert response.status_code == 204


def test_cannot_delete_self(client, owner_user, auth_headers_owner):
    """Test that user cannot delete themselves."""
    response = client.delete(
        f"/api/v1/users/{owner_user.id}",
        headers=auth_headers_owner
    )
    assert response.status_code == 400
