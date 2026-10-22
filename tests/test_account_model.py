import pytest
from sqlalchemy.exc import IntegrityError

from app.models.account import Account
from app.models.user import User


def test_account_model_creation() -> None:
    account = Account(
        user_id=1,
        name="Monobank",
        type="card",
    )

    assert account.user_id == 1
    assert account.name == "Monobank"
    assert account.type == "card"


def test_account_can_be_saved_to_database(db_session) -> None:
    user = User(
        email="account@example.com",
        password_hash="hashed_password",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    account = Account(
        user_id=user.id,
        name="Monobank",
        type="card",
    )

    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    assert account.id is not None
    assert account.user_id == user.id
    assert account.name == "Monobank"
    assert account.type == "card"
    assert account.is_active is True
    assert account.created_at is not None


def test_account_belongs_to_user(db_session) -> None:
    user = User(
        email="relationship@example.com",
        password_hash="hashed_password",
    )

    account = Account(
        name="Cash",
        type="cash",
    )

    user.accounts.append(account)

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert len(user.accounts) == 1
    assert user.accounts[0].name == "Cash"
    assert account.user == user


def test_account_name_must_be_unique_per_user(db_session) -> None:
    user = User(
        email="unique@example.com",
        password_hash="hashed_password",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    first_account = Account(
        user_id=user.id,
        name="Monobank",
        type="card",
    )

    second_account = Account(
        user_id=user.id,
        name="Monobank",
        type="card",
    )

    db_session.add(first_account)
    db_session.commit()

    db_session.add(second_account)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()