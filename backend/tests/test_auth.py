import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, dev_user):
    response = await client.post(
        "/api/auth/login",
        json={"username": "dev", "password": "dev"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/auth/login",
        json={"username": "dev", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        "/api/auth/login",
        json={"username": "nonexistent", "password": "pass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, dev_user):
    # First login
    login_resp = await client.post(
        "/api/auth/login",
        json={"username": "dev", "password": "dev"},
    )
    refresh_token = login_resp.json()["refresh_token"]
    
    # Refresh
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    response = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": "invalid.token.here"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers, dev_user):
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dev_user.id
    assert data["username"] == "dev"
    assert data["email"] == "dev@localhost"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_unauthenticated_access_denied(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_voice_access_without_auth(client: AsyncClient):
    response = await client.get("/api/voices")
    assert response.status_code == 401