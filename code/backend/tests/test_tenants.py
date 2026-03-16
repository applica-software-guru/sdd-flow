"""Tests for /api/v1/tenants endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant


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
