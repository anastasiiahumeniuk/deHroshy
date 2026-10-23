def register_and_login(client, email: str) -> str:
    password = "strong_password"

    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}"
    }


def test_create_account(client) -> None:
    token = register_and_login(
        client,
        "account_create@example.com",
    )

    response = client.post(
        "/accounts",
        headers=auth_headers(token),
        json={
            "name": "Monobank",
            "type": "card",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Monobank"
    assert data["type"] == "card"
    assert data["is_active"] is True


def test_list_accounts(client) -> None:
    token = register_and_login(
        client,
        "account_list@example.com",
    )

    client.post(
        "/accounts",
        headers=auth_headers(token),
        json={
            "name": "Monobank",
            "type": "card",
        },
    )

    client.post(
        "/accounts",
        headers=auth_headers(token),
        json={
            "name": "Cash",
            "type": "cash",
        },
    )

    response = client.get(
        "/accounts",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


def test_get_account(client) -> None:
    token = register_and_login(
        client,
        "account_get@example.com",
    )

    create_response = client.post(
        "/accounts",
        headers=auth_headers(token),
        json={
            "name": "Monobank",
            "type": "card",
        },
    )

    account_id = create_response.json()["id"]

    response = client.get(
        f"/accounts/{account_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Monobank"


def test_update_account(client) -> None:
    token = register_and_login(
        client,
        "account_update@example.com",
    )

    create_response = client.post(
        "/accounts",
        headers=auth_headers(token),
        json={
            "name": "Monobank",
            "type": "card",
        },
    )

    account_id = create_response.json()["id"]

    response = client.patch(
        f"/accounts/{account_id}",
        headers=auth_headers(token),
        json={
            "name": "Main Monobank",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Main Monobank"


def test_deactivate_account(client) -> None:
    token = register_and_login(
        client,
        "account_deactivate@example.com",
    )

    create_response = client.post(
        "/accounts",
        headers=auth_headers(token),
        json={
            "name": "Cash",
            "type": "cash",
        },
    )

    account_id = create_response.json()["id"]

    response = client.patch(
        f"/accounts/{account_id}/deactivate",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_user_cannot_access_another_users_account(client) -> None:
    first_token = register_and_login(
        client,
        "account_owner@example.com",
    )

    second_token = register_and_login(
        client,
        "account_other@example.com",
    )

    create_response = client.post(
        "/accounts",
        headers=auth_headers(first_token),
        json={
            "name": "Private account",
            "type": "card",
        },
    )

    account_id = create_response.json()["id"]

    response = client.get(
        f"/accounts/{account_id}",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 404


def test_create_account_requires_authentication(client) -> None:
    response = client.post(
        "/accounts",
        json={
            "name": "Monobank",
            "type": "card",
        },
    )

    assert response.status_code == 401


def test_account_name_validation(client) -> None:
    token = register_and_login(
        client,
        "account_validation@example.com",
    )

    response = client.post(
        "/accounts",
        headers=auth_headers(token),
        json={
            "name": "",
            "type": "card",
        },
    )

    assert response.status_code == 422