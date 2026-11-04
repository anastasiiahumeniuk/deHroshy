from tests.factories import auth_headers, register_and_login


def test_create_category(client, authenticated_user, category_data) -> None:
    response = client.post(
        "/categories",
        headers=authenticated_user["headers"],
        json=category_data,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == category_data["name"]
    assert data["type"] == category_data["type"]
    assert data["is_active"] is True


def test_list_categories(client) -> None:
    token = register_and_login(
        client,
        "category_list@example.com",
    )

    client.post(
        "/categories",
        headers=auth_headers(token),
        json={
            "name": "Salary",
            "type": "INCOME",
        },
    )

    client.post(
        "/categories",
        headers=auth_headers(token),
        json={
            "name": "Food",
            "type": "EXPENSE",
        },
    )

    response = client.get(
        "/categories",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_filter_categories_by_type(client) -> None:
    token = register_and_login(
        client,
        "category_filter@example.com",
    )

    client.post(
        "/categories",
        headers=auth_headers(token),
        json={
            "name": "Salary",
            "type": "INCOME",
        },
    )

    client.post(
        "/categories",
        headers=auth_headers(token),
        json={
            "name": "Food",
            "type": "EXPENSE",
        },
    )

    response = client.get(
        "/categories?type=INCOME",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Salary"
    assert data[0]["type"] == "INCOME"


def test_update_category(client) -> None:
    token = register_and_login(
        client,
        "category_update@example.com",
    )

    create_response = client.post(
        "/categories",
        headers=auth_headers(token),
        json={
            "name": "Salary",
            "type": "INCOME",
        },
    )

    category_id = create_response.json()["id"]

    response = client.patch(
        f"/categories/{category_id}",
        headers=auth_headers(token),
        json={
            "name": "Main salary",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Main salary"


def test_deactivate_category(client) -> None:
    token = register_and_login(
        client,
        "category_deactivate@example.com",
    )

    create_response = client.post(
        "/categories",
        headers=auth_headers(token),
        json={
            "name": "Food",
            "type": "EXPENSE",
        },
    )

    category_id = create_response.json()["id"]

    response = client.patch(
        f"/categories/{category_id}/deactivate",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_invalid_category_type_is_rejected(client) -> None:
    token = register_and_login(
        client,
        "category_invalid@example.com",
    )

    response = client.post(
        "/categories",
        headers=auth_headers(token),
        json={
            "name": "Salary",
            "type": "SALARY",
        },
    )

    assert response.status_code == 422


def test_category_name_is_normalized(client) -> None:
    token = register_and_login(
        client,
        "category_normalized@example.com",
    )

    response = client.post(
        "/categories",
        headers=auth_headers(token),
        json={"name": "  Food   and Dining  ", "type": "EXPENSE"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Food and Dining"


def test_invalid_category_name_characters_are_rejected(client) -> None:
    token = register_and_login(
        client,
        "category_invalid_characters@example.com",
    )

    for name in ("<script>", "Food🍕", "Food_Category", "@@@", "   "):
        response = client.post(
            "/categories",
            headers=auth_headers(token),
            json={"name": name, "type": "EXPENSE"},
        )

        assert response.status_code == 422
        assert "Category name" in response.text


def test_category_update_name_is_normalized(client) -> None:
    token = register_and_login(
        client,
        "category_update_normalized@example.com",
    )
    create_response = client.post(
        "/categories",
        headers=auth_headers(token),
        json={"name": "Food", "type": "EXPENSE"},
    )
    category_id = create_response.json()["id"]

    response = client.patch(
        f"/categories/{category_id}",
        headers=auth_headers(token),
        json={"name": "  Restaurants   and Cafes  "},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Restaurants and Cafes"


def test_duplicate_category_is_rejected(client) -> None:
    token = register_and_login(
        client,
        "category_duplicate@example.com",
    )

    category = {
        "name": "Food",
        "type": "EXPENSE",
    }

    first_response = client.post(
        "/categories",
        headers=auth_headers(token),
        json=category,
    )

    second_response = client.post(
        "/categories",
        headers=auth_headers(token),
        json=category,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_user_cannot_update_another_users_category(client) -> None:
    first_token = register_and_login(
        client,
        "category_owner@example.com",
    )

    second_token = register_and_login(
        client,
        "category_other@example.com",
    )

    create_response = client.post(
        "/categories",
        headers=auth_headers(first_token),
        json={
            "name": "Private category",
            "type": "EXPENSE",
        },
    )

    category_id = create_response.json()["id"]

    response = client.patch(
        f"/categories/{category_id}",
        headers=auth_headers(second_token),
        json={
            "name": "Changed",
        },
    )

    assert response.status_code == 404


def test_duplicate_category_is_rejected_on_update(client) -> None:
    token = register_and_login(client, "category_duplicate_update@example.com")
    first_id = client.post(
        "/categories",
        headers=auth_headers(token),
        json={"name": "First category", "type": "EXPENSE"},
    ).json()["id"]
    client.post(
        "/categories",
        headers=auth_headers(token),
        json={"name": "Second category", "type": "EXPENSE"},
    )

    response = client.patch(
        f"/categories/{first_id}",
        headers=auth_headers(token),
        json={"name": "Second category"},
    )

    assert response.status_code == 409


def test_user_cannot_deactivate_another_users_category(client) -> None:
    owner_token = register_and_login(client, "category_deactivate_owner@example.com")
    other_token = register_and_login(client, "category_deactivate_other@example.com")
    category_id = client.post(
        "/categories",
        headers=auth_headers(owner_token),
        json={"name": "Owner category", "type": "EXPENSE"},
    ).json()["id"]

    response = client.patch(
        f"/categories/{category_id}/deactivate",
        headers=auth_headers(other_token),
    )

    assert response.status_code == 404
