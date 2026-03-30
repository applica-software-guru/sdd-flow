"""
Tests that verify cross-project access is correctly denied.
Resources belonging to project A must not be accessible via project B URLs.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models.bug import Bug
from app.models.change_request import ChangeRequest
from app.models.document_file import DocumentFile
from app.models.project import Project
from app.models.tenant import Tenant


@pytest.fixture
async def second_project(test_tenant: Tenant, unique_id: str) -> Project:
    project = Project(
        tenant_id=test_tenant.id,
        name=f"Second Project {unique_id}",
        slug=f"second-proj-{unique_id}",
    )
    await project.insert()
    yield project
    await project.delete()


def _bugs(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/bugs"


def _crs(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/change-requests"


def _docs(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/docs"


@pytest.mark.asyncio
async def test_get_bug_from_wrong_project(
    client: AsyncClient, test_tenant, test_project, second_project
):
    resp = await client.post(_bugs(test_tenant, test_project), json={
        "title": "Bug in project 1", "body": "body", "severity": "minor"
    })
    bug_id = resp.json()["id"]

    # Try to access it via the second project's URL
    resp = await client.get(f"{_bugs(test_tenant, second_project)}/{bug_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_cr_from_wrong_project(
    client: AsyncClient, test_tenant, test_project, second_project
):
    resp = await client.post(_crs(test_tenant, test_project), json={
        "title": "CR in project 1", "body": "body"
    })
    cr_id = resp.json()["id"]

    resp = await client.get(f"{_crs(test_tenant, second_project)}/{cr_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_doc_from_wrong_project(
    client: AsyncClient, test_tenant, test_project, second_project
):
    resp = await client.post(_docs(test_tenant, test_project), json={
        "path": "product/test.md",
        "title": "Doc in project 1",
        "content": "# Test",
        "status": "synced",
        "version": "1.0",
    })
    doc_id = resp.json()["id"]

    resp = await client.get(f"{_docs(test_tenant, second_project)}/{doc_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_bug_from_wrong_project(
    client: AsyncClient, test_tenant, test_project, second_project
):
    resp = await client.post(_bugs(test_tenant, test_project), json={
        "title": "Bug", "body": "body", "severity": "minor"
    })
    bug_id = resp.json()["id"]

    resp = await client.patch(
        f"{_bugs(test_tenant, second_project)}/{bug_id}",
        json={"title": "Hacked title"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_transition_bug_from_wrong_project(
    client: AsyncClient, test_tenant, test_project, second_project
):
    resp = await client.post(_bugs(test_tenant, test_project), json={
        "title": "Bug", "body": "body", "severity": "minor"
    })
    bug_id = resp.json()["id"]

    resp = await client.post(
        f"{_bugs(test_tenant, second_project)}/{bug_id}/transition",
        json={"status": "open"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_bugs_does_not_leak_across_projects(
    client: AsyncClient, test_tenant, test_project, second_project
):
    resp = await client.post(_bugs(test_tenant, test_project), json={
        "title": "Project 1 bug", "body": "body", "severity": "minor"
    })
    bug_id = resp.json()["id"]

    # List bugs for second project — must not contain the bug from project 1
    resp = await client.get(_bugs(test_tenant, second_project))
    ids = [i["id"] for i in resp.json()["items"]]
    assert bug_id not in ids
