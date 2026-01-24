"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User

# Test database URL (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database and session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db):
    """Alias for db fixture for compatibility."""
    return db


@pytest.fixture(scope="function")
def client(db):
    """Create test client."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def create_test_user(db):
    """Factory fixture to create test users."""
    def _create_user(
        telegram_user_id: int,
        role: str = "operator",
        is_active: bool = True,
        username: str = None,
        first_name: str = None,
        last_name: str = None
    ) -> User:
        user = User(
            telegram_user_id=telegram_user_id,
            username=username or f"user_{telegram_user_id}",
            first_name=first_name or "Test",
            last_name=last_name or f"User{telegram_user_id}",
            role=role,
            is_active=is_active
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    return _create_user


@pytest.fixture
def owner_user(db):
    """Create owner user for testing."""
    user = User(
        telegram_user_id=602720033,
        username="testowner",
        first_name="Test",
        last_name="Owner",
        role="owner",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def operator_user(db):
    """Create operator user for testing."""
    user = User(
        telegram_user_id=123456789,
        username="testoperator",
        first_name="Test",
        last_name="Operator",
        role="operator",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers_owner(owner_user):
    """Generate auth headers for owner."""
    from app.auth.jwt import create_access_token
    token = create_access_token({"user_id": owner_user.id, "role": "owner"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_operator(operator_user):
    """Generate auth headers for operator."""
    from app.auth.jwt import create_access_token
    token = create_access_token({"user_id": operator_user.id, "role": "operator"})
    return {"Authorization": f"Bearer {token}"}
