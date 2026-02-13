
import sys
import os

# Add app path
sys.path.insert(0, "/app")

from app.db.session import SessionLocal
from app.crud.user import get_user_by_email
from app.auth.password import get_password_hash, verify_password

def reset_password(email="admin@example.com", new_password="TestPass123"):
    db = SessionLocal()
    try:
        user = get_user_by_email(db, email)
        if not user:
            print(f"❌ User {email} not found!")
            return False
            
        print(f"User {email} found.")
        
        # Verify if password already matches
        current_match = False
        try:
             current_match = verify_password(new_password, user.hashed_password)
        except Exception:
             pass # Maybe old hash format

        if current_match:
            print(f"✅ Password is already '{new_password}'")
            return True
            
        print(f"Updating password to '{new_password}'...")
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        db.commit()
        print(f"✅ Password updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    email = "admin@example.com"
    password = "TestPass123"
    
    if len(sys.argv) > 1:
        password = sys.argv[1]
    
    reset_password(email, password)
