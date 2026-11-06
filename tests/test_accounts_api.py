from tests.factories import auth_headers, register_and_login


def test_create_account(client, authenticated_user, account_data) -> None:
    response = client.post(
        "/accounts",
        headers=authenticated_user["headers"],
        json=account_data,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == account_data["name"]
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


def test_account_fields_are_normalized(client) -> None:
    token = register_and_login(
        client,
        "account_normalized@example.com",
    )

    response = client.post(
        "/accounts",
        headers=auth_headers(token),
        json={
            "name": "  Main   Card  ",
            "type": "  CREDIT   CARD  ",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Main Card"
    assert response.json()["type"] == "credit card"


def test_invalid_account_characters_are_rejected(client) -> None:
    token = register_and_login(
        client,
        "account_invalid_characters@example.com",
    )

    for name in ("<script>", "Wallet💳", "Card_One", "@@@", "   "):
        response = client.post(
            "/accounts",
            headers=auth_headers(token),
            json={"name": name, "type": "card"},
        )

        assert response.status_code == 422
        assert "Account name" in response.text


def test_invalid_account_type_characters_are_rejected(client) -> None:
    token = register_and_login(
        client,
        "account_invalid_type@example.com",
    )

    response = client.post(
        "/accounts",
        headers=auth_headers(token),
        json={"name": "Main card", "type": "card@home"},
    )

    assert response.status_code == 422
    assert "Account type" in response.text


def test_account_update_is_normalized(client) -> None:
    token = register_and_login(
        client,
        "account_update_normalized@example.com",
    )
    create_response = client.post(
        "/accounts",
        headers=auth_headers(token),
        json={"name": "Main card", "type": "card"},
    )
    account_id = create_response.json()["id"]

    response = client.patch(
        f"/accounts/{account_id}",
        headers=auth_headers(token),
        json={"name": "  Travel   Card  ", "type": "  BANK  "},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Travel Card"
    assert response.json()["type"] == "bank"


def test_duplicate_normalized_account_name_is_rejected(client) -> None:
    token = register_and_login(
        client,
        "account_duplicate_normalized@example.com",
    )

    first_response = client.post(
        "/accounts",
        headers=auth_headers(token),
        json={"name": "Main Card", "type": "card"},
    )
    second_response = client.post(
        "/accounts",
        headers=auth_headers(token),
        json={"name": "  Main   Card  ", "type": "cash"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Account with this name already exists"


def test_duplicate_account_name_is_rejected_on_update(client) -> None:
    token = register_and_login(client, "account_duplicate_update@example.com")
    first_id = client.post(
        "/accounts",
        headers=auth_headers(token),
        json={"name": "First account", "type": "card"},
    ).json()["id"]
    client.post(
        "/accounts",
        headers=auth_headers(token),
        json={"name": "Second account", "type": "cash"},
    )

    response = client.patch(
        f"/accounts/{first_id}",
        headers=auth_headers(token),
        json={"name": "Second account"},
    )

    assert response.status_code == 409


def test_user_cannot_update_or_deactivate_another_users_account(client) -> None:
    owner_token = register_and_login(client, "account_mutation_owner@example.com")
    other_token = register_and_login(client, "account_mutation_other@example.com")
    account_id = client.post(
        "/accounts",
        headers=auth_headers(owner_token),
        json={"name": "Owner account", "type": "card"},
    ).json()["id"]

    update_response = client.patch(
        f"/accounts/{account_id}",
        headers=auth_headers(other_token),
        json={"name": "Stolen account"},
    )
    deactivate_response = client.patch(
        f"/accounts/{account_id}/deactivate",
        headers=auth_headers(other_token),
    )

    assert update_response.status_code == 404
    assert deactivate_response.status_code == 404


def test_creating_inactive_account_again_reactivates_it(client) -> None:
    token = register_and_login(client, "account_reactivate@example.com")
    headers = auth_headers(token)
    first = client.post(
        "/accounts",
        headers=headers,
        json={"name": "Cash", "type": "cash"},
    )
    account_id = first.json()["id"]
    client.patch(f"/accounts/{account_id}/deactivate", headers=headers)

    response = client.post(
        "/accounts",
        headers=headers,
        json={"name": "Cash", "type": "wallet"},
    )

    assert response.status_code == 201
    assert response.json()["id"] == account_id
    assert response.json()["is_active"] is True
    assert response.json()["type"] == "wallet"
