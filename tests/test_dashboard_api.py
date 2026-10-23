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
    name: str,
    type: str,
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


def create_record(
    client,
    token: str,
    account_id: int,
    category_id: int,
    amount: str,
    year: int = 2026,
    month: int = 10,
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
        },
    )


def test_monthly_dashboard_totals(client) -> None:
    token = register_and_login(
        client,
        "dashboard_totals@example.com",
    )

    account_id = create_account(client, token)

    salary_id = create_category(
        client,
        token,
        "Salary",
        "INCOME",
    )

    food_id = create_category(
        client,
        token,
        "Food",
        "EXPENSE",
    )

    create_record(
        client,
        token,
        account_id,
        salary_id,
        "40000.00",
    )

    create_record(
        client,
        token,
        account_id,
        food_id,
        "15000.00",
    )

    response = client.get(
        "/dashboard/monthly?year=2026&month=10",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_income"] == "40000.00"
    assert data["total_expenses"] == "15000.00"
    assert data["difference"] == "25000.00"
    assert data["savings_rate"] == "62.50"


def test_dashboard_groups_income_by_category(client) -> None:
    token = register_and_login(
        client,
        "dashboard_income@example.com",
    )

    account_id = create_account(client, token)

    salary_id = create_category(
        client,
        token,
        "Salary",
        "INCOME",
    )

    scholarship_id = create_category(
        client,
        token,
        "Scholarship",
        "INCOME",
    )

    create_record(
        client,
        token,
        account_id,
        salary_id,
        "35000.00",
    )

    create_record(
        client,
        token,
        account_id,
        scholarship_id,
        "5000.00",
    )

    response = client.get(
        "/dashboard/monthly?year=2026&month=10",
        headers=auth_headers(token),
    )

    data = response.json()

    assert len(data["income_by_category"]) == 2

    assert data["income_by_category"][0]["name"] == "Salary"
    assert data["income_by_category"][0]["amount"] == "35000.00"
    assert data["income_by_category"][0]["percentage"] == "87.50"

    assert data["income_by_category"][1]["name"] == "Scholarship"
    assert data["income_by_category"][1]["amount"] == "5000.00"
    assert data["income_by_category"][1]["percentage"] == "12.50"


def test_dashboard_groups_expenses_by_category(client) -> None:
    token = register_and_login(
        client,
        "dashboard_expenses@example.com",
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

    create_record(
        client,
        token,
        account_id,
        food_id,
        "8000.00",
    )

    create_record(
        client,
        token,
        account_id,
        transport_id,
        "2000.00",
    )

    response = client.get(
        "/dashboard/monthly?year=2026&month=10",
        headers=auth_headers(token),
    )

    data = response.json()

    assert len(data["expenses_by_category"]) == 2

    assert data["expenses_by_category"][0]["name"] == "Food"
    assert data["expenses_by_category"][0]["amount"] == "8000.00"
    assert data["expenses_by_category"][0]["percentage"] == "80.00"

    assert data["expenses_by_category"][1]["name"] == "Transport"
    assert data["expenses_by_category"][1]["percentage"] == "20.00"


def test_dashboard_groups_multiple_records_of_same_category(client) -> None:
    token = register_and_login(
        client,
        "dashboard_grouping@example.com",
    )

    account_id = create_account(client, token)

    food_id = create_category(
        client,
        token,
        "Food",
        "EXPENSE",
    )

    create_record(
        client,
        token,
        account_id,
        food_id,
        "5000.00",
    )

    create_record(
        client,
        token,
        account_id,
        food_id,
        "3000.00",
    )

    response = client.get(
        "/dashboard/monthly?year=2026&month=10",
        headers=auth_headers(token),
    )

    data = response.json()

    assert len(data["expenses_by_category"]) == 1
    assert data["expenses_by_category"][0]["name"] == "Food"
    assert data["expenses_by_category"][0]["amount"] == "8000.00"


def test_dashboard_categories_are_sorted_by_amount(client) -> None:
    token = register_and_login(
        client,
        "dashboard_sort@example.com",
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

    entertainment_id = create_category(
        client,
        token,
        "Entertainment",
        "EXPENSE",
    )

    create_record(
        client,
        token,
        account_id,
        transport_id,
        "2000.00",
    )

    create_record(
        client,
        token,
        account_id,
        food_id,
        "8000.00",
    )

    create_record(
        client,
        token,
        account_id,
        entertainment_id,
        "4000.00",
    )

    response = client.get(
        "/dashboard/monthly?year=2026&month=10",
        headers=auth_headers(token),
    )

    categories = response.json()["expenses_by_category"]

    assert categories[0]["name"] == "Food"
    assert categories[1]["name"] == "Entertainment"
    assert categories[2]["name"] == "Transport"


def test_dashboard_filters_by_month(client) -> None:
    token = register_and_login(
        client,
        "dashboard_month@example.com",
    )

    account_id = create_account(client, token)

    salary_id = create_category(
        client,
        token,
        "Salary",
        "INCOME",
    )

    create_record(
        client,
        token,
        account_id,
        salary_id,
        "30000.00",
        month=10,
    )

    create_record(
        client,
        token,
        account_id,
        salary_id,
        "50000.00",
        month=11,
    )

    response = client.get(
        "/dashboard/monthly?year=2026&month=10",
        headers=auth_headers(token),
    )

    assert response.json()["total_income"] == "30000.00"


def test_empty_month_returns_zero_values(client) -> None:
    token = register_and_login(
        client,
        "dashboard_empty@example.com",
    )

    response = client.get(
        "/dashboard/monthly?year=2026&month=12",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_income"] == "0.00"
    assert data["total_expenses"] == "0.00"
    assert data["difference"] == "0.00"
    assert data["savings_rate"] is None
    assert data["income_by_category"] == []
    assert data["expenses_by_category"] == []


def test_dashboard_only_contains_current_users_data(client) -> None:
    first_token = register_and_login(
        client,
        "dashboard_first@example.com",
    )

    second_token = register_and_login(
        client,
        "dashboard_second@example.com",
    )

    first_account_id = create_account(
        client,
        first_token,
        "First account",
    )

    second_account_id = create_account(
        client,
        second_token,
        "Second account",
    )

    first_salary_id = create_category(
        client,
        first_token,
        "Salary",
        "INCOME",
    )

    second_salary_id = create_category(
        client,
        second_token,
        "Salary",
        "INCOME",
    )

    create_record(
        client,
        first_token,
        first_account_id,
        first_salary_id,
        "10000.00",
    )

    create_record(
        client,
        second_token,
        second_account_id,
        second_salary_id,
        "50000.00",
    )

    response = client.get(
        "/dashboard/monthly?year=2026&month=10",
        headers=auth_headers(first_token),
    )

    assert response.status_code == 200
    assert response.json()["total_income"] == "10000.00"