"""Tests for /api/v1/tenants/{tenant_id}/projects endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.project import Project
from app.models.tenant import Tenant


# ---------------------------------------------------------------------------
# Create project
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, test_tenant: Tenant):
    slug = f"p-{uuid.uuid4().hex[:8]}"
    resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/projects",
        json={"name": "New Project", "slug": slug, "description": "desc"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New Project"
    assert data["slug"] == slug
    assert data["tenant_id"] == str(test_tenant.id)


@pytest.mark.asyncio
async def test_create_project_duplicate_slug(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/projects",
        json={"name": "Dup", "slug": test_project.slug},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_project_validation_error(client: AsyncClient, test_tenant: Tenant):
    resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/projects",
        json={"description": "missing name and slug"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List projects
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, test_tenant: Tenant, test_project: Project):
    resp = await client.get(f"/api/v1/tenants/{test_tenant.id}/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(p["id"] == str(test_project.id) for p in data)


# ---------------------------------------------------------------------------
# Get project
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_project(client: AsyncClient, test_tenant: Tenant, test_project: Project):
    resp = await client.get(
        f"/api/v1/tenants/{test_tenant.id}/projects/{test_project.id}"
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == str(test_project.id)


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient, test_tenant: Tenant):
    resp = await client.get(
        f"/api/v1/tenants/{test_tenant.id}/projects/{uuid.uuid4()}"
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update project
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, test_tenant: Tenant, test_project: Project):
    resp = await client.patch(
        f"/api/v1/tenants/{test_tenant.id}/projects/{test_project.id}",
        json={"name": "Updated Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


# ---------------------------------------------------------------------------
# Archive / restore
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_archive_and_restore_project(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    # Archive
    resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/projects/{test_project.id}/archive"
    )
    assert resp.status_code == 200
    assert resp.json()["archived_at"] is not None

    # After archiving, list should exclude it
    resp = await client.get(f"/api/v1/tenants/{test_tenant.id}/projects")
    assert all(p["id"] != str(test_project.id) for p in resp.json())

    # Restore
    resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/projects/{test_project.id}/restore"
    )
    assert resp.status_code == 200
    assert resp.json()["archived_at"] is None
