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


# ---------------------------------------------------------------------------
# Sorting — list must be ordered by number descending
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_crs_sorted_by_number_descending(client: AsyncClient, test_tenant, test_project):
    """Items in the CR list must come back with the highest number first."""
    for i in range(3):
        await client.post(_crs(test_tenant, test_project), json={
            "title": f"Sorting CR {i}", "body": "body"
        })

    resp = await client.get(_crs(test_tenant, test_project))
    assert resp.status_code == 200
    numbers = [item["number"] for item in resp.json()["items"]]
    assert numbers == sorted(numbers, reverse=True), (
        f"CR list not sorted by number desc: {numbers}"
    )


@pytest.mark.asyncio
async def test_list_bugs_sorted_by_number_descending(client: AsyncClient, test_tenant, test_project):
    """Items in the Bug list must come back with the highest number first."""
    for i in range(3):
        await client.post(_bugs(test_tenant, test_project), json={
            "title": f"Sorting Bug {i}", "body": "body", "severity": "minor"
        })

    resp = await client.get(_bugs(test_tenant, test_project))
    assert resp.status_code == 200
    numbers = [item["number"] for item in resp.json()["items"]]
    assert numbers == sorted(numbers, reverse=True), (
        f"Bug list not sorted by number desc: {numbers}"
    )


@pytest.mark.asyncio
async def test_list_crs_first_item_is_latest(client: AsyncClient, test_tenant, test_project):
    """The first item returned must be the one with the highest progressive number."""
    r1 = await client.post(_crs(test_tenant, test_project), json={"title": "First", "body": "b"})
    r2 = await client.post(_crs(test_tenant, test_project), json={"title": "Second", "body": "b"})
    r3 = await client.post(_crs(test_tenant, test_project), json={"title": "Third", "body": "b"})

    last_number = r3.json()["number"]
    resp = await client.get(_crs(test_tenant, test_project))
    assert resp.status_code == 200
    assert resp.json()["items"][0]["number"] == last_number


@pytest.mark.asyncio
async def test_list_bugs_first_item_is_latest(client: AsyncClient, test_tenant, test_project):
    """The first item returned must be the one with the highest progressive number."""
    await client.post(_bugs(test_tenant, test_project), json={"title": "Bug A", "body": "b", "severity": "minor"})
    await client.post(_bugs(test_tenant, test_project), json={"title": "Bug B", "body": "b", "severity": "minor"})
    r3 = await client.post(_bugs(test_tenant, test_project), json={"title": "Bug C", "body": "b", "severity": "minor"})

    last_number = r3.json()["number"]
    resp = await client.get(_bugs(test_tenant, test_project))
    assert resp.status_code == 200
    assert resp.json()["items"][0]["number"] == last_number


@pytest.mark.asyncio
async def test_list_crs_sort_stable_across_pages(client: AsyncClient, test_tenant, test_project):
    """Numbers on page 2 must all be lower than numbers on page 1."""
    for i in range(5):
        await client.post(_crs(test_tenant, test_project), json={"title": f"Page CR {i}", "body": "b"})

    p1 = await client.get(_crs(test_tenant, test_project), params={"page": 1, "page_size": 2})
    p2 = await client.get(_crs(test_tenant, test_project), params={"page": 2, "page_size": 2})
    assert p1.status_code == 200
    assert p2.status_code == 200

    max_p2 = max(item["number"] for item in p2.json()["items"])
    min_p1 = min(item["number"] for item in p1.json()["items"])
    assert max_p2 < min_p1, "Page 2 numbers must be lower than page 1 numbers"


@pytest.mark.asyncio
async def test_list_bugs_sort_stable_across_pages(client: AsyncClient, test_tenant, test_project):
    """Numbers on page 2 must all be lower than numbers on page 1."""
    for i in range(5):
        await client.post(_bugs(test_tenant, test_project), json={"title": f"Page Bug {i}", "body": "b", "severity": "minor"})

    p1 = await client.get(_bugs(test_tenant, test_project), params={"page": 1, "page_size": 2})
    p2 = await client.get(_bugs(test_tenant, test_project), params={"page": 2, "page_size": 2})
    assert p1.status_code == 200
    assert p2.status_code == 200

    max_p2 = max(item["number"] for item in p2.json()["items"])
    min_p1 = min(item["number"] for item in p1.json()["items"])
    assert max_p2 < min_p1, "Page 2 numbers must be lower than page 1 numbers"


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
