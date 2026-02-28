import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user_endpoint(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/users",
        json={"email": "ep_user@example.com", "password": "secret123", "full_name": "EP User"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "ep_user@example.com"
    assert data["full_name"] == "EP User"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_user_duplicate(client: AsyncClient) -> None:
    payload = {"email": "dup_ep@example.com", "password": "secret123"}
    await client.post("/api/v1/users", json=payload)
    response = await client.post("/api/v1/users", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_user_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_user_not_found_with_auth(client: AsyncClient) -> None:
    # Create a user and authenticate
    await client.post(
        "/api/v1/users",
        json={"email": "auth_ep@example.com", "password": "secret123"},
    )
    token_response = await client.post(
        "/api/v1/auth/token",
        data={"username": "auth_ep@example.com", "password": "secret123"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/users/99999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_users_with_auth(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/users",
        json={"email": "list_ep@example.com", "password": "secret123"},
    )
    token_response = await client.post(
        "/api/v1/auth/token",
        data={"username": "list_ep@example.com", "password": "secret123"},
    )
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/users?page=1&limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data


@pytest.mark.asyncio
async def test_delete_user_with_auth(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/users",
        json={"email": "del_ep@example.com", "password": "secret123"},
    )
    user_id = create_resp.json()["id"]

    token_response = await client.post(
        "/api/v1/auth/token",
        data={"username": "del_ep@example.com", "password": "secret123"},
    )
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert response.status_code == 204
