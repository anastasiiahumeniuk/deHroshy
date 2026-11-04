from tests.factories import (
    auth_headers,
    create_account,
    create_category,
    create_monthly_record,
    register_and_login,
)


def test_create_monthly_record(
    authenticated_user,
    account_factory,
    category_factory,
    monthly_record_factory,
    monthly_record_data,
) -> None:
    token = authenticated_user["token"]
    account_id = account_factory(token)
    category_id = category_factory(token)

    response = monthly_record_factory(
        token,
        account_id,
        category_id,
        **monthly_record_data,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["account_id"] == account_id
    assert data["category_id"] == category_id
    assert data["year"] == monthly_record_data["year"]
    assert data["month"] == monthly_record_data["month"]
    assert data["amount"] == monthly_record_data["amount"]


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


def test_amount_with_comma_and_whitespace_is_normalized(client) -> None:
    token = register_and_login(
        client,
        "monthly_comma_amount@example.com",
    )

    account_id = create_account(client, token)
    category_id = create_category(client, token)

    response = create_monthly_record(
        client,
        token,
        account_id,
        category_id,
        amount=" 8500,50 ",
    )

    assert response.status_code == 201
    assert response.json()["amount"] == "8500.50"


def test_invalid_amount_formats_are_rejected(client) -> None:
    token = register_and_login(
        client,
        "monthly_invalid_amount_format@example.com",
    )

    account_id = create_account(client, token)
    category_id = create_category(client, token)

    for amount in (
        "12abc",
        "1,000.50",
        "1.000,50",
        "10,999",
        "100.999",
        "",
    ):
        response = create_monthly_record(
            client,
            token,
            account_id,
            category_id,
            amount=amount,
        )

        assert response.status_code == 422
        assert "Amount must be a positive number" in response.text


def test_comment_whitespace_is_normalized(client) -> None:
    token = register_and_login(
        client,
        "monthly_comment_normalized@example.com",
    )
    account_id = create_account(client, token)
    category_id = create_category(client, token)

    response = create_monthly_record(
        client,
        token,
        account_id,
        category_id,
        comment="  Monthly   salary\nfor October  ",
    )

    assert response.status_code == 201
    assert response.json()["comment"] == "Monthly salary for October"


def test_blank_comment_is_stored_as_none(client) -> None:
    token = register_and_login(
        client,
        "monthly_blank_comment@example.com",
    )
    account_id = create_account(client, token)
    category_id = create_category(client, token)

    response = create_monthly_record(
        client,
        token,
        account_id,
        category_id,
        comment="   ",
    )

    assert response.status_code == 201
    assert response.json()["comment"] is None


def test_comment_length_is_limited(client) -> None:
    token = register_and_login(
        client,
        "monthly_long_comment@example.com",
    )
    account_id = create_account(client, token)
    category_id = create_category(client, token)

    response = create_monthly_record(
        client,
        token,
        account_id,
        category_id,
        comment="a" * 501,
    )

    assert response.status_code == 422


def test_record_ids_must_be_positive(client) -> None:
    token = register_and_login(
        client,
        "monthly_positive_ids@example.com",
    )

    response = client.post(
        "/monthly-records",
        headers=auth_headers(token),
        json={
            "account_id": 0,
            "category_id": -1,
            "year": 2026,
            "month": 10,
            "amount": "100.00",
        },
    )

    assert response.status_code == 422


def test_blank_comment_clears_existing_comment(client) -> None:
    token = register_and_login(
        client,
        "monthly_clear_comment@example.com",
    )
    account_id = create_account(client, token)
    category_id = create_category(client, token)
    create_response = create_monthly_record(
        client,
        token,
        account_id,
        category_id,
        comment="Original comment",
    )
    record_id = create_response.json()["id"]

    response = client.patch(
        f"/monthly-records/{record_id}",
        headers=auth_headers(token),
        json={"comment": "   "},
    )

    assert response.status_code == 200
    assert response.json()["comment"] is None


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
