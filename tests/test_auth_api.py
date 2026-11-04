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


def test_duplicate_registration_is_rejected(client) -> None:
    payload = {
        "email": "duplicate-auth@example.com",
        "password": "StrongPassword1_",
    }

    first_response = client.post("/auth/register", json=payload)
    second_response = client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_get_current_user(client, authenticated_user) -> None:
    response = client.get(
        "/auth/me",
        headers=authenticated_user["headers"],
    )

    assert response.status_code == 200
    assert response.json()["email"] == authenticated_user["email"]


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


@pytest.mark.parametrize(
    "password",
    [
        "StrongPassword1_",
        "StrongPassword1.",
        "StrongPassword1-",
        "StrongPassword1?",
        "StrongPassword1+",
    ],
)
def test_different_special_characters_are_accepted(
    client,
    password: str,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": f"special-{ord(password[-1])}@example.com",
            "password": password,
        },
    )

    assert response.status_code == 201
