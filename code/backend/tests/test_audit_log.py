"""
Tests for /api/v1/tenants/{tid}/audit-log endpoint.
"""

import pytest
from httpx import AsyncClient

from app.models.audit_log_entry import AuditLogEntry
from app.models.tenant import Tenant
from app.models.user import User


def _base(tenant: Tenant) -> str:
    return f"/api/v1/tenants/{tenant.id}/audit-log"


async def _create_entry(tenant: Tenant, user: User, event_type: str = "test.event") -> AuditLogEntry:
    entry = AuditLogEntry(
        tenant_id=tenant.id,
        user_id=user.id,
        event_type=event_type,
        entity_type="project",
        details={"key": "value"},
    )
    await entry.insert()
    return entry


@pytest.mark.asyncio
async def test_list_audit_log_empty(client: AsyncClient, test_tenant: Tenant):
    resp = await client.get(_base(test_tenant))
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_audit_log_returns_entry(
    client: AsyncClient, test_tenant: Tenant, test_user: User
):
    entry = await _create_entry(test_tenant, test_user, "cr.created")
    try:
        resp = await client.get(_base(test_tenant))
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()["items"]]
        assert str(entry.id) in ids
    finally:
        await entry.delete()


@pytest.mark.asyncio
async def test_audit_log_entry_fields(
    client: AsyncClient, test_tenant: Tenant, test_user: User
):
    entry = await _create_entry(test_tenant, test_user, "bug.created")
    try:
        resp = await client.get(_base(test_tenant))
        assert resp.status_code == 200
        found = next((i for i in resp.json()["items"] if i["id"] == str(entry.id)), None)
        assert found is not None
        assert found["event_type"] == "bug.created"
        assert found["user_id"] == str(test_user.id)
    finally:
        await entry.delete()


@pytest.mark.asyncio
async def test_audit_log_pagination(
    client: AsyncClient, test_tenant: Tenant, test_user: User
):
    entries = [await _create_entry(test_tenant, test_user) for _ in range(5)]
    try:
        resp = await client.get(_base(test_tenant), params={"page": 1, "page_size": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 2
        assert data["total"] >= 5
    finally:
        for e in entries:
            await e.delete()


@pytest.mark.asyncio
async def test_audit_log_scoped_to_tenant(
    client: AsyncClient, test_tenant: Tenant, test_user: User, unique_id: str
):
    # Create a second tenant and add an entry there
    from app.models.tenant import Tenant, DefaultRole
    other_tenant = Tenant(
        name=f"Other {unique_id}",
        slug=f"other-{unique_id}",
        default_role=DefaultRole.member,
    )
    await other_tenant.insert()
    entry = await _create_entry(other_tenant, test_user, "other.event")
    try:
        resp = await client.get(_base(test_tenant))
        ids = [i["id"] for i in resp.json()["items"]]
        assert str(entry.id) not in ids, "Entry from other tenant must not appear"
    finally:
        await entry.delete()
        await other_tenant.delete()
