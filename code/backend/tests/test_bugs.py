"""Tests for /api/v1/tenants/{tid}/projects/{pid}/bugs endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.project import Project
from app.models.tenant import Tenant
from app.models.user import User


def _base(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/bugs"


@pytest.fixture
def bug_payload():
    return {
        "title": "Button not clickable",
        "body": "The submit button on the form does not respond to clicks",
        "severity": "major",
    }


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_bug(client: AsyncClient, test_tenant, test_project, test_user: User, bug_payload):
    resp = await client.post(_base(test_tenant, test_project), json=bug_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == bug_payload["title"]
    assert data["status"] == "draft"
    assert data["severity"] == "major"
    assert data["author_id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_create_bug_assigns_number_and_slug(client: AsyncClient, test_tenant, test_project, bug_payload):
    resp = await client.post(_base(test_tenant, test_project), json=bug_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["number"] == 1
    assert data["formatted_number"] == "001"
    assert data["slug"] == "button-not-clickable"


@pytest.mark.asyncio
async def test_create_bug_sequential_numbering(client: AsyncClient, test_tenant, test_project):
    r1 = await client.post(_base(test_tenant, test_project), json={"title": "Bug one", "body": "b", "severity": "minor"})
    r2 = await client.post(_base(test_tenant, test_project), json={"title": "Bug two", "body": "b", "severity": "minor"})
    r3 = await client.post(_base(test_tenant, test_project), json={"title": "Bug three", "body": "b", "severity": "minor"})
    assert r1.json()["number"] == 1
    assert r2.json()["number"] == 2
    assert r3.json()["number"] == 3
    assert r3.json()["formatted_number"] == "003"


@pytest.mark.asyncio
async def test_create_bug_slug_dedup(client: AsyncClient, test_tenant, test_project):
    r1 = await client.post(_base(test_tenant, test_project), json={"title": "Login crash", "body": "b", "severity": "major"})
    r2 = await client.post(_base(test_tenant, test_project), json={"title": "Login crash", "body": "b", "severity": "minor"})
    assert r1.json()["slug"] == "login-crash"
    assert r2.json()["slug"] == "login-crash-2"


@pytest.mark.asyncio
async def test_create_bug_missing_severity(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_base(test_tenant, test_project), json={
        "title": "No severity",
        "body": "missing required field",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_bug_invalid_severity(client: AsyncClient, test_tenant, test_project):
    resp = await client.post(_base(test_tenant, test_project), json={
        "title": "Bad sev",
        "body": "bad",
        "severity": "catastrophic",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_bugs(client: AsyncClient, test_tenant, test_project, bug_payload):
    await client.post(_base(test_tenant, test_project), json=bug_payload)
    resp = await client.get(_base(test_tenant, test_project))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_list_bugs_items_include_number_and_slug(client: AsyncClient, test_tenant, test_project, bug_payload):
    await client.post(_base(test_tenant, test_project), json=bug_payload)
    resp = await client.get(_base(test_tenant, test_project))
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert "number" in item
    assert "formatted_number" in item
    assert "slug" in item


@pytest.mark.asyncio
async def test_list_bugs_filter_by_status(client: AsyncClient, test_tenant, test_project, bug_payload):
    await client.post(_base(test_tenant, test_project), json=bug_payload)
    resp = await client.get(_base(test_tenant, test_project), params={"status": "open"})
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["status"] == "open"


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_bug(client: AsyncClient, test_tenant, test_project, bug_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=bug_payload)
    bug_id = create_resp.json()["id"]

    resp = await client.get(f"{_base(test_tenant, test_project)}/{bug_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == bug_id
    assert "number" in data
    assert "formatted_number" in data
    assert "slug" in data


@pytest.mark.asyncio
async def test_get_bug_not_found(client: AsyncClient, test_tenant, test_project):
    resp = await client.get(f"{_base(test_tenant, test_project)}/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_bug(client: AsyncClient, test_tenant, test_project, bug_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=bug_payload)
    bug_id = create_resp.json()["id"]

    resp = await client.patch(
        f"{_base(test_tenant, test_project)}/{bug_id}",
        json={"title": "Updated bug title", "severity": "critical"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated bug title"
    assert resp.json()["severity"] == "critical"


@pytest.mark.asyncio
async def test_update_bug_slug_is_immutable(client: AsyncClient, test_tenant, test_project, bug_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=bug_payload)
    original_slug = create_resp.json()["slug"]
    bug_id = create_resp.json()["id"]

    resp = await client.patch(
        f"{_base(test_tenant, test_project)}/{bug_id}",
        json={"title": "Renamed bug", "slug": "hacker-slug"},
    )
    assert resp.status_code == 200
    assert resp.json()["slug"] == original_slug


@pytest.mark.asyncio
async def test_update_bug_number_is_immutable(client: AsyncClient, test_tenant, test_project, bug_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=bug_payload)
    original_number = create_resp.json()["number"]
    bug_id = create_resp.json()["id"]

    resp = await client.patch(
        f"{_base(test_tenant, test_project)}/{bug_id}",
        json={"title": "Renamed bug"},
    )
    assert resp.status_code == 200
    assert resp.json()["number"] == original_number


# ---------------------------------------------------------------------------
# Transition
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_transition_bug(client: AsyncClient, test_tenant, test_project, bug_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=bug_payload)
    bug_id = create_resp.json()["id"]

    resp = await client.post(
        f"{_base(test_tenant, test_project)}/{bug_id}/transition",
        json={"status": "in_progress"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"

    # Transition to resolved should set closed_at
    resp = await client.post(
        f"{_base(test_tenant, test_project)}/{bug_id}/transition",
        json={"status": "resolved"},
    )
    assert resp.status_code == 200
    assert resp.json()["closed_at"] is not None


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_and_list_bug_comments(client: AsyncClient, test_tenant, test_project, bug_payload):
    create_resp = await client.post(_base(test_tenant, test_project), json=bug_payload)
    bug_id = create_resp.json()["id"]

    resp = await client.post(
        f"{_base(test_tenant, test_project)}/{bug_id}/comments",
        json={"body": "I can reproduce this on Chrome"},
    )
    assert resp.status_code == 201

    resp = await client.get(f"{_base(test_tenant, test_project)}/{bug_id}/comments")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    assert resp.json()[0]["body"] == "I can reproduce this on Chrome"
