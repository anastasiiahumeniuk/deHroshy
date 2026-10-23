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


def create_account(client, token: str, name: str = "Monobank") -> int:
    response = client.post(
        "/accounts",
        headers=auth_headers(token),
        json={
            "name": name,
            "type": "card",
        },
    )

    return response.json()["id"]


def create_category(
    client,
    token: str,
    name: str = "Food",
    type: str = "EXPENSE",
) -> int:
    response = client.post(
        "/categories",
        headers=auth_headers(token),
        json={
            "name": name,
            "type": type,
        },
    )

    return response.json()["id"]


def create_monthly_record(
    client,
    token: str,
    account_id: int,
    category_id: int,
    year: int = 2026,
    month: int = 10,
    amount: str = "8500.50",
):
    return client.post(
        "/monthly-records",
        headers=auth_headers(token),
        json={
            "account_id": account_id,
            "category_id": category_id,
            "year": year,
            "month": month,
            "amount": amount,
            "comment": "Test record",
        },
    )


def test_create_monthly_record(client) -> None:
    token = register_and_login(
        client,
        "monthly_create@example.com",
    )

    account_id = create_account(client, token)
    category_id = create_category(client, token)

    response = create_monthly_record(
        client,
        token,
        account_id,
        category_id,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["account_id"] == account_id
    assert data["category_id"] == category_id
    assert data["year"] == 2026
    assert data["month"] == 10
    assert data["amount"] == "8500.50"


def test_list_records_for_selected_month(client) -> None:
    token = register_and_login(
        client,
        "monthly_list@example.com",
    )

    account_id = create_account(client, token)
    category_id = create_category(client, token)

    create_monthly_record(
        client,
        token,
        account_id,
        category_id,
        year=2026,
        month=10,
    )

    response = client.get(
        "/monthly-records?year=2026&month=10",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_filter_records_by_account(client) -> None:
    token = register_and_login(
        client,
        "monthly_account_filter@example.com",
    )

    first_account_id = create_account(
        client,
        token,
        "Monobank",
    )

    second_account_id = create_account(
        client,
        token,
        "PrivatBank",
    )

    category_id = create_category(client, token)

    create_monthly_record(
        client,
        token,
        first_account_id,
        category_id,
    )

    create_monthly_record(
        client,
        token,
        second_account_id,
        category_id,
        amount="3000.00",
    )

    response = client.get(
        f"/monthly-records?year=2026&month=10&account_id={first_account_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["account_id"] == first_account_id


def test_filter_records_by_category(client) -> None:
    token = register_and_login(
        client,
        "monthly_category_filter@example.com",
    )

    account_id = create_account(client, token)

    food_id = create_category(
        client,
        token,
        "Food",
        "EXPENSE",
    )

    transport_id = create_category(
        client,
        token,
        "Transport",
        "EXPENSE",
    )

    create_monthly_record(
        client,
        token,
        account_id,
        food_id,
    )

    create_monthly_record(
        client,
        token,
        account_id,
        transport_id,
        amount="1500.00",
    )

    response = client.get(
        f"/monthly-records?year=2026&month=10&category_id={food_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["category_id"] == food_id


def test_filter_records_by_type(client) -> None:
    token = register_and_login(
        client,
        "monthly_type_filter@example.com",
    )

    account_id = create_account(client, token)

    expense_category_id = create_category(
        client,
        token,
        "Food",
        "EXPENSE",
    )

    income_category_id = create_category(
        client,
        token,
        "Salary",
        "INCOME",
    )

    create_monthly_record(
        client,
        token,
        account_id,
        expense_category_id,
        amount="2000.00",
    )

    create_monthly_record(
        client,
        token,
        account_id,
        income_category_id,
        amount="30000.00",
    )

    response = client.get(
        "/monthly-records?year=2026&month=10&type=INCOME",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["category_id"] == income_category_id


def test_update_monthly_record(client) -> None:
    token = register_and_login(
        client,
        "monthly_update@example.com",
    )

    account_id = create_account(client, token)
    category_id = create_category(client, token)

    create_response = create_monthly_record(
        client,
        token,
        account_id,
        category_id,
    )

    record_id = create_response.json()["id"]

    response = client.patch(
        f"/monthly-records/{record_id}",
        headers=auth_headers(token),
        json={
            "amount": "9200.50",
            "comment": "Corrected amount",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["amount"] == "9200.50"
    assert data["comment"] == "Corrected amount"


def test_delete_monthly_record(client) -> None:
    token = register_and_login(
        client,
        "monthly_delete@example.com",
    )

    account_id = create_account(client, token)
    category_id = create_category(client, token)

    create_response = create_monthly_record(
        client,
        token,
        account_id,
        category_id,
    )

    record_id = create_response.json()["id"]

    response = client.delete(
        f"/monthly-records/{record_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204


def test_invalid_amount_is_rejected(client) -> None:
    token = register_and_login(
        client,
        "monthly_amount_validation@example.com",
    )

    account_id = create_account(client, token)
    category_id = create_category(client, token)

    response = create_monthly_record(
        client,
        token,
        account_id,
        category_id,
        amount="-100.00",
    )

    assert response.status_code == 422


def test_invalid_month_is_rejected(client) -> None:
    token = register_and_login(
        client,
        "monthly_month_validation@example.com",
    )

    account_id = create_account(client, token)
    category_id = create_category(client, token)

    response = create_monthly_record(
        client,
        token,
        account_id,
        category_id,
        month=13,
    )

    assert response.status_code == 422


def test_user_cannot_create_record_with_another_users_account(client) -> None:
    first_token = register_and_login(
        client,
        "monthly_owner@example.com",
    )

    second_token = register_and_login(
        client,
        "monthly_other@example.com",
    )

    first_account_id = create_account(
        client,
        first_token,
    )

    second_category_id = create_category(
        client,
        second_token,
    )

    response = create_monthly_record(
        client,
        second_token,
        first_account_id,
        second_category_id,
    )

    assert response.status_code == 404


def test_user_cannot_update_another_users_record(client) -> None:
    first_token = register_and_login(
        client,
        "monthly_record_owner@example.com",
    )

    second_token = register_and_login(
        client,
        "monthly_record_other@example.com",
    )

    account_id = create_account(
        client,
        first_token,
    )

    category_id = create_category(
        client,
        first_token,
    )

    create_response = create_monthly_record(
        client,
        first_token,
        account_id,
        category_id,
    )

    record_id = create_response.json()["id"]

    response = client.patch(
        f"/monthly-records/{record_id}",
        headers=auth_headers(second_token),
        json={
            "amount": "100.00",
        },
    )

    assert response.status_code == 404


def test_user_cannot_delete_another_users_record(client) -> None:
    first_token = register_and_login(
        client,
        "monthly_delete_owner@example.com",
    )

    second_token = register_and_login(
        client,
        "monthly_delete_other@example.com",
    )

    account_id = create_account(
        client,
        first_token,
    )

    category_id = create_category(
        client,
        first_token,
    )

    create_response = create_monthly_record(
        client,
        first_token,
        account_id,
        category_id,
    )

    record_id = create_response.json()["id"]

    response = client.delete(
        f"/monthly-records/{record_id}",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 404