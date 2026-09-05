"""Tests for /api/v1/tenants endpoints."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.main import app
from app.middleware.auth import get_current_tenant_member, get_current_user
from app.models.bug import Bug, BugSeverity, BugStatus
from app.models.change_request import ChangeRequest, CRStatus
from app.models.comment import Comment, EntityType
from app.models.document_file import DocStatus, DocumentFile
from app.models.project import Project
from app.models.tenant import Tenant
from app.models.tenant_invitation import TenantInvitation
from app.models.tenant_member import MemberRole, TenantMember
from app.models.user import User
from app.models.worker import Worker, WorkerStatus

# ---------------------------------------------------------------------------
# Create tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_tenant(client: AsyncClient):
    slug = f"t-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        "/api/v1/tenants",
        json={
            "name": "My Org",
            "slug": slug,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Org"
    assert data["slug"] == slug
    assert "id" in data


@pytest.mark.asyncio
async def test_create_tenant_duplicate_slug(client: AsyncClient, test_tenant: Tenant):
    resp = await client.post(
        "/api/v1/tenants",
        json={
            "name": "Dup",
            "slug": test_tenant.slug,
        },
    )
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


@pytest.mark.asyncio
async def test_workspace_navigation_returns_visible_tenants_and_projects(
    client: AsyncClient,
    test_tenant: Tenant,
    test_project: Project,
    test_user: User,
    unique_id: str,
):
    second_tenant = Tenant(
        name=f"Second Tenant {unique_id}",
        slug=f"second-tenant-{unique_id}",
    )
    hidden_tenant = Tenant(
        name=f"Hidden Tenant {unique_id}",
        slug=f"hidden-tenant-{unique_id}",
    )
    await second_tenant.insert()
    await hidden_tenant.insert()
    await TenantMember(
        tenant_id=second_tenant.id,
        user_id=test_user.id,
        role=MemberRole.viewer,
    ).insert()
    second_project = Project(
        tenant_id=second_tenant.id,
        name=f"Second Project {unique_id}",
        slug=f"second-project-{unique_id}",
    )
    hidden_project = Project(
        tenant_id=hidden_tenant.id,
        name=f"Hidden Project {unique_id}",
        slug=f"hidden-project-{unique_id}",
    )
    await second_project.insert()
    await hidden_project.insert()

    try:
        resp = await client.get("/api/v1/tenants/navigation")
    finally:
        await second_project.delete()
        await hidden_project.delete()
        await TenantMember.find({"tenantId": second_tenant.id}).delete()
        await second_tenant.delete()
        await hidden_tenant.delete()

    assert resp.status_code == 200
    data = resp.json()
    tenants = {tenant["id"]: tenant for tenant in data["tenants"]}

    assert str(test_tenant.id) in tenants
    assert str(second_tenant.id) in tenants
    assert str(hidden_tenant.id) not in tenants
    assert tenants[str(test_tenant.id)]["can_create_project"] is True
    assert tenants[str(second_tenant.id)]["role"] == "viewer"
    assert tenants[str(second_tenant.id)]["can_create_project"] is False
    assert any(
        project["id"] == str(test_project.id)
        for project in tenants[str(test_tenant.id)]["projects"]
    )
    assert tenants[str(second_tenant.id)]["projects"] == [
        {
            "id": str(second_project.id),
            "name": second_project.name,
            "slug": second_project.slug,
            "archived_at": None,
        }
    ]


@pytest.mark.asyncio
async def test_workspace_navigation_uses_static_route_before_tenant_id(client: AsyncClient):
    resp = await client.get("/api/v1/tenants/navigation")

    assert resp.status_code == 200
    assert "tenants" in resp.json()


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
# Tenant dashboard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tenant_dashboard_aggregates_active_project_kpis(
    client: AsyncClient,
    test_tenant: Tenant,
    test_project,
    test_user: User,
):
    await DocumentFile(
        project_id=test_project.id,
        path="product/vision.md",
        title="Vision",
        status=DocStatus.synced,
    ).insert()
    await DocumentFile(
        project_id=test_project.id,
        path="product/features/auth.md",
        title="Auth",
        status=DocStatus.changed,
    ).insert()
    cr = ChangeRequest(
        project_id=test_project.id,
        number=1,
        slug="dashboard-kpis",
        title="Dashboard KPIs",
        body="Add tenant KPIs",
        status=CRStatus.approved,
        author_id=test_user.id,
    )
    await cr.insert()
    bug = Bug(
        project_id=test_project.id,
        number=1,
        slug="critical-login",
        title="Critical login bug",
        body="Fails on redirect",
        status=BugStatus.open,
        severity=BugSeverity.critical,
        author_id=test_user.id,
    )
    await bug.insert()
    await Comment(
        entity_type=EntityType.change_request,
        entity_id=cr.id,
        author_id=test_user.id,
        body="Looks good",
    ).insert()
    await Worker(
        project_id=test_project.id,
        name="local-worker",
        status=WorkerStatus.online,
    ).insert()
    resp = await client.get(f"/api/v1/tenants/{test_tenant.id}/dashboard")

    assert resp.status_code == 200
    data = resp.json()
    assert data["tenant"]["id"] == str(test_tenant.id)
    assert data["kpis"]["active_projects"] >= 1
    assert data["kpis"]["documents_total"] == 2
    assert data["kpis"]["documents_synced"] == 1
    assert data["kpis"]["documents_pending"] == 1
    assert data["kpis"]["open_bugs"] == 1
    assert data["kpis"]["critical_bugs"] == 1
    assert data["kpis"]["active_crs"] == 1
    assert data["kpis"]["review_queue_crs"] == 1
    assert data["kpis"]["comments_in_window"] == 1
    assert data["kpis"]["workers_online"] == 1
    assert data["projects"][0]["id"] == str(test_project.id)


# ---------------------------------------------------------------------------
# Update tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_tenant(client: AsyncClient, test_tenant: Tenant):
    resp = await client.patch(
        f"/api/v1/tenants/{test_tenant.id}",
        json={
            "name": "Renamed Tenant",
        },
    )
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
    test_tenant: Tenant,
    unique_id: str,
):
    invitee = User(
        email=f"invitee-{unique_id}@example.com",
        display_name="Invitee",
        password_hash="fakehash",
        email_verified=True,
    )
    await invitee.insert()

    try:
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
    finally:
        await TenantMember.find(
            {"tenantId": str(test_tenant.id), "userId": str(invitee.id)}
        ).delete()
        await TenantInvitation.find(
            {"tenantId": str(test_tenant.id), "email": invitee.email}
        ).delete()
        await invitee.delete()


@pytest.mark.asyncio
async def test_accept_invitation_expired(
    client: AsyncClient,
    test_tenant: Tenant,
    test_user: User,
):
    expired_invitation = TenantInvitation(
        tenant_id=test_tenant.id,
        email=test_user.email,
        role=MemberRole.member,
        invited_by=test_user.id,
        token=f"expired-{uuid.uuid4().hex}",
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    await expired_invitation.insert()

    try:
        resp = await client.post(f"/api/v1/tenants/invitations/{expired_invitation.token}/accept")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invitation expired"
    finally:
        await expired_invitation.delete()


@pytest.mark.asyncio
async def test_accept_invitation_wrong_email(
    client: AsyncClient,
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
    await different_user.insert()

    invitation = TenantInvitation(
        tenant_id=test_tenant.id,
        email=different_user.email,
        role=MemberRole.member,
        invited_by=test_user.id,
        token=f"wrong-email-{uuid.uuid4().hex}",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    await invitation.insert()

    try:
        resp = await client.post(f"/api/v1/tenants/invitations/{invitation.token}/accept")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Invitation is for a different email"
    finally:
        await invitation.delete()
        await different_user.delete()


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
        "app.services.tenants.send_tenant_invitation_email",
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
    test_tenant: Tenant,
    test_user: User,
):
    accepted_invitation = TenantInvitation(
        tenant_id=test_tenant.id,
        email=f"accepted-{uuid.uuid4().hex[:8]}@example.com",
        role=MemberRole.member,
        invited_by=test_user.id,
        token=f"accepted-{uuid.uuid4().hex}",
        expires_at=datetime.now(UTC) + timedelta(days=2),
        accepted_at=datetime.now(UTC),
    )
    expired_invitation = TenantInvitation(
        tenant_id=test_tenant.id,
        email=f"expired-{uuid.uuid4().hex[:8]}@example.com",
        role=MemberRole.viewer,
        invited_by=test_user.id,
        token=f"expired-{uuid.uuid4().hex}",
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    await accepted_invitation.insert()
    await expired_invitation.insert()

    try:
        list_resp = await client.get(f"/api/v1/tenants/{test_tenant.id}/invitations")
        assert list_resp.status_code == 200
        data = list_resp.json()

        accepted = next((item for item in data if item["id"] == str(accepted_invitation.id)), None)
        expired = next((item for item in data if item["id"] == str(expired_invitation.id)), None)

        assert accepted is not None
        assert accepted["status"] == "accepted"
        assert expired is not None
        assert expired["status"] == "expired"
    finally:
        await accepted_invitation.delete()
        await expired_invitation.delete()
