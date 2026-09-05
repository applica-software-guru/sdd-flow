import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.models.audit_log_entry import AuditLogEntry
from app.models.project import Project
from app.models.tenant import Tenant
from app.models.user import PlatformRole, User
from app.services.auth import hash_password
from app.services.super_user import promote_configured_super_user

pytestmark = pytest.mark.asyncio


async def test_standard_user_cannot_access_platform_admin(client: AsyncClient):
    response = await client.get("/api/v1/admin/overview")
    assert response.status_code == 403


async def test_super_user_can_view_global_inventory(
    client: AsyncClient, test_user: User, test_tenant: Tenant, test_project: Project
):
    test_user.platform_role = PlatformRole.super_user
    await test_user.save()

    overview = await client.get("/api/v1/admin/overview")
    users = await client.get(f"/api/v1/admin/users?search={test_user.email}")
    tenants = await client.get(f"/api/v1/admin/tenants?search={test_tenant.slug}")
    projects = await client.get(f"/api/v1/admin/projects?search={test_project.slug}")

    assert overview.status_code == 200
    assert overview.json()["users_count"] >= 1
    assert all(response.status_code == 200 for response in (users, tenants, projects))
    assert any(item["id"] == str(test_user.id) for item in users.json()["items"])
    user_item = next(item for item in users.json()["items"] if item["id"] == str(test_user.id))
    assert "password_hash" not in user_item
    assert any(item["id"] == str(test_tenant.id) for item in tenants.json()["items"])
    assert any(item["id"] == str(test_project.id) for item in projects.json()["items"])


async def test_admin_view_is_platform_audited(client: AsyncClient, test_user: User):
    test_user.platform_role = PlatformRole.super_user
    await test_user.save()
    await client.get("/api/v1/admin/users")

    entry = await AuditLogEntry.find_one(
        {"tenantId": None, "userId": test_user.id, "eventType": "super_user.admin_users_viewed"}
    )
    assert entry is not None
    assert entry.details == {}


async def test_admin_audit_supports_global_filters(client: AsyncClient, test_user: User):
    test_user.platform_role = PlatformRole.super_user
    await test_user.save()
    await AuditLogEntry(
        tenant_id=None,
        user_id=test_user.id,
        event_type="auth.login_success",
        details={},
    ).insert()

    response = await client.get("/api/v1/admin/audit-log?event_type=auth.login_success")
    assert response.status_code == 200
    assert any(item["event_type"] == "auth.login_success" for item in response.json()["items"])


async def test_configured_super_user_promotion_is_idempotent(test_user: User, monkeypatch):
    monkeypatch.setattr(settings, "SUPER_USER_EMAIL", f"  {test_user.email.upper()}  ")

    first = await promote_configured_super_user()
    second = await promote_configured_super_user()
    refreshed = await User.get(str(test_user.id))

    assert first is True
    assert second is False
    assert refreshed is not None
    assert refreshed.platform_role == PlatformRole.super_user
    assert (
        await AuditLogEntry.find(
            {
                "tenantId": None,
                "userId": test_user.id,
                "eventType": "super_user.promoted_from_environment",
            }
        ).count()
        == 1
    )


async def test_missing_configured_super_user_does_not_fail(monkeypatch):
    monkeypatch.setattr(settings, "SUPER_USER_EMAIL", f"missing-{uuid.uuid4()}@example.com")
    assert await promote_configured_super_user() is False


async def test_registration_promotes_configured_account(monkeypatch):
    email = f"configured-{uuid.uuid4()}@example.com"
    monkeypatch.setattr(settings, "SUPER_USER_EMAIL", email.upper())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as auth_client:
        response = await auth_client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Str0ngP@ss!", "display_name": "Configured"},
        )
    assert response.status_code == 201
    assert response.json()["platform_role"] == "super_user"
    created = await User.find_one(User.email == email)
    assert created is not None
    await created.delete()


async def test_login_promotes_existing_configured_account_and_audits_access(monkeypatch):
    email = f"login-configured-{uuid.uuid4()}@example.com"
    user = User(
        email=email,
        display_name="Configured",
        password_hash=hash_password("Str0ngP@ss!"),
        email_verified=True,
    )
    await user.insert()
    monkeypatch.setattr(settings, "SUPER_USER_EMAIL", email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as auth_client:
        response = await auth_client.post(
            "/api/v1/auth/login", json={"email": email, "password": "Str0ngP@ss!"}
        )
    assert response.status_code == 200
    assert response.json()["platform_role"] == "super_user"
    assert await AuditLogEntry.find_one(
        {"tenantId": None, "userId": user.id, "eventType": "auth.login_success"}
    )
    await user.delete()
