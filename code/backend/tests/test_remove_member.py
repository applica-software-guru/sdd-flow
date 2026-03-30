"""
Tests for DELETE /api/v1/tenants/{tid}/members/{uid} endpoint.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.middleware.auth import get_current_tenant_member, get_current_user
from app.models.tenant import DefaultRole, Tenant
from app.models.tenant_member import MemberRole, TenantMember
from app.models.user import User


def _members_url(tenant: Tenant, user_id: uuid.UUID) -> str:
    return f"/api/v1/tenants/{tenant.id}/members/{user_id}"


async def _make_member(tenant: Tenant, role: MemberRole, unique_id: str) -> tuple[User, TenantMember]:
    user = User(
        email=f"member-{unique_id}@example.com",
        display_name=f"Member {unique_id}",
        password_hash="x",
        email_verified=True,
    )
    await user.insert()
    member = TenantMember(tenant_id=tenant.id, user_id=user.id, role=role)
    await member.insert()
    return user, member


@pytest.mark.asyncio
async def test_remove_member_success(
    test_user: User, test_tenant: Tenant, test_member: TenantMember, unique_id: str
):
    """Owner can remove a regular member."""
    target_user, target_member = await _make_member(test_tenant, MemberRole.member, unique_id)

    try:
        async def _current_user():
            return test_user

        async def _current_member(tenant_id: uuid.UUID = None):
            return test_member  # owner

        app.dependency_overrides[get_current_user] = _current_user
        app.dependency_overrides[get_current_tenant_member] = _current_member

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            resp = await ac.delete(_members_url(test_tenant, target_user.id))

        assert resp.status_code == 204

        # Verify the member no longer exists in DB
        removed = await TenantMember.find_one(
            {"tenantId": test_tenant.id, "userId": target_user.id}
        )
        assert removed is None
    finally:
        app.dependency_overrides.clear()
        try:
            await target_user.delete()
        except Exception:
            pass


@pytest.mark.asyncio
async def test_remove_member_not_found(
    test_user: User, test_tenant: Tenant, test_member: TenantMember
):
    """Removing a nonexistent user_id returns 404."""

    async def _current_user():
        return test_user

    async def _current_member(tenant_id: uuid.UUID = None):
        return test_member

    app.dependency_overrides[get_current_user] = _current_user
    app.dependency_overrides[get_current_tenant_member] = _current_member

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            resp = await ac.delete(_members_url(test_tenant, uuid.uuid4()))

        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_remove_owner_by_other_admin_is_forbidden(
    test_user: User, test_tenant: Tenant, unique_id: str
):
    """An admin cannot remove an owner."""
    admin_user, admin_member = await _make_member(test_tenant, MemberRole.admin, f"admin-{unique_id}")

    try:
        async def _current_user():
            return admin_user

        async def _current_member(tenant_id: uuid.UUID = None):
            return admin_member

        app.dependency_overrides[get_current_user] = _current_user
        app.dependency_overrides[get_current_tenant_member] = _current_member

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            resp = await ac.delete(_members_url(test_tenant, test_user.id))

        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()
        try:
            await admin_member.delete()
            await admin_user.delete()
        except Exception:
            pass


@pytest.mark.asyncio
async def test_remove_member_requires_admin_or_owner(
    test_user: User, test_tenant: Tenant, unique_id: str
):
    """A regular member cannot remove anyone — should get 403."""
    regular_user, regular_member = await _make_member(test_tenant, MemberRole.member, f"reg-{unique_id}")
    target_user, target_member = await _make_member(test_tenant, MemberRole.member, f"tgt-{unique_id}")

    try:
        async def _current_user():
            return regular_user

        async def _current_member(tenant_id: uuid.UUID = None):
            return regular_member

        app.dependency_overrides[get_current_user] = _current_user
        app.dependency_overrides[get_current_tenant_member] = _current_member

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            resp = await ac.delete(_members_url(test_tenant, target_user.id))

        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()
        for obj in [regular_member, regular_user, target_member, target_user]:
            try:
                await obj.delete()
            except Exception:
                pass
