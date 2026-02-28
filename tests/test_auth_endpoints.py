import pytest
from datetime import timedelta
from httpx import AsyncClient

from app.core.security import create_access_token
from tests.conftest import TEST_PASSWORD


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/users",
        json={"email": "auth_login@example.com", "password": TEST_PASSWORD},
    )
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "auth_login@example.com", "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/users",
        json={"email": "auth_wrong@example.com", "password": TEST_PASSWORD},
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
        data={"username": "nobody@example.com", "password": TEST_PASSWORD},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/users",
        json={
            "email": "auth_me@example.com",
            "password": TEST_PASSWORD,
            "full_name": "Me User",
        },
    )
    token_response = await client.post(
        "/api/v1/auth/token",
        data={"username": "auth_me@example.com", "password": TEST_PASSWORD},
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


@pytest.mark.asyncio
async def test_expired_token_returns_401(client: AsyncClient) -> None:
    """A token with negative expiry must be rejected with 401."""
    expired_token = create_access_token(
        subject=9999, expires_delta=timedelta(seconds=-1)
    )
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_returns_401(client: AsyncClient) -> None:
    """Deactivated users must not be able to authenticate."""
    await client.post(
        "/api/v1/users",
        json={"email": "inactive@example.com", "password": TEST_PASSWORD},
    )
    # get a superuser token to deactivate the user
    su_token_resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "inactive@example.com", "password": TEST_PASSWORD},
    )
    token = su_token_resp.json()["access_token"]

    # find user id
    me_resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = me_resp.json()["id"]

    # deactivate via update (requires auth — use same token, still valid)
    await client.patch(
        f"/api/v1/users/{user_id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )

    # now token should be rejected because user is inactive
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
