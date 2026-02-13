#!/usr/bin/env python3
"""
Скрипт для создания пользователя с email/паролем
"""
import sys
import os

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.crud.user import create_user, get_user_by_email
from app.schemas.auth import UserCreate


def main():
    if len(sys.argv) < 4:
        print("Usage: python create_user.py <email> <password> <role> [first_name]")
        print("Example: python create_user.py admin@example.com password123 owner Admin")
        print("\nRoles:")
        print("  - owner: Full access to all sections")
        print("  - operator: Limited access (no matrix templates, no settings)")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    role = sys.argv[3]
    first_name = sys.argv[4] if len(sys.argv) > 4 else email.split('@')[0]
    
    if role not in ['owner', 'operator']:
        print("❌ Error: role must be 'owner' or 'operator'")
        sys.exit(1)
    
    db = SessionLocal()
    
    try:
        # Проверяем, существует ли пользователь
        existing = get_user_by_email(db, email)
        if existing:
            print(f"❌ Error: User with email {email} already exists")
            sys.exit(1)
        
        # Создаем пользователя
        user = create_user(
            db,
            UserCreate(
                email=email,
                password=password,
                first_name=first_name,
                role=role,
            )
        )
        
        print(f"\n✅ User created successfully!")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.first_name}")
        print(f"   Role: {user.role}")
        print(f"   ID: {user.id}")
        print(f"\n🔐 You can now login with:")
        print(f"   Email: {user.email}")
        print(f"   Password: {password}")
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
