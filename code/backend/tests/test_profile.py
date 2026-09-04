"""Tests for self-service profile endpoints (CR-035)."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.audit_log_entry import AuditLogEntry
from app.models.user import User
from app.services.auth import display_name_from_email, hash_password, verify_password


async def fresh_user(user: User) -> User:
    """Re-fetch the user from the DB (no reload support on detached docs)."""
    return await User.get(user.id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
async def google_user(unique_id: str):
    """Google-only user: no password hash."""
    user = User(
        email=f"google-{unique_id}@example.com",
        display_name=f"Google User {unique_id}",
        google_id=f"gid-{unique_id}",
        email_verified=True,
    )
    await user.insert()
    yield user
    try:
        await user.delete()
    except Exception:
        pass


@pytest.fixture
async def google_client(google_user: User):
    from app.middleware.auth import get_current_user

    async def override_get_current_user():
        return google_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def unauth_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ---------------------------------------------------------------------------
# PATCH /auth/me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_display_name_success(client: AsyncClient, test_user: User):
    resp = await client.patch("/api/v1/auth/me", json={"display_name": "  New Name  "})
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "New Name"
    assert data["has_password"] is True
    test_user = await fresh_user(test_user)
    assert test_user.display_name == "New Name"


@pytest.mark.asyncio
async def test_update_display_name_empty_rejected(client: AsyncClient):
    resp = await client.patch("/api/v1/auth/me", json={"display_name": "   "})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_display_name_too_long_rejected(client: AsyncClient):
    resp = await client.patch("/api/v1/auth/me", json={"display_name": "x" * 81})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_display_name_unauthenticated(unauth_client: AsyncClient):
    resp = await unauth_client.patch("/api/v1/auth/me", json={"display_name": "Nope"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_profile_writes_audit_entries(
    client: AsyncClient, test_user: User, test_tenant
):
    resp = await client.patch("/api/v1/auth/me", json={"display_name": "Audited Name"})
    assert resp.status_code == 200
    entries = await AuditLogEntry.find(
        {"tenantId": test_tenant.id, "eventType": "user.profile_updated"}
    ).to_list()
    assert len(entries) >= 1
    entry = entries[-1]
    assert str(entry.user_id) == str(test_user.id)
    assert entry.details["new_display_name"] == "Audited Name"
    # Cleanup audit entries created by this test
    await AuditLogEntry.find({"tenantId": test_tenant.id}).delete()


# ---------------------------------------------------------------------------
# POST /auth/me/change-password
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient, test_user: User):
    test_user.password_hash = hash_password("OldPassword1!")
    await test_user.save()

    resp = await client.post(
        "/api/v1/auth/me/change-password",
        json={"current_password": "WrongOld1!", "new_password": "NewPassword1!"},
    )
    assert resp.status_code == 400
    test_user = await fresh_user(test_user)
    assert verify_password("NewPassword1!", test_user.password_hash) is False


@pytest.mark.asyncio
async def test_change_password_success_and_session_kept(
    client: AsyncClient, test_user: User
):
    test_user.password_hash = hash_password("OldPassword1!")
    await test_user.save()

    resp = await client.post(
        "/api/v1/auth/me/change-password",
        json={"current_password": "OldPassword1!", "new_password": "NewPassword1!"},
        cookies={"refresh_token": "current-session-token"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"password_set": True}
    test_user = await fresh_user(test_user)
    assert verify_password("NewPassword1!", test_user.password_hash)


@pytest.mark.asyncio
async def test_change_password_too_short(client: AsyncClient, test_user: User):
    test_user.password_hash = hash_password("OldPassword1!")
    await test_user.save()
    resp = await client.post(
        "/api/v1/auth/me/change-password",
        json={"current_password": "OldPassword1!", "new_password": "short"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_google_only_user_sets_initial_password(
    google_client: AsyncClient, google_user: User
):
    resp = await google_client.post(
        "/api/v1/auth/me/change-password",
        json={"new_password": "BrandNew1!"},
    )
    assert resp.status_code == 200
    google_user = await fresh_user(google_user)
    assert google_user.password_hash is not None
    assert verify_password("BrandNew1!", google_user.password_hash)

    # /me now reports has_password True
    me_resp = await google_client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["has_password"] is True


@pytest.mark.asyncio
async def test_google_only_user_cannot_change_without_current(
    google_client: AsyncClient, google_user: User
):
    """Google-only user with password set afterwards must provide current password."""
    google_user.password_hash = hash_password("Existing1!")
    await google_user.save()
    resp = await google_client.post(
        "/api/v1/auth/me/change-password",
        json={"new_password": "BrandNew1!"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Display-name fallback for Google accounts
# ---------------------------------------------------------------------------


def test_display_name_from_email_periods():
    assert display_name_from_email("mario.rossi@acme.com") == "Mario Rossi"


def test_display_name_from_email_mixed_separators():
    assert display_name_from_email("mario_rossi-smith+dev@acme.com") == "Mario Rossi Smith Dev"


def test_display_name_from_email_no_separators():
    assert display_name_from_email("mario@acme.com") == "Mario"


def test_display_name_from_email_edge_cases():
    assert display_name_from_email("@acme.com") == "@acme.com"
    assert display_name_from_email("...@acme.com") == "...@acme.com"