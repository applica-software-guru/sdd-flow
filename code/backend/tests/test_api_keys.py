"""Tests for /api/v1/tenants/{tid}/projects/{pid}/api-keys endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.project import Project
from app.models.tenant import Tenant


def _base(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/api-keys"


# ---------------------------------------------------------------------------
# Create API key
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_api_key(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(
        _base(test_tenant, test_project),
        json={"name": "CI Key"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "CI Key"
    assert "full_key" in data
    assert data["full_key"].startswith("sdd_")
    assert data["key_prefix"] == data["full_key"][:12]
    assert data["revoked_at"] is None


@pytest.mark.asyncio
async def test_create_api_key_missing_name(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(
        _base(test_tenant, test_project),
        json={},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List API keys
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_api_keys(client: AsyncClient, test_tenant, test_project):
    # Create two keys
    await client.post(_base(test_tenant, test_project), json={"name": "Key 1"})
    await client.post(_base(test_tenant, test_project), json={"name": "Key 2"})

    resp = await client.get(_base(test_tenant, test_project))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    # full_key should NOT appear in list response
    for key in data:
        assert "full_key" not in key


# ---------------------------------------------------------------------------
# Revoke API key
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_revoke_api_key(client: AsyncClient, test_tenant, test_project):
    create_resp = await client.post(
        _base(test_tenant, test_project), json={"name": "To Revoke"},
    )
    key_id = create_resp.json()["id"]

    resp = await client.delete(f"{_base(test_tenant, test_project)}/{key_id}")
    assert resp.status_code == 204

    # Verify it shows as revoked in the list
    resp = await client.get(_base(test_tenant, test_project))
    revoked = [k for k in resp.json() if k["id"] == key_id]
    assert len(revoked) == 1
    assert revoked[0]["revoked_at"] is not None


@pytest.mark.asyncio
async def test_revoke_api_key_not_found(client: AsyncClient, test_tenant, test_project):
    resp = await client.delete(f"{_base(test_tenant, test_project)}/{uuid.uuid4()}")
    assert resp.status_code == 404
