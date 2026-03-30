"""
Tests for /api/v1/notifications endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models.notification import Notification
from app.models.tenant import Tenant
from app.models.user import User


def _base() -> str:
    return "/api/v1/notifications"


async def _create_notification(user: User, tenant: Tenant) -> Notification:
    n = Notification(
        user_id=user.id,
        tenant_id=tenant.id,
        event_type="test.event",
        entity_type="bug",
        entity_id=uuid.uuid4(),
        title="Test notification",
    )
    await n.insert()
    return n


@pytest.mark.asyncio
async def test_list_notifications_empty(client: AsyncClient):
    resp = await client.get(_base())
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_notifications_returns_own(
    client: AsyncClient, test_user: User, test_tenant: Tenant
):
    n = await _create_notification(test_user, test_tenant)
    try:
        resp = await client.get(_base())
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert str(n.id) in ids
    finally:
        await n.delete()


@pytest.mark.asyncio
async def test_unread_count(client: AsyncClient, test_user: User, test_tenant: Tenant):
    n = await _create_notification(test_user, test_tenant)
    try:
        resp = await client.get(f"{_base()}/unread-count")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1
    finally:
        await n.delete()


@pytest.mark.asyncio
async def test_mark_notification_read(client: AsyncClient, test_user: User, test_tenant: Tenant):
    n = await _create_notification(test_user, test_tenant)
    try:
        resp = await client.post(f"{_base()}/{n.id}/read")
        assert resp.status_code == 200
        assert resp.json()["read_at"] is not None
    finally:
        await n.delete()


@pytest.mark.asyncio
async def test_mark_all_notifications_read(
    client: AsyncClient, test_user: User, test_tenant: Tenant
):
    n1 = await _create_notification(test_user, test_tenant)
    n2 = await _create_notification(test_user, test_tenant)
    try:
        resp = await client.post(f"{_base()}/read-all")
        assert resp.status_code == 200

        resp = await client.get(f"{_base()}/unread-count")
        assert resp.json()["count"] == 0
    finally:
        await n1.delete()
        await n2.delete()


@pytest.mark.asyncio
async def test_mark_nonexistent_notification_read(client: AsyncClient):
    resp = await client.post(f"{_base()}/{uuid.uuid4()}/read")
    assert resp.status_code == 404
