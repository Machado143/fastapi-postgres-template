import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/users",
        json={"email": "auth_login@example.com", "password": "secret123"},
    )
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "auth_login@example.com", "password": "secret123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/users",
        json={"email": "auth_wrong@example.com", "password": "correct"},
    )
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "auth_wrong@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "nobody@example.com", "password": "whatever"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/users",
        json={"email": "auth_me@example.com", "password": "secret123", "full_name": "Me User"},
    )
    token_response = await client.post(
        "/api/v1/auth/token",
        data={"username": "auth_me@example.com", "password": "secret123"},
    )
    token = token_response.json()["access_token"]
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "auth_me@example.com"
    assert data["full_name"] == "Me User"


@pytest.mark.asyncio
async def test_protected_route_no_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401
