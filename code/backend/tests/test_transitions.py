"""
Tests for terminal-state guards and status transition edge cases on Bugs and CRs.
"""

import pytest
from httpx import AsyncClient

from app.models.bug import Bug, BugStatus
from app.models.change_request import ChangeRequest, CRStatus
from app.models.project import Project
from app.models.tenant import Tenant


def _bugs(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/bugs"


def _crs(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/change-requests"


# ---------------------------------------------------------------------------
# Bug terminal state guards
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cannot_transition_closed_bug(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_bugs(test_tenant, test_project), json={
        "title": "Closed bug", "body": "body", "severity": "minor"
    })
    bug_id = resp.json()["id"]

    # Close it
    await client.post(f"{_bugs(test_tenant, test_project)}/{bug_id}/transition",
                      json={"status": "closed"})

    # Attempt to re-transition a closed bug
    resp = await client.post(f"{_bugs(test_tenant, test_project)}/{bug_id}/transition",
                             json={"status": "open"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_cannot_transition_deleted_bug(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_bugs(test_tenant, test_project), json={
        "title": "Deleted bug", "body": "body", "severity": "minor"
    })
    bug_id = resp.json()["id"]

    await client.post(f"{_bugs(test_tenant, test_project)}/{bug_id}/transition",
                      json={"status": "deleted"})

    resp = await client.post(f"{_bugs(test_tenant, test_project)}/{bug_id}/transition",
                             json={"status": "open"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_bug_valid_transitions(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_bugs(test_tenant, test_project), json={
        "title": "Transition test", "body": "body", "severity": "major"
    })
    assert resp.status_code == 201
    bug_id = resp.json()["id"]

    for new_status in ("open", "in_progress", "resolved"):
        resp = await client.post(
            f"{_bugs(test_tenant, test_project)}/{bug_id}/transition",
            json={"status": new_status},
        )
        assert resp.status_code == 200, f"Transition to {new_status} failed: {resp.text}"
        assert resp.json()["status"] == new_status


@pytest.mark.asyncio
async def test_resolved_bug_sets_closed_at(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_bugs(test_tenant, test_project), json={
        "title": "Resolved bug", "body": "body", "severity": "trivial"
    })
    bug_id = resp.json()["id"]

    resp = await client.post(f"{_bugs(test_tenant, test_project)}/{bug_id}/transition",
                             json={"status": "resolved"})
    assert resp.status_code == 200
    assert resp.json()["closed_at"] is not None


# ---------------------------------------------------------------------------
# CR terminal state guards
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cannot_transition_closed_cr(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_crs(test_tenant, test_project), json={
        "title": "Closed CR", "body": "body"
    })
    cr_id = resp.json()["id"]

    await client.post(f"{_crs(test_tenant, test_project)}/{cr_id}/transition",
                      json={"status": "closed"})

    resp = await client.post(f"{_crs(test_tenant, test_project)}/{cr_id}/transition",
                             json={"status": "pending"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_cannot_transition_deleted_cr(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_crs(test_tenant, test_project), json={
        "title": "Deleted CR", "body": "body"
    })
    cr_id = resp.json()["id"]

    await client.post(f"{_crs(test_tenant, test_project)}/{cr_id}/transition",
                      json={"status": "deleted"})

    resp = await client.post(f"{_crs(test_tenant, test_project)}/{cr_id}/transition",
                             json={"status": "pending"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_cr_applied_sets_closed_at(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_crs(test_tenant, test_project), json={
        "title": "Applied CR", "body": "body"
    })
    cr_id = resp.json()["id"]

    resp = await client.post(f"{_crs(test_tenant, test_project)}/{cr_id}/transition",
                             json={"status": "applied"})
    assert resp.status_code == 200
    assert resp.json()["closed_at"] is not None


@pytest.mark.asyncio
async def test_cr_formatted_number(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_crs(test_tenant, test_project), json={
        "title": "Numbered CR", "body": "body"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "formatted_number" in data
    assert data["formatted_number"].isdigit() or data["formatted_number"][0].isdigit()
