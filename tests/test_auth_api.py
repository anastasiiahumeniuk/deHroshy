import pytest

def test_register_user(client) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "StrongPassword1!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "newuser@example.com"
    assert "id" in data


def test_login_user(client) -> None:
    client.post(
        "/auth/register",
        json={
            "email": "loginuser@example.com",
            "password": "StrongPassword1!",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "loginuser@example.com",
            "password": "StrongPassword1!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_wrong_password(client) -> None:
    client.post(
        "/auth/register",
        json={
            "email": "wrongpassword@example.com",
            "password": "CorrectPassword1!",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "wrongpassword@example.com",
            "password": "WrongPassword1!",
        },
    )

    assert response.status_code == 401

def test_invalid_email_is_rejected(client) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "StrongPassword1!",
        },
    )

    assert response.status_code == 422


def test_email_is_normalized(client) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "  Normalized@Example.COM  ",
            "password": "StrongPassword1!",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "normalized@example.com"


@pytest.mark.parametrize(
    "password",
    [
        "Short1!",
        "lowercase1!",
        "UPPERCASE1!",
        "NoNumbers!",
        "NoSpecial1",
        "With Space1!",
    ],
)
def test_weak_password_is_rejected(
    client,
    password: str,
    ) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": f"weak-{password.replace(' ', '-')}@example.com",
            "password": password,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]
