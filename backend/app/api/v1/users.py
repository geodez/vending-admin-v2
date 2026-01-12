"""
API endpoints for user management (Owner only).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse, UserCreate
from app.crud import user as crud_user
from pydantic import BaseModel

router = APIRouter()


class UserUpdateRequest(BaseModel):
    """Request schema for updating user."""
    role: str | None = None
    is_active: bool | None = None


def require_owner(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure only owners can access."""
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can manage users"
        )
    return current_user


@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    """
    Get list of all users (Owner only).
    """
    users = crud_user.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    """
    Get user by ID (Owner only).
    """
    user = crud_user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    """
    Create a new user (Owner only).
    """
    # Check if user already exists
    existing_user = crud_user.get_user_by_telegram_id(db, user.telegram_user_id)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this Telegram ID already exists"
        )
    
    return crud_user.create_user(db, user)


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    """
    Update user role or active status (Owner only).
    """
    user = crud_user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if user_update.role is not None:
        if user_update.role not in ['owner', 'operator']:
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = user_update.role
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    """
    Delete user (Owner only).
    Prevents deleting yourself.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete yourself"
        )
    
    user = crud_user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return None
