"""
Tests for JWT token refresh and logout flows.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.user import User
from app.services.auth import hash_password


@pytest.fixture
async def auth_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


async def _register_and_login(client: AsyncClient, unique_id: str) -> dict:
    email = f"tokens-{unique_id}@example.com"
    password = "StrongPass123!"
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "display_name": f"Token User {unique_id}",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    return {"email": email, "password": password, "resp": resp}


@pytest.mark.asyncio
async def test_refresh_token_success(auth_client: AsyncClient):
    uid = uuid.uuid4().hex[:8]
    result = await _register_and_login(auth_client, uid)
    assert result["resp"].status_code == 200

    # The refresh_token cookie should have been set by login
    resp = await auth_client.post("/api/v1/auth/refresh")
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Token refreshed"

    # New access_token cookie should be set
    assert "access_token" in auth_client.cookies

    # Cleanup
    user = await User.find_one({"email": result["email"]})
    if user:
        await user.delete()


@pytest.mark.asyncio
async def test_refresh_token_missing_returns_401(auth_client: AsyncClient):
    """Calling /refresh with no cookie should fail with 401."""
    fresh_client = AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    )
    async with fresh_client as ac:
        resp = await ac.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_clears_cookies(auth_client: AsyncClient):
    uid = uuid.uuid4().hex[:8]
    result = await _register_and_login(auth_client, uid)
    assert result["resp"].status_code == 200

    resp = await auth_client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Logged out"

    # After logout, refresh should fail (token revoked)
    resp2 = await auth_client.post("/api/v1/auth/refresh")
    assert resp2.status_code == 401

    # Cleanup
    user = await User.find_one({"email": result["email"]})
    if user:
        await user.delete()


@pytest.mark.asyncio
async def test_logout_without_token_is_noop(auth_client: AsyncClient):
    """Logout without an active session should still return 200."""
    fresh_client = AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    )
    async with fresh_client as ac:
        resp = await ac.post("/api/v1/auth/logout")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        ac.cookies.set("refresh_token", "totally.invalid.token")
        resp = await ac.post("/api/v1/auth/refresh")
    assert resp.status_code == 401
