import jwt

from app.config import settings
from app.core.security import create_access_token
from app.core.security import hash_password, verify_password

def test_hash_password() -> None:
    password = "secure_password"

    hashed_password = hash_password(password)

    assert hashed_password != password


def test_verify_correct_password() -> None:
    password = "secure_password"
    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password) is True


def test_verify_wrong_password() -> None:
    hashed_password = hash_password("correct_password")

    assert verify_password(
        "wrong_password",
        hashed_password,
    ) is False


def test_create_access_token() -> None:
    token = create_access_token("1")

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == "1"
    assert "exp" in payload