import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from app.models.account import Account
from app.models.category import Category, CategoryType
from app.models.monthly_record import MonthlyRecord
from app.models.user import User


def create_test_data(db_session):
    user = User(
        email="monthly@example.com",
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

    category = Category(
        user_id=user.id,
        name="Food",
        type=CategoryType.EXPENSE,
    )

    db_session.add_all([account, category])
    db_session.commit()

    db_session.refresh(account)
    db_session.refresh(category)

    return user, account, category


def test_monthly_record_model_creation() -> None:
    record = MonthlyRecord(
        user_id=1,
        account_id=1,
        category_id=1,
        year=2026,
        month=10,
        amount=Decimal("8500.50"),
        comment="Food expenses",
    )

    assert record.user_id == 1
    assert record.account_id == 1
    assert record.category_id == 1
    assert record.year == 2026
    assert record.month == 10
    assert record.amount == Decimal("8500.50")
    assert record.comment == "Food expenses"


def test_monthly_record_can_be_saved_to_database(db_session) -> None:
    user, account, category = create_test_data(db_session)

    record = MonthlyRecord(
        user_id=user.id,
        account_id=account.id,
        category_id=category.id,
        year=2026,
        month=10,
        amount=Decimal("8500.50"),
        comment="October food expenses",
    )

    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    assert record.id is not None
    assert record.amount == Decimal("8500.50")
    assert record.created_at is not None
    assert record.updated_at is not None


def test_monthly_record_relationships(db_session) -> None:
    user, account, category = create_test_data(db_session)

    record = MonthlyRecord(
        user_id=user.id,
        account_id=account.id,
        category_id=category.id,
        year=2026,
        month=10,
        amount=Decimal("1000.00"),
    )

    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    assert record.user == user
    assert record.account == account
    assert record.category == category


def test_monthly_record_amount_must_be_positive(db_session) -> None:
    user, account, category = create_test_data(db_session)

    record = MonthlyRecord(
        user_id=user.id,
        account_id=account.id,
        category_id=category.id,
        year=2026,
        month=10,
        amount=Decimal("-100.00"),
    )

    db_session.add(record)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_monthly_record_month_must_be_valid(db_session) -> None:
    user, account, category = create_test_data(db_session)

    record = MonthlyRecord(
        user_id=user.id,
        account_id=account.id,
        category_id=category.id,
        year=2026,
        month=13,
        amount=Decimal("100.00"),
    )

    db_session.add(record)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_monthly_record_year_must_be_positive(db_session) -> None:
    user, account, category = create_test_data(db_session)

    record = MonthlyRecord(
        user_id=user.id,
        account_id=account.id,
        category_id=category.id,
        year=0,
        month=10,
        amount=Decimal("100.00"),
    )

    db_session.add(record)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()