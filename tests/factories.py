from typing import Any

from fastapi.testclient import TestClient


TEST_PASSWORD = "StrongPassword1!"


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_and_login(
    client: TestClient,
    email: str,
    password: str = TEST_PASSWORD,
) -> str:
    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def create_account(
    client: TestClient,
    token: str,
    name: str = "Monobank",
    account_type: str = "card",
) -> int:
    response = client.post(
        "/accounts",
        headers=auth_headers(token),
        json={"name": name, "type": account_type},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_category(
    client: TestClient,
    token: str,
    name: str = "Food",
    category_type: str = "EXPENSE",
) -> int:
    response = client.post(
        "/categories",
        headers=auth_headers(token),
        json={"name": name, "type": category_type},
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_monthly_record(
    client: TestClient,
    token: str,
    account_id: int,
    category_id: int,
    amount: str = "8500.50",
    year: int = 2026,
    month: int = 10,
    comment: str | None = "Test record",
    **overrides: Any,
):
    payload: dict[str, Any] = {
        "account_id": account_id,
        "category_id": category_id,
        "year": year,
        "month": month,
        "amount": amount,
        "comment": comment,
    }
    payload.update(overrides)

    return client.post(
        "/monthly-records",
        headers=auth_headers(token),
        json=payload,
    )
