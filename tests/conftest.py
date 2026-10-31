"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import os
import sys
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ENVIRONMENT"] = "testing"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.database as src_database  # noqa: E402
from src.config import settings  # noqa: E402
from src.main import app  # noqa: E402
from src.models import Account, AccountType, Company, User  # noqa: E402


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    src_database.engine = engine
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def reset_database(test_engine):
    """Clean up after each test."""
    yield
    with test_engine.connect() as conn:
        for table in reversed(SQLModel.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


@pytest.fixture(scope="function")
def db_session(test_engine):
    session = Session(test_engine)
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def client(test_engine):
    """Provide a TestClient that uses the in-memory SQLite database."""
    from src.core.middleware import get_db

    def override_get_db():
        with Session(test_engine) as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def test_company(db_session):
    company = Company(name="Test Company", slug=f"test-company-{uuid4().hex[:8]}", currency="USD")
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def test_user(db_session, test_company):
    from src.core.security import get_password_hash

    user = User(
        company_id=test_company.id,
        email=f"user-{uuid4().hex[:8]}@example.com",
        name="Test User",
        role="owner",
        password_hash=get_password_hash("Password123"),
        is_verified=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_accounts(db_session, test_company):
    accounts = []
    for code, name, atype in [
        ("1000", "Cash", AccountType.ASSET),
        ("1010", "Accounts Receivable", AccountType.ASSET),
        ("1200", "Accounts Payable", AccountType.LIABILITY),
        ("2000", "Tax Payable", AccountType.LIABILITY),
        ("3000", "Sales Revenue", AccountType.REVENUE),
        ("4000", "Expenses", AccountType.EXPENSE),
    ]:
        acct = Account(
            company_id=test_company.id,
            code=code,
            name=name,
            type=atype,
            is_system=True,
        )
        db_session.add(acct)
        accounts.append(acct)
    db_session.commit()
    return accounts


@pytest.fixture
def auth_user(client):
    """Create a test user via signup and return credentials."""
    unique = uuid4().hex[:8]
    email = f"signup-{unique}@example.com"
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "name": "Signup Test",
            "password": "Password123",
            "company_name": "Test Company",
            "company_slug": f"test-company-{unique}",
            "role": "owner",
        },
    )
    token = response.json()["access_token"]
    return {"email": email, "password": "Password123", "access_token": token}


@pytest.fixture
def auth_headers(auth_user):
    return {"Authorization": f"Bearer {auth_user['access_token']}"}
