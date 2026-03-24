"""Tests for /api/v1/tenants endpoints."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.middleware.auth import get_current_tenant_member, get_current_user
from app.models.tenant import Tenant
from app.models.tenant_invitation import TenantInvitation
from app.models.tenant_member import MemberRole, TenantMember
from app.models.user import User


# ---------------------------------------------------------------------------
# Create tenant
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_tenant(client: AsyncClient):
    slug = f"t-{uuid.uuid4().hex[:8]}"
    resp = await client.post("/api/v1/tenants", json={
        "name": "My Org",
        "slug": slug,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Org"
    assert data["slug"] == slug
    assert "id" in data


@pytest.mark.asyncio
async def test_create_tenant_duplicate_slug(client: AsyncClient, test_tenant: Tenant):
    resp = await client.post("/api/v1/tenants", json={
        "name": "Dup",
        "slug": test_tenant.slug,
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_tenant_missing_fields(client: AsyncClient):
    resp = await client.post("/api/v1/tenants", json={"name": "No slug"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List tenants
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_tenants(client: AsyncClient, test_tenant: Tenant):
    resp = await client.get("/api/v1/tenants")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(t["id"] == str(test_tenant.id) for t in data)


# ---------------------------------------------------------------------------
# Get tenant by ID
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_tenant(client: AsyncClient, test_tenant: Tenant):
    resp = await client.get(f"/api/v1/tenants/{test_tenant.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(test_tenant.id)


@pytest.mark.asyncio
async def test_get_tenant_not_found(client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/tenants/{fake_id}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update tenant
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_tenant(client: AsyncClient, test_tenant: Tenant):
    resp = await client.patch(f"/api/v1/tenants/{test_tenant.id}", json={
        "name": "Renamed Tenant",
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Tenant"


# ---------------------------------------------------------------------------
# List members
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_members(client: AsyncClient, test_tenant: Tenant):
    resp = await client.get(f"/api/v1/tenants/{test_tenant.id}/members")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["role"] == "owner"


# ---------------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invite_member_success(client: AsyncClient, test_tenant: Tenant):
    invite_email = f"invite-{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/invitations",
        json={"email": invite_email, "role": "member"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["tenant_id"] == str(test_tenant.id)
    assert data["email"] == invite_email
    assert data["role"] == "member"
    assert data["token"]
    assert data["expires_at"]


@pytest.mark.asyncio
async def test_invite_member_already_member_conflict(
    client: AsyncClient,
    test_tenant: Tenant,
    test_user: User,
):
    resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/invitations",
        json={"email": test_user.email, "role": "member"},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "User is already a member"


@pytest.mark.asyncio
async def test_invite_member_requires_owner_or_admin(
    client: AsyncClient,
    test_tenant: Tenant,
    test_user: User,
):
    viewer_member = TenantMember(
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        role=MemberRole.viewer,
    )

    async def override_get_current_tenant_member(tenant_id: uuid.UUID | None = None):
        return viewer_member

    app.dependency_overrides[get_current_tenant_member] = override_get_current_tenant_member
    try:
        resp = await client.post(
            f"/api/v1/tenants/{test_tenant.id}/invitations",
            json={"email": f"viewer-{uuid.uuid4().hex[:8]}@example.com", "role": "member"},
        )
    finally:
        app.dependency_overrides.pop(get_current_tenant_member, None)

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_accept_invitation_success(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    unique_id: str,
):
    invitee = User(
        email=f"invitee-{unique_id}@example.com",
        display_name="Invitee",
        password_hash="fakehash",
        email_verified=True,
    )
    db_session.add(invitee)
    await db_session.commit()

    invite_resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/invitations",
        json={"email": invitee.email, "role": "member"},
    )
    assert invite_resp.status_code == 201
    token = invite_resp.json()["token"]

    async def override_get_current_user():
        return invitee

    app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        accept_resp = await client.post(f"/api/v1/tenants/invitations/{token}/accept")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert accept_resp.status_code == 200
    data = accept_resp.json()
    assert data["email"] == invitee.email
    assert data["role"] == "member"


@pytest.mark.asyncio
async def test_accept_invitation_expired(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    expired_invitation = TenantInvitation(
        tenant_id=test_tenant.id,
        email=test_user.email,
        role=MemberRole.member,
        invited_by=test_user.id,
        token=f"expired-{uuid.uuid4().hex}",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(expired_invitation)
    await db_session.commit()

    resp = await client.post(f"/api/v1/tenants/invitations/{expired_invitation.token}/accept")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invitation expired"


@pytest.mark.asyncio
async def test_accept_invitation_wrong_email(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    unique_id: str,
):
    different_user = User(
        email=f"different-{unique_id}@example.com",
        display_name="Different",
        password_hash="fakehash",
        email_verified=True,
    )
    db_session.add(different_user)
    await db_session.commit()

    invitation = TenantInvitation(
        tenant_id=test_tenant.id,
        email=different_user.email,
        role=MemberRole.member,
        invited_by=test_user.id,
        token=f"wrong-email-{uuid.uuid4().hex}",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(invitation)
    await db_session.commit()

    resp = await client.post(f"/api/v1/tenants/invitations/{invitation.token}/accept")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Invitation is for a different email"


@pytest.mark.asyncio
async def test_invitation_email_dispatch_called(
    client: AsyncClient,
    test_tenant: Tenant,
    monkeypatch: pytest.MonkeyPatch,
):
    called = {"count": 0}

    async def fake_send_tenant_invitation_email(**kwargs):
        called["count"] += 1
        assert kwargs["recipient_email"].endswith("@example.com")
        assert kwargs["tenant_name"]
        assert kwargs["inviter_name"]
        assert kwargs["token"]

    monkeypatch.setattr(
        "app.api.tenants.send_tenant_invitation_email",
        fake_send_tenant_invitation_email,
    )

    resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/invitations",
        json={"email": f"mail-{uuid.uuid4().hex[:8]}@example.com", "role": "member"},
    )
    assert resp.status_code == 201
    assert called["count"] == 1


@pytest.mark.asyncio
async def test_list_invitations_shows_pending_status(
    client: AsyncClient,
    test_tenant: Tenant,
):
    invite_email = f"pending-{uuid.uuid4().hex[:8]}@example.com"
    create_resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/invitations",
        json={"email": invite_email, "role": "member"},
    )
    assert create_resp.status_code == 201

    list_resp = await client.get(f"/api/v1/tenants/{test_tenant.id}/invitations")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert isinstance(data, list)
    target = next((item for item in data if item["email"] == invite_email), None)
    assert target is not None
    assert target["status"] == "pending"


@pytest.mark.asyncio
async def test_list_invitations_shows_accepted_and_expired_status(
    client: AsyncClient,
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    accepted_invitation = TenantInvitation(
        tenant_id=test_tenant.id,
        email=f"accepted-{uuid.uuid4().hex[:8]}@example.com",
        role=MemberRole.member,
        invited_by=test_user.id,
        token=f"accepted-{uuid.uuid4().hex}",
        expires_at=datetime.now(timezone.utc) + timedelta(days=2),
        accepted_at=datetime.now(timezone.utc),
    )
    expired_invitation = TenantInvitation(
        tenant_id=test_tenant.id,
        email=f"expired-{uuid.uuid4().hex[:8]}@example.com",
        role=MemberRole.viewer,
        invited_by=test_user.id,
        token=f"expired-{uuid.uuid4().hex}",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(accepted_invitation)
    db_session.add(expired_invitation)
    await db_session.commit()

    list_resp = await client.get(f"/api/v1/tenants/{test_tenant.id}/invitations")
    assert list_resp.status_code == 200
    data = list_resp.json()

    accepted = next((item for item in data if item["id"] == str(accepted_invitation.id)), None)
    expired = next((item for item in data if item["id"] == str(expired_invitation.id)), None)

    assert accepted is not None
    assert accepted["status"] == "accepted"
    assert expired is not None
    assert expired["status"] == "expired"
