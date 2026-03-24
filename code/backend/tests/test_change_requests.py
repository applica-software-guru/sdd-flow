"""Tests for /api/v1/tenants/{tid}/projects/{pid}/change-requests endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.change_request import ChangeRequest, CRStatus
from app.models.project import Project
from app.models.tenant import Tenant
from app.models.user import User


def _base(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/change-requests"


@pytest.fixture
async def cr_payload():
    return {
        "title": "Add login page",
        "body": "We need a login page with email/password",
    }


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_cr(client: AsyncClient, test_tenant, test_project, test_user: User, cr_payload):
    resp = await client.post(_base(test_tenant, test_project), json=cr_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == cr_payload["title"]
    assert data["status"] == "draft"
    assert data["author_id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_create_cr_assigns_number_and_slug(client: AsyncClient, test_tenant, test_project, cr_payload):
    resp = await client.post(_base(test_tenant, test_project), json=cr_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["number"] == 1
    assert data["formatted_number"] == "001"
    assert data["slug"] == "add-login-page"


@pytest.mark.asyncio
async def test_create_cr_sequential_numbering(client: AsyncClient, test_tenant, test_project):
    r1 = await client.post(_base(test_tenant, test_project), json={"title": "First CR", "body": "b"})
    r2 = await client.post(_base(test_tenant, test_project), json={"title": "Second CR", "body": "b"})
    r3 = await client.post(_base(test_tenant, test_project), json={"title": "Third CR", "body": "b"})
    assert r1.json()["number"] == 1
    assert r2.json()["number"] == 2
    assert r3.json()["number"] == 3
    assert r3.json()["formatted_number"] == "003"


@pytest.mark.asyncio
async def test_create_cr_slug_dedup(client: AsyncClient, test_tenant, test_project):
    r1 = await client.post(_base(test_tenant, test_project), json={"title": "Fix auth", "body": "b"})
    r2 = await client.post(_base(test_tenant, test_project), json={"title": "Fix auth", "body": "b"})
    assert r1.json()["slug"] == "fix-auth"
    assert r2.json()["slug"] == "fix-auth-2"


@pytest.mark.asyncio
async def test_create_cr_with_target_files(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_base(test_tenant, test_project), json={
        "title": "Refactor utils",
        "body": "Clean up utility functions",
        "target_files": ["src/utils.py", "src/helpers.py"],
    })
    assert resp.status_code == 201
    assert resp.json()["target_files"] == ["src/utils.py", "src/helpers.py"]


@pytest.mark.asyncio
async def test_create_cr_missing_body(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_base(test_tenant, test_project), json={
        "title": "No body",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_crs(client: AsyncClient, test_tenant, test_project, cr_payload):
    # Create two CRs
    await client.post(_base(test_tenant, test_project), json=cr_payload)
    await client.post(_base(test_tenant, test_project), json={
        "title": "Second CR", "body": "body2",
    })

    resp = await client.get(_base(test_tenant, test_project))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


@pytest.mark.asyncio
async def test_list_crs_items_include_number_and_slug(client: AsyncClient, test_tenant, test_project):
    await client.post(_base(test_tenant, test_project), json={"title": "Some CR", "body": "b"})
    resp = await client.get(_base(test_tenant, test_project))
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert "number" in item
    assert "formatted_number" in item
    assert "slug" in item


@pytest.mark.asyncio
async def test_list_crs_with_status_filter(client: AsyncClient, test_tenant, test_project, cr_payload):
    await client.post(_base(test_tenant, test_project), json=cr_payload)
    resp = await client.get(_base(test_tenant, test_project), params={"status": "draft"})
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["status"] == "draft"


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_cr(client: AsyncClient, test_tenant, test_project, cr_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=cr_payload)
    cr_id = create_resp.json()["id"]

    resp = await client.get(f"{_base(test_tenant, test_project)}/{cr_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == cr_id
    assert "number" in data
    assert "formatted_number" in data
    assert "slug" in data


@pytest.mark.asyncio
async def test_get_cr_not_found(client: AsyncClient, test_tenant, test_project):
    resp = await client.get(f"{_base(test_tenant, test_project)}/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_cr(client: AsyncClient, test_tenant, test_project, cr_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=cr_payload)
    cr_id = create_resp.json()["id"]

    resp = await client.patch(
        f"{_base(test_tenant, test_project)}/{cr_id}",
        json={"title": "Updated title"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated title"


@pytest.mark.asyncio
async def test_update_cr_slug_is_immutable(client: AsyncClient, test_tenant, test_project, cr_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=cr_payload)
    original_slug = create_resp.json()["slug"]
    cr_id = create_resp.json()["id"]

    resp = await client.patch(
        f"{_base(test_tenant, test_project)}/{cr_id}",
        json={"title": "Renamed CR", "slug": "hacker-slug"},
    )
    assert resp.status_code == 200
    # slug must not have changed
    assert resp.json()["slug"] == original_slug


@pytest.mark.asyncio
async def test_update_cr_number_is_immutable(client: AsyncClient, test_tenant, test_project, cr_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=cr_payload)
    original_number = create_resp.json()["number"]
    cr_id = create_resp.json()["id"]

    resp = await client.patch(
        f"{_base(test_tenant, test_project)}/{cr_id}",
        json={"title": "Renamed CR"},
    )
    assert resp.status_code == 200
    assert resp.json()["number"] == original_number


# ---------------------------------------------------------------------------
# Transition
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_transition_cr(client: AsyncClient, test_tenant, test_project, cr_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=cr_payload)
    cr_id = create_resp.json()["id"]

    resp = await client.post(
        f"{_base(test_tenant, test_project)}/{cr_id}/transition",
        json={"status": "approved"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    # Transition to closed should set closed_at
    resp = await client.post(
        f"{_base(test_tenant, test_project)}/{cr_id}/transition",
        json={"status": "closed"},
    )
    assert resp.status_code == 200
    assert resp.json()["closed_at"] is not None


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_and_list_comments(client: AsyncClient, test_tenant, test_project, cr_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=cr_payload)
    cr_id = create_resp.json()["id"]

    # Add comment
    resp = await client.post(
        f"{_base(test_tenant, test_project)}/{cr_id}/comments",
        json={"body": "Looks good to me!"},
    )
    assert resp.status_code == 201
    assert resp.json()["body"] == "Looks good to me!"

    # List comments
    resp = await client.get(f"{_base(test_tenant, test_project)}/{cr_id}/comments")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
