import pytest
from collections.abc import Callable
from functools import partial
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models
from app.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from tests.factories import (
    TEST_PASSWORD,
    auth_headers,
    create_account,
    create_category,
    create_monthly_record,
    register_and_login,
)


test_engine = create_engine(settings.test_database_url)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()

        if transaction.is_active:
            transaction.rollback()

        connection.close()

@pytest.fixture
def client():
    def override_get_db():
        db: Session = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_factory(client: TestClient) -> Callable[[str], str]:
    """Create and authenticate API users with a caller-provided email."""
    return partial(register_and_login, client)


@pytest.fixture
def user_credentials() -> dict[str, str]:
    return {
        "email": f"fixture-user-{uuid4().hex}@example.com",
        "password": TEST_PASSWORD,
    }


@pytest.fixture
def authenticated_user(
    client: TestClient,
    user_credentials: dict[str, str],
) -> dict[str, object]:
    """Return a ready-to-use user, token, and Authorization headers."""
    token = register_and_login(
        client,
        user_credentials["email"],
        user_credentials["password"],
    )
    return {
        "email": user_credentials["email"],
        "token": token,
        "headers": auth_headers(token),
    }


@pytest.fixture
def account_data() -> dict[str, str]:
    return {"name": "Main card", "type": "card"}


@pytest.fixture
def category_data() -> dict[str, str]:
    return {"name": "Food", "type": "EXPENSE"}


@pytest.fixture
def monthly_record_data() -> dict[str, int | str]:
    return {
        "year": 2026,
        "month": 10,
        "amount": "8500.50",
        "comment": "Test record",
    }


@pytest.fixture
def account_factory(client: TestClient):
    return partial(create_account, client)


@pytest.fixture
def category_factory(client: TestClient):
    return partial(create_category, client)


@pytest.fixture
def monthly_record_factory(client: TestClient):
    return partial(create_monthly_record, client)
