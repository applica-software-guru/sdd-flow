"""Tests for /api/v1/tenants/{tid}/projects/{pid}/docs endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.project import Project
from app.models.tenant import Tenant


def _base(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/docs"


@pytest.fixture
def doc_payload():
    return {
        "path": "docs/architecture.md",
        "title": "Architecture Overview",
        "content": "# Architecture\n\nThis doc describes the system architecture.",
    }


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_doc(client: AsyncClient, test_tenant, test_project, doc_payload):
    resp = await client.post(_base(test_tenant, test_project), json=doc_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["path"] == doc_payload["path"]
    assert data["title"] == doc_payload["title"]
    assert data["status"] == "new"
    assert data["version"] == 1


@pytest.mark.asyncio
async def test_create_doc_duplicate_path(client: AsyncClient, test_tenant, test_project, doc_payload):
    await client.post(_base(test_tenant, test_project), json=doc_payload)
    resp = await client.post(_base(test_tenant, test_project), json=doc_payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_doc_missing_path(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_base(test_tenant, test_project), json={
        "title": "No path",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_docs(client: AsyncClient, test_tenant, test_project, doc_payload):
    await client.post(_base(test_tenant, test_project), json=doc_payload)
    resp = await client.get(_base(test_tenant, test_project))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_doc(client: AsyncClient, test_tenant, test_project, doc_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=doc_payload)
    doc_id = create_resp.json()["id"]

    resp = await client.get(f"{_base(test_tenant, test_project)}/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == doc_id
    assert resp.json()["content"] == doc_payload["content"]


@pytest.mark.asyncio
async def test_get_doc_not_found(client: AsyncClient, test_tenant, test_project):
    resp = await client.get(f"{_base(test_tenant, test_project)}/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_doc(client: AsyncClient, test_tenant, test_project, doc_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=doc_payload)
    doc_id = create_resp.json()["id"]

    resp = await client.patch(
        f"{_base(test_tenant, test_project)}/{doc_id}",
        json={"title": "Updated Title", "content": "New content"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated Title"
    assert data["content"] == "New content"
    assert data["status"] == "changed"
    assert data["version"] == 2


# ---------------------------------------------------------------------------
# Delete (soft-delete)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_doc(client: AsyncClient, test_tenant, test_project, doc_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=doc_payload)
    doc_id = create_resp.json()["id"]

    resp = await client.delete(f"{_base(test_tenant, test_project)}/{doc_id}")
    assert resp.status_code == 204

    # After deletion, the doc should not appear in list (status = deleted is filtered out)
    resp = await client.get(_base(test_tenant, test_project))
    assert all(d["id"] != doc_id for d in resp.json())


# ---------------------------------------------------------------------------
# Bulk upsert
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bulk_upsert(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(
        f"{_base(test_tenant, test_project)}/bulk",
        json={
            "documents": [
                {"path": "docs/a.md", "title": "Doc A", "content": "Content A"},
                {"path": "docs/b.md", "title": "Doc B", "content": "Content B"},
            ]
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == 2
    assert data["updated"] == 0
    assert len(data["documents"]) == 2

    # Upsert again -- should update existing
    resp = await client.post(
        f"{_base(test_tenant, test_project)}/bulk",
        json={
            "documents": [
                {"path": "docs/a.md", "title": "Doc A v2", "content": "Updated A"},
            ]
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == 0
    assert data["updated"] == 1
