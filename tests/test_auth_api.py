def test_register_user(client) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "strong_password",
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
            "password": "strong_password",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "loginuser@example.com",
            "password": "strong_password",
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
            "password": "correct_password",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "wrongpassword@example.com",
            "password": "wrong_password",
        },
    )

    assert response.status_code == 401