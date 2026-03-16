"""Tests for /api/v1/auth endpoints."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.services.auth import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _override_db(session: AsyncSession):
    async def _get():
        yield session
    return _get


@pytest.fixture
async def auth_client(db_session: AsyncSession):
    """Client with only db overridden -- no auth override (we test login/register)."""
    app.dependency_overrides[get_db] = _override_db(db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_success(auth_client: AsyncClient):
    resp = await auth_client.post("/api/v1/auth/register", json={
        "email": f"new-{uuid.uuid4().hex[:8]}@example.com",
        "password": "Str0ngP@ss!",
        "display_name": "New User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["display_name"] == "New User"
    # Should set cookies
    assert "access_token" in resp.cookies
    assert "refresh_token" in resp.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email(db_session: AsyncSession, auth_client: AsyncClient):
    email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=email,
        display_name="Existing",
        password_hash=hash_password("pass"),
        email_verified=False,
    )
    db_session.add(user)
    await db_session.flush()

    resp = await auth_client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "AnotherP@ss1",
        "display_name": "Dup User",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_email(auth_client: AsyncClient):
    resp = await auth_client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "abc",
        "display_name": "Bad",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success(db_session: AsyncSession, auth_client: AsyncClient):
    email = f"login-{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=email,
        display_name="Login User",
        password_hash=hash_password("MyPassword1!"),
        email_verified=False,
    )
    db_session.add(user)
    await db_session.flush()

    resp = await auth_client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "MyPassword1!",
    })
    assert resp.status_code == 200
    assert resp.json()["email"] == email
    assert "access_token" in resp.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(db_session: AsyncSession, auth_client: AsyncClient):
    email = f"wrongpw-{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=email,
        display_name="WP User",
        password_hash=hash_password("CorrectPassword1"),
        email_verified=False,
    )
    db_session.add(user)
    await db_session.flush()

    resp = await auth_client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "WrongPassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(auth_client: AsyncClient):
    resp = await auth_client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "whatever",
    })
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /me
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert "@example.com" in data["email"]


@pytest.mark.asyncio
async def test_me_unauthenticated():
    """Without auth override, /me should 401."""
    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get("/api/v1/auth/me")
    assert resp.status_code == 401
