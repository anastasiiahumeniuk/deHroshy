from app.models.user import User


def test_user_model_creation() -> None:
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
    )

    assert user.email == "test@example.com"
    assert user.password_hash == "hashed_password"


def test_user_can_be_saved_to_database(db_session) -> None:
    user = User(
        email="dbtest@example.com",
        password_hash="hashed_password",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == "dbtest@example.com"
    assert user.created_at is not None