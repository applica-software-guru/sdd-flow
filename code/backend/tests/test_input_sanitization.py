"""
Tests verifying that HTML/script content in input fields is stored as-is
and returned unchanged (no server-side injection risk from unescaped output).
The API is JSON-based so XSS risks live in the client, but we verify the
server does not strip or alter the content in unexpected ways.
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
async def test_bug_title_with_html_stored_as_is(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    html_title = "<script>alert('xss')</script> Bug"
    resp = await client.post(_bugs(test_tenant, test_project), json={
        "title": html_title,
        "body": "Normal body",
        "severity": "minor",
    })
    assert resp.status_code == 201
    assert resp.json()["title"] == html_title


@pytest.mark.asyncio
async def test_bug_body_with_html_stored_as_is(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    html_body = "<img src=x onerror=alert(1)> description"
    resp = await client.post(_bugs(test_tenant, test_project), json={
        "title": "Normal title",
        "body": html_body,
        "severity": "minor",
    })
    assert resp.status_code == 201
    assert resp.json()["body"] == html_body


@pytest.mark.asyncio
async def test_cr_title_with_script_tag_stored_as_is(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    script_title = "<script>evil()</script>"
    resp = await client.post(_crs(test_tenant, test_project), json={
        "title": script_title,
        "body": "body",
    })
    assert resp.status_code == 201
    assert resp.json()["title"] == script_title


@pytest.mark.asyncio
async def test_doc_title_with_html_stored_as_is(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    html_title = "<b>Bold</b> Doc"
    resp = await client.post(_docs(test_tenant, test_project), json={
        "path": "product/html-title.md",
        "title": html_title,
        "content": "# Test",
        "status": "synced",
        "version": "1.0",
    })
    assert resp.status_code == 201
    assert resp.json()["title"] == html_title


@pytest.mark.asyncio
async def test_very_long_title_is_rejected_or_stored(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    """A title of 10 000 characters should either be accepted or rejected with 422 — not crash."""
    long_title = "A" * 10_000
    resp = await client.post(_bugs(test_tenant, test_project), json={
        "title": long_title,
        "body": "body",
        "severity": "minor",
    })
    assert resp.status_code in (201, 422)


@pytest.mark.asyncio
async def test_unicode_title_roundtrips_correctly(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    emoji_title = "Bug: 🐛 TypeError in ñoño module"
    resp = await client.post(_bugs(test_tenant, test_project), json={
        "title": emoji_title,
        "body": "body",
        "severity": "trivial",
    })
    assert resp.status_code == 201
    assert resp.json()["title"] == emoji_title
