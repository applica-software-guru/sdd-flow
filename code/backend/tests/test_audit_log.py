"""
Tests for /api/v1/tenants/{tid}/audit-log endpoint.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models.audit_log_entry import AuditLogEntry
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories import AuditRepository, TenantRepository, UserRepository
from app.services.audit import AuditService


def _base(tenant: Tenant) -> str:
    return f"/api/v1/tenants/{tenant.id}/audit-log"


async def _create_entry(
    tenant: Tenant,
    user: User,
    event_type: str = "test.event",
    entity_type: str = "project",
    entity_label: str | None = None,
    summary: str | None = None,
) -> AuditLogEntry:
    entry = AuditLogEntry(
        tenant_id=tenant.id,
        user_id=user.id,
        event_type=event_type,
        entity_type=entity_type,
        entity_label=entity_label,
        summary=summary,
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
async def test_audit_log_entry_fields(client: AsyncClient, test_tenant: Tenant, test_user: User):
    entry = await _create_entry(
        test_tenant,
        test_user,
        "bug.transitioned",
        entity_label="Fix login redirect",
        summary="status: new → open",
    )
    try:
        resp = await client.get(_base(test_tenant))
        assert resp.status_code == 200
        found = next((i for i in resp.json()["items"] if i["id"] == str(entry.id)), None)
        assert found is not None
        # action mirrors event_type and is always present
        assert found["action"] == "bug.transitioned"
        assert found["event_type"] == "bug.transitioned"
        # user is resolved, not just a raw id
        assert found["user_id"] == str(test_user.id)
        assert found["user"]["id"] == str(test_user.id)
        assert found["user"]["display_name"] == test_user.display_name
        assert found["user"]["email"] == test_user.email
        # entity label / summary round-trip
        assert found["entity_label"] == "Fix login redirect"
        assert found["summary"] == "status: new → open"
    finally:
        await entry.delete()


@pytest.mark.asyncio
async def test_audit_log_legacy_entry_without_label(
    client: AsyncClient, test_tenant: Tenant, test_user: User
):
    """Legacy entries (no label/summary) still expose action and null optionals."""
    entry = await _create_entry(test_tenant, test_user, "project.created")
    try:
        resp = await client.get(_base(test_tenant))
        assert resp.status_code == 200
        found = next((i for i in resp.json()["items"] if i["id"] == str(entry.id)), None)
        assert found is not None
        assert found["action"] == "project.created"
        assert found["entity_label"] is None
        assert found["summary"] is None
    finally:
        await entry.delete()


@pytest.mark.asyncio
async def test_audit_log_system_entry_user_is_null(client: AsyncClient, test_tenant: Tenant):
    """Entries without a user (system events) expose user: null instead of failing."""
    entry = AuditLogEntry(
        tenant_id=test_tenant.id,
        user_id=None,
        event_type="system.event",
        entity_type="tenant",
    )
    await entry.insert()
    try:
        resp = await client.get(_base(test_tenant))
        assert resp.status_code == 200
        found = next((i for i in resp.json()["items"] if i["id"] == str(entry.id)), None)
        assert found is not None
        assert found["user_id"] is None
        assert found["user"] is None
    finally:
        await entry.delete()


@pytest.mark.asyncio
async def test_audit_log_pagination(client: AsyncClient, test_tenant: Tenant, test_user: User):
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
async def test_audit_log_filter_action_substring(
    client: AsyncClient, test_tenant: Tenant, test_user: User
):
    """The action filter is a case-insensitive substring match on event type."""
    e1 = await _create_entry(test_tenant, test_user, "bug.created")
    e2 = await _create_entry(test_tenant, test_user, "bug.transitioned")
    e3 = await _create_entry(test_tenant, test_user, "project.created")
    try:
        resp = await client.get(_base(test_tenant), params={"action": "BUG.TRANS"})
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()["items"]]
        assert str(e2.id) in ids
        assert str(e1.id) not in ids
        assert str(e3.id) not in ids
    finally:
        for e in (e1, e2, e3):
            await e.delete()


@pytest.mark.asyncio
async def test_audit_log_filter_entity_type(
    client: AsyncClient, test_tenant: Tenant, test_user: User
):
    e1 = await _create_entry(test_tenant, test_user, "a.one", entity_type="project")
    e2 = await _create_entry(test_tenant, test_user, "a.two", entity_type="bug")
    try:
        resp = await client.get(_base(test_tenant), params={"entity_type": "bug"})
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()["items"]]
        assert str(e2.id) in ids
        assert str(e1.id) not in ids
    finally:
        for e in (e1, e2):
            await e.delete()


@pytest.mark.asyncio
async def test_audit_log_filter_user_id(client: AsyncClient, test_tenant: Tenant, test_user: User):
    e1 = await _create_entry(test_tenant, test_user, "a.one")
    e2 = await _create_entry(test_tenant, test_user, "a.two")
    try:
        resp = await client.get(_base(test_tenant), params={"user_id": str(test_user.id)})
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()["items"]]
        assert str(e1.id) in ids
        assert str(e2.id) in ids

        resp = await client.get(_base(test_tenant), params={"user_id": str(uuid.uuid4())})
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()["items"]]
        assert str(e1.id) not in ids
    finally:
        for e in (e1, e2):
            await e.delete()


@pytest.mark.asyncio
async def test_audit_log_filter_date_range(
    client: AsyncClient, test_tenant: Tenant, test_user: User
):
    e1 = await _create_entry(test_tenant, test_user, "a.one")
    e2 = await _create_entry(test_tenant, test_user, "a.two")
    try:
        # Range entirely in the future excludes both entries
        resp = await client.get(
            _base(test_tenant),
            params={"from": "2099-01-01T00:00:00Z", "to": "2099-12-31T00:00:00Z"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

        # Wide range in the past includes both
        resp = await client.get(
            _base(test_tenant),
            params={"from": "2020-01-01T00:00:00Z"},
        )
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()["items"]]
        assert str(e1.id) in ids
        assert str(e2.id) in ids
    finally:
        for e in (e1, e2):
            await e.delete()


@pytest.mark.asyncio
async def test_audit_log_filter_event_type_exact_legacy(
    client: AsyncClient, test_tenant: Tenant, test_user: User
):
    """The legacy event_type param still works with exact match."""
    e1 = await _create_entry(test_tenant, test_user, "bug.created")
    e2 = await _create_entry(test_tenant, test_user, "bug.transitioned")
    try:
        resp = await client.get(_base(test_tenant), params={"event_type": "bug.created"})
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()["items"]]
        assert str(e1.id) in ids
        assert str(e2.id) not in ids
    finally:
        for e in (e1, e2):
            await e.delete()


@pytest.mark.asyncio
async def test_log_event_persists_label_and_summary(
    client: AsyncClient, test_tenant: Tenant, test_user: User
):
    """Unit test: AuditService.log_event captures entity_label and summary at write time."""
    svc = AuditService(
        audit_repo=AuditRepository(),
        user_repo=UserRepository(),
        tenant_repo=TenantRepository(),
    )
    entry = await svc.log_event(
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        event_type="bug.transitioned",
        entity_type="bug",
        entity_id=uuid.uuid4(),
        details={"old_status": "new", "new_status": "open"},
        entity_label="Fix login redirect",
        summary="status: new → open",
    )
    try:
        stored = await AuditLogEntry.get(entry.id)
        assert stored is not None
        assert stored.entity_label == "Fix login redirect"
        assert stored.summary == "status: new → open"
        assert stored.event_type == "bug.transitioned"
    finally:
        await entry.delete()
