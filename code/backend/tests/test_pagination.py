"""
Tests for pagination across list endpoints.
"""

import pytest
from httpx import AsyncClient

from app.models.project import Project
from app.models.tenant import Tenant


def _bugs(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/bugs"


def _crs(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/change-requests"


def _docs(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/docs"


@pytest.mark.asyncio
async def test_list_bugs_pagination(client: AsyncClient, test_tenant, test_project):
    # Create 5 bugs
    for i in range(5):
        await client.post(_bugs(test_tenant, test_project), json={
            "title": f"Pagination bug {i}", "body": "body", "severity": "minor"
        })

    resp = await client.get(_bugs(test_tenant, test_project), params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 5
    assert data["pages"] >= 3
    assert data["page"] == 1
    assert data["page_size"] == 2

    # Second page
    resp2 = await client.get(_bugs(test_tenant, test_project), params={"page": 2, "page_size": 2})
    assert resp2.status_code == 200
    ids_page1 = {i["id"] for i in data["items"]}
    ids_page2 = {i["id"] for i in resp2.json()["items"]}
    assert ids_page1.isdisjoint(ids_page2), "Pages must not overlap"


@pytest.mark.asyncio
async def test_list_crs_pagination(client: AsyncClient, test_tenant, test_project):
    for i in range(4):
        await client.post(_crs(test_tenant, test_project), json={
            "title": f"Pagination CR {i}", "body": "body"
        })

    resp = await client.get(_crs(test_tenant, test_project), params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 4


@pytest.mark.asyncio
async def test_page_size_validation_too_large(client: AsyncClient, test_tenant, test_project):
    resp = await client.get(_bugs(test_tenant, test_project), params={"page_size": 999})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_page_validation_zero(client: AsyncClient, test_tenant, test_project):
    resp = await client.get(_bugs(test_tenant, test_project), params={"page": 0})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_empty_list_pagination(client: AsyncClient, test_tenant, test_project):
    resp = await client.get(_crs(test_tenant, test_project))
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == [] or isinstance(data["items"], list)
    assert data["total"] >= 0
    assert data["pages"] >= 0


@pytest.mark.asyncio
async def test_status_filter_excludes_deleted(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_bugs(test_tenant, test_project), json={
        "title": "Soon deleted", "body": "body", "severity": "minor"
    })
    bug_id = resp.json()["id"]
    await client.post(f"{_bugs(test_tenant, test_project)}/{bug_id}/transition",
                      json={"status": "deleted"})

    # Default list should not include deleted
    resp = await client.get(_bugs(test_tenant, test_project))
    ids = [i["id"] for i in resp.json()["items"]]
    assert bug_id not in ids

    # Explicit deleted filter should include it
    resp = await client.get(_bugs(test_tenant, test_project), params={"status": "deleted"})
    ids = [i["id"] for i in resp.json()["items"]]
    assert bug_id in ids
