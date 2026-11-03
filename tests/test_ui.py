def register_and_login_ui(client, email: str = "ui@example.com") -> str:
    register_response = client.post(
        "/ui/register",
        data={"email": email, "password": "StrongPassword1!"},
        follow_redirects=False,
    )
    assert register_response.status_code == 303

    login_response = client.post(
        "/ui/login",
        data={"email": email, "password": "StrongPassword1!"},
        follow_redirects=False,
    )
    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/ui/dashboard"
    assert login_response.cookies["access_token"]
    assert "HttpOnly" in login_response.headers["set-cookie"]
    return client.cookies["csrf_token"]


def create_ui_account(client, csrf_token: str, name: str = "Main card") -> None:
    response = client.post(
        "/ui/accounts",
        data={
            "name": name,
            "type": "card",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


def create_ui_category(
    client,
    csrf_token: str,
    name: str = "Salary",
    category_type: str = "INCOME",
) -> None:
    response = client.post(
        "/ui/categories",
        data={
            "name": name,
            "type": category_type,
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_protected_ui_redirects_to_login(client) -> None:
    response = client.get("/ui/dashboard", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"].startswith("/ui/login")


def test_registration_login_dashboard_and_logout(client) -> None:
    csrf_token = register_and_login_ui(client, "ui_auth@example.com")

    dashboard = client.get("/ui/dashboard?year=2026&month=10")
    assert dashboard.status_code == 200
    assert "Financial overview" in dashboard.text
    assert "October 2026" in dashboard.text
    assert "No income yet" in dashboard.text
    assert "Good morning" not in dashboard.text

    logout = client.post(
        "/ui/logout",
        data={"csrf_token": csrf_token},
        follow_redirects=False,
    )
    assert logout.status_code == 303
    assert logout.headers["location"] == "/ui/login"


def test_ui_can_create_and_display_monthly_record(client) -> None:
    csrf_token = register_and_login_ui(client, "ui_records@example.com")
    create_ui_account(client, csrf_token)
    create_ui_category(client, csrf_token)

    account_page = client.get("/ui/accounts")
    category_page = client.get("/ui/categories")
    assert "Main card" in account_page.text
    assert "Salary" in category_page.text

    account_id = account_page.text.split('/ui/accounts/')[1].split('/edit')[0]
    category_id = category_page.text.split('/ui/categories/')[1].split('/edit')[0]

    response = client.post(
        "/ui/monthly-records/new",
        data={
            "account_id": account_id,
            "category_id": category_id,
            "year": "2026",
            "month": "10",
            "amount": "40000.00",
            "comment": "Monthly salary",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    records = client.get("/ui/monthly-records?year=2026&month=10")
    assert records.status_code == 200
    assert "Monthly salary" in records.text
    assert "+40,000.00" in records.text

    dashboard = client.get("/ui/dashboard?year=2026&month=10")
    assert "40,000.00" in dashboard.text
    assert "Salary" in dashboard.text


def test_inactive_items_are_not_offered_for_new_records(client) -> None:
    csrf_token = register_and_login_ui(client, "ui_inactive@example.com")
    create_ui_account(client, csrf_token, "Old account")
    create_ui_category(client, csrf_token, "Old category", "EXPENSE")

    accounts_page = client.get("/ui/accounts")
    categories_page = client.get("/ui/categories")
    account_id = accounts_page.text.split('/ui/accounts/')[1].split('/edit')[0]
    category_id = categories_page.text.split('/ui/categories/')[1].split('/edit')[0]

    client.post(
        f"/ui/accounts/{account_id}/deactivate",
        data={"csrf_token": csrf_token},
    )
    client.post(
        f"/ui/categories/{category_id}/deactivate",
        data={"csrf_token": csrf_token},
    )

    form = client.get("/ui/monthly-records/new?year=2026&month=10")
    assert form.status_code == 200
    assert "Old account" not in form.text
    assert "Old category" not in form.text
    assert "at least one active account" in form.text


def test_ui_can_edit_and_delete_monthly_record(client) -> None:
    csrf_token = register_and_login_ui(client, "ui_record_crud@example.com")
    create_ui_account(client, csrf_token)
    create_ui_category(client, csrf_token, "Food", "EXPENSE")
    account_id = re.search(r"/ui/accounts/(\d+)/edit", client.get("/ui/accounts").text).group(1)
    category_id = re.search(r"/ui/categories/(\d+)/edit", client.get("/ui/categories").text).group(1)

    client.post(
        "/ui/monthly-records/new",
        data={
            "account_id": account_id,
            "category_id": category_id,
            "year": "2026",
            "month": "10",
            "amount": "120.00",
            "comment": "Groceries",
            "csrf_token": csrf_token,
        },
    )
    records = client.get("/ui/monthly-records?year=2026&month=10")
    record_id = re.search(r"/ui/monthly-records/(\d+)/edit", records.text).group(1)

    update = client.post(
        f"/ui/monthly-records/{record_id}/edit",
        data={
            "account_id": account_id,
            "category_id": category_id,
            "year": "2026",
            "month": "10",
            "amount": "150.00",
            "comment": "Groceries corrected",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert update.status_code == 303
    assert "Groceries corrected" in client.get("/ui/monthly-records?year=2026&month=10").text

    delete = client.post(
        f"/ui/monthly-records/{record_id}/delete",
        data={"year": "2026", "month": "10", "csrf_token": csrf_token},
        follow_redirects=False,
    )
    assert delete.status_code == 303
    assert "Groceries corrected" not in client.get("/ui/monthly-records?year=2026&month=10").text


def test_ui_can_edit_accounts_and_categories(client) -> None:
    csrf_token = register_and_login_ui(client, "ui_entity_edit@example.com")
    create_ui_account(client, csrf_token, "Old account name")
    create_ui_category(client, csrf_token, "Old category name", "EXPENSE")
    account_id = re.search(r"/ui/accounts/(\d+)/edit", client.get("/ui/accounts").text).group(1)
    category_id = re.search(r"/ui/categories/(\d+)/edit", client.get("/ui/categories").text).group(1)

    account_update = client.post(
        f"/ui/accounts/{account_id}/edit",
        data={"name": "Everyday card", "type": "card", "csrf_token": csrf_token},
        follow_redirects=False,
    )
    category_update = client.post(
        f"/ui/categories/{category_id}/edit",
        data={"name": "Dining", "type": "EXPENSE", "csrf_token": csrf_token},
        follow_redirects=False,
    )

    assert account_update.status_code == 303
    assert category_update.status_code == 303
    assert "Everyday card" in client.get("/ui/accounts").text
    assert "Dining" in client.get("/ui/categories").text


def test_ui_never_lists_another_users_data(client) -> None:
    first_csrf = register_and_login_ui(client, "ui_owner@example.com")
    create_ui_account(client, first_csrf, "Private account")
    account_id = re.search(r"/ui/accounts/(\d+)/edit", client.get("/ui/accounts").text).group(1)

    client.post("/ui/logout", data={"csrf_token": first_csrf})
    register_and_login_ui(client, "ui_other@example.com")

    response = client.get("/ui/accounts")
    assert response.status_code == 200
    assert "Private account" not in response.text
    assert client.get(f"/ui/accounts/{account_id}/edit").status_code == 404


def test_ui_rejects_missing_csrf_token(client) -> None:
    register_and_login_ui(client, "ui_csrf@example.com")

    response = client.post(
        "/ui/accounts",
        data={"name": "Unsafe", "type": "cash", "csrf_token": "wrong"},
    )

    assert response.status_code == 403
import re


