"""Tests for /api/v1/tenants/{tenant_id}/projects endpoints."""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bug import Bug, BugSeverity, BugStatus
from app.models.change_request import ChangeRequest, CRStatus
from app.models.document_file import DocStatus, DocumentFile
from app.models.project import Project
from app.models.tenant import Tenant
from app.models.user import User


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


# ---------------------------------------------------------------------------
# Reset project
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def project_with_data(
    db_session: AsyncSession, test_project: Project, test_user: User
):
    """Populate a project with docs, CRs, and bugs for reset tests."""
    doc = DocumentFile(
        project_id=test_project.id,
        path="product/vision.md",
        title="Vision",
        content="# Vision",
        status=DocStatus.synced,
        version=1,
    )
    cr = ChangeRequest(
        project_id=test_project.id,
        path="change-requests/001-auth.md",
        title="Add auth",
        body="Implement JWT",
        status=CRStatus.pending,
        author_id=test_user.id,
        number=1,
        slug="add-auth",
    )
    bug = Bug(
        project_id=test_project.id,
        path="bugs/001-crash.md",
        title="Login crash",
        body="App crashes on login",
        status=BugStatus.open,
        severity=BugSeverity.major,
        author_id=test_user.id,
        number=1,
        slug="login-crash",
    )
    db_session.add_all([doc, cr, bug])
    await db_session.commit()
    return test_project


@pytest.mark.asyncio
async def test_reset_project(
    client: AsyncClient,
    test_tenant: Tenant,
    project_with_data: Project,
    db_session: AsyncSession,
):
    project = project_with_data
    resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/projects/{project.id}/reset",
        json={"confirm_slug": project.slug},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted_documents"] == 1
    assert data["deleted_change_requests"] == 1
    assert data["deleted_bugs"] == 1

    # Verify entities are gone
    docs = await db_session.execute(
        select(DocumentFile).where(DocumentFile.project_id == project.id)
    )
    assert docs.scalars().all() == []

    # Verify project still exists
    proj = await db_session.execute(
        select(Project).where(Project.id == project.id)
    )
    assert proj.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_reset_project_wrong_slug(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/projects/{test_project.id}/reset",
        json={"confirm_slug": "wrong-slug"},
    )
    assert resp.status_code == 400
    assert "Slug mismatch" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_reset_empty_project(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/projects/{test_project.id}/reset",
        json={"confirm_slug": test_project.slug},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted_documents"] == 0
    assert data["deleted_change_requests"] == 0
    assert data["deleted_bugs"] == 0
