import pytest
from sqlalchemy.exc import IntegrityError

from app.models.category import Category, CategoryType
from app.models.user import User


def test_category_model_creation() -> None:
    category = Category(
        user_id=1,
        name="Salary",
        type=CategoryType.INCOME,
    )

    assert category.user_id == 1
    assert category.name == "Salary"
    assert category.type == CategoryType.INCOME


def test_category_can_be_saved_to_database(db_session) -> None:
    user = User(
        email="category@example.com",
        password_hash="hashed_password",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    category = Category(
        user_id=user.id,
        name="Food",
        type=CategoryType.EXPENSE,
    )

    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    assert category.id is not None
    assert category.user_id == user.id
    assert category.name == "Food"
    assert category.type == CategoryType.EXPENSE
    assert category.is_active is True
    assert category.created_at is not None


def test_category_belongs_to_user(db_session) -> None:
    user = User(
        email="category_relationship@example.com",
        password_hash="hashed_password",
    )

    category = Category(
        name="Scholarship",
        type=CategoryType.INCOME,
    )

    user.categories.append(category)

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert len(user.categories) == 1
    assert user.categories[0].name == "Scholarship"
    assert category.user == user


def test_category_name_and_type_must_be_unique_per_user(db_session) -> None:
    user = User(
        email="category_unique@example.com",
        password_hash="hashed_password",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    first_category = Category(
        user_id=user.id,
        name="Food",
        type=CategoryType.EXPENSE,
    )

    second_category = Category(
        user_id=user.id,
        name="Food",
        type=CategoryType.EXPENSE,
    )

    db_session.add(first_category)
    db_session.commit()

    db_session.add(second_category)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_same_category_name_can_have_different_types(db_session) -> None:
    user = User(
        email="category_types@example.com",
        password_hash="hashed_password",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    income_category = Category(
        user_id=user.id,
        name="Other",
        type=CategoryType.INCOME,
    )

    expense_category = Category(
        user_id=user.id,
        name="Other",
        type=CategoryType.EXPENSE,
    )

    db_session.add_all([income_category, expense_category])
    db_session.commit()

    assert income_category.id is not None
    assert expense_category.id is not None