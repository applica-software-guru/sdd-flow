"""Tests for /api/v1/auth endpoints."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.main import app
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.auth import hash_password, verify_password


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


# ---------------------------------------------------------------------------
# Forgot/reset password
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_forgot_password_creates_token_and_dispatches_email(
    db_session: AsyncSession,
    auth_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    email = f"forgot-{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=email,
        display_name="Forgot User",
        password_hash=hash_password("OldPassword1!"),
        email_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    calls = {"count": 0}

    async def fake_send_email(**kwargs):
        calls["count"] += 1
        assert kwargs["recipient_email"] == email
        assert kwargs["subject"]
        assert "reset" in kwargs["subject"].lower()

    monkeypatch.setattr("app.services.password_reset.send_email", fake_send_email)

    resp = await auth_client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert resp.status_code == 200
    assert "If an account" in resp.json()["detail"]
    assert calls["count"] == 1

    token_result = await db_session.execute(
        select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    )
    reset_token = token_result.scalar_one_or_none()
    assert reset_token is not None
    assert reset_token.used_at is None


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_returns_generic_message(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": f"unknown-{uuid.uuid4().hex[:8]}@example.com"},
    )
    assert resp.status_code == 200
    assert "If an account" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_success(
    db_session: AsyncSession,
    auth_client: AsyncClient,
):
    from app.services.password_reset import _hash_token

    email = f"reset-{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=email,
        display_name="Reset User",
        password_hash=hash_password("OldPassword1!"),
        email_verified=False,
    )
    db_session.add(user)
    await db_session.flush()

    raw_token = f"raw-{uuid.uuid4().hex}"
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=20),
    )
    db_session.add(reset_token)

    refresh = RefreshToken(
        user_id=user.id,
        token_hash=f"refresh-{uuid.uuid4().hex}",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(refresh)
    await db_session.flush()

    resp = await auth_client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewPassword1!"},
    )
    assert resp.status_code == 200

    await db_session.refresh(user)
    assert user.password_hash is not None
    assert verify_password("NewPassword1!", user.password_hash)
    assert not verify_password("OldPassword1!", user.password_hash)
    assert user.email_verified is True

    token_result = await db_session.execute(
        select(PasswordResetToken).where(PasswordResetToken.id == reset_token.id)
    )
    updated_token = token_result.scalar_one()
    assert updated_token.used_at is not None

    refresh_result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    assert refresh_result.scalars().first() is None


@pytest.mark.asyncio
async def test_reset_password_invalid_token(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/v1/auth/reset-password",
        json={"token": "does-not-exist", "new_password": "NewPassword1!"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid or expired reset token"
