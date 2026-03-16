"""Tests for /api/v1/tenants/{tid}/search endpoint."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log_entry import AuditLogEntry
from app.models.bug import Bug
from app.models.change_request import ChangeRequest
from app.models.document_file import DocumentFile
from app.models.project import Project
from app.models.tenant import Tenant
from app.models.user import User


def _url(tenant: Tenant) -> str:
    return f"/api/v1/tenants/{tenant.id}/search"


# ---------------------------------------------------------------------------
# Fixtures: seed searchable data
# ---------------------------------------------------------------------------

@pytest.fixture
async def search_data(db_session: AsyncSession, test_tenant: Tenant, test_project: Project, test_user: User):
    """Create one of each entity type with known searchable content."""
    doc = DocumentFile(
        project_id=test_project.id,
        path="product/search-test.md",
        title="Searchable Doc Title",
        content="This document contains the keyword foobar for testing",
        status="synced",
        version=1,
    )
    cr = ChangeRequest(
        project_id=test_project.id,
        title="Searchable CR foobar",
        body="Change request body with keyword",
        status="draft",
        author_id=test_user.id,
    )
    bug = Bug(
        project_id=test_project.id,
        title="Searchable Bug foobar",
        body="Bug body with keyword",
        status="open",
        severity="minor",
        author_id=test_user.id,
    )
    audit = AuditLogEntry(
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        event_type="cr.created.foobar",
        entity_type="change_request",
        entity_id=cr.id if cr.id else uuid.uuid4(),
        details={"action": "created", "keyword": "foobar"},
    )
    db_session.add_all([doc, cr, bug, audit])
    await db_session.commit()
    return {"doc": doc, "cr": cr, "bug": bug, "audit": audit}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_requires_query(client: AsyncClient, test_tenant):
    resp = await client.get(_url(test_tenant))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_returns_all_entity_types(client: AsyncClient, test_tenant, test_project, search_data):
    resp = await client.get(_url(test_tenant), params={"q": "foobar"})
    assert resp.status_code == 200
    data = resp.json()
    types_found = {r["entity_type"] for r in data["results"]}
    assert "project" not in types_found  # project name doesn't contain foobar
    assert "document" in types_found
    assert "change_request" in types_found
    assert "bug" in types_found
    assert "audit_log" in types_found


@pytest.mark.asyncio
async def test_search_filter_by_type_cr(client: AsyncClient, test_tenant, test_project, search_data):
    resp = await client.get(_url(test_tenant), params={"q": "foobar", "type": "cr"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) > 0
    assert all(r["entity_type"] == "change_request" for r in data["results"])


@pytest.mark.asyncio
async def test_search_filter_by_type_bug(client: AsyncClient, test_tenant, test_project, search_data):
    resp = await client.get(_url(test_tenant), params={"q": "foobar", "type": "bug"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) > 0
    assert all(r["entity_type"] == "bug" for r in data["results"])


@pytest.mark.asyncio
async def test_search_filter_by_type_doc(client: AsyncClient, test_tenant, test_project, search_data):
    resp = await client.get(_url(test_tenant), params={"q": "foobar", "type": "doc"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) > 0
    assert all(r["entity_type"] == "document" for r in data["results"])


@pytest.mark.asyncio
async def test_search_filter_by_type_audit_log(client: AsyncClient, test_tenant, test_project, search_data):
    resp = await client.get(_url(test_tenant), params={"q": "foobar", "type": "audit_log"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) > 0
    assert all(r["entity_type"] == "audit_log" for r in data["results"])


@pytest.mark.asyncio
async def test_search_filter_by_type_project(client: AsyncClient, test_tenant, test_project, search_data):
    resp = await client.get(_url(test_tenant), params={"q": "Test Project", "type": "project"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) > 0
    assert all(r["entity_type"] == "project" for r in data["results"])


@pytest.mark.asyncio
async def test_search_no_results(client: AsyncClient, test_tenant):
    resp = await client.get(_url(test_tenant), params={"q": "zzz_nonexistent_zzz"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_search_invalid_type_filter(client: AsyncClient, test_tenant):
    resp = await client.get(_url(test_tenant), params={"q": "test", "type": "invalid"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_result_structure(client: AsyncClient, test_tenant, test_project, search_data):
    resp = await client.get(_url(test_tenant), params={"q": "foobar", "type": "cr"})
    assert resp.status_code == 200
    result = resp.json()["results"][0]
    assert "entity_type" in result
    assert "entity_id" in result
    assert "title" in result
    assert "snippet" in result
    assert "project_id" in result
