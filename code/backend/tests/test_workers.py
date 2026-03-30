"""
Tests for worker and worker-job endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models.project import Project
from app.models.tenant import Tenant
from app.models.worker_job import JobStatus


def _workers(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/workers"


def _jobs(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/worker-jobs"


def _preview(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/worker-jobs/preview"


def _agent_models(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/worker-jobs/agent-models"


# ---------------------------------------------------------------------------
# Workers list
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_workers_empty(client: AsyncClient, test_tenant: Tenant, test_project: Project):
    resp = await client.get(_workers(test_tenant, test_project))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_agent_models(client: AsyncClient, test_tenant: Tenant, test_project: Project):
    resp = await client.get(_agent_models(test_tenant, test_project))
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert len(data) > 0


# ---------------------------------------------------------------------------
# Create worker jobs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_build_job(client: AsyncClient, test_tenant: Tenant, test_project: Project):
    resp = await client.post(_jobs(test_tenant, test_project), json={"job_type": "build"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["job_type"] == "build"
    assert data["status"] == "queued"
    assert data["project_id"] == str(test_project.id)


@pytest.mark.asyncio
async def test_create_custom_job_requires_prompt(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    resp = await client.post(_jobs(test_tenant, test_project), json={"job_type": "custom"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_custom_job_with_prompt(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    resp = await client.post(_jobs(test_tenant, test_project), json={
        "job_type": "custom",
        "prompt": "Do something useful",
    })
    assert resp.status_code == 201
    assert resp.json()["job_type"] == "custom"


@pytest.mark.asyncio
async def test_create_enrich_job_requires_entity(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    """An enrich job without entity_type/entity_id must return 400."""
    resp = await client.post(_jobs(test_tenant, test_project), json={"job_type": "enrich"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_job_with_unknown_worker_returns_404(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    resp = await client.post(_jobs(test_tenant, test_project), json={
        "job_type": "build",
        "worker_id": str(uuid.uuid4()),
    })
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# List / get jobs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_worker_jobs(client: AsyncClient, test_tenant: Tenant, test_project: Project):
    await client.post(_jobs(test_tenant, test_project), json={"job_type": "build"})

    resp = await client.get(_jobs(test_tenant, test_project))
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_worker_jobs_filter_by_status(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    await client.post(_jobs(test_tenant, test_project), json={"job_type": "build"})

    resp = await client.get(_jobs(test_tenant, test_project), params={"status": "queued"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(i["status"] == "queued" for i in items)


@pytest.mark.asyncio
async def test_get_worker_job(client: AsyncClient, test_tenant: Tenant, test_project: Project):
    create_resp = await client.post(_jobs(test_tenant, test_project), json={"job_type": "build"})
    job_id = create_resp.json()["id"]

    resp = await client.get(f"{_jobs(test_tenant, test_project)}/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == job_id
    assert "messages" in data


@pytest.mark.asyncio
async def test_get_worker_job_not_found(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    resp = await client.get(f"{_jobs(test_tenant, test_project)}/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cancel_queued_job(client: AsyncClient, test_tenant: Tenant, test_project: Project):
    create_resp = await client.post(_jobs(test_tenant, test_project), json={"job_type": "build"})
    job_id = create_resp.json()["id"]

    resp = await client.post(f"{_jobs(test_tenant, test_project)}/{job_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    # Verify persisted status
    get_resp = await client.get(f"{_jobs(test_tenant, test_project)}/{job_id}")
    assert get_resp.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_already_cancelled_job_returns_400(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    create_resp = await client.post(_jobs(test_tenant, test_project), json={"job_type": "build"})
    job_id = create_resp.json()["id"]

    await client.post(f"{_jobs(test_tenant, test_project)}/{job_id}/cancel")

    resp = await client.post(f"{_jobs(test_tenant, test_project)}/{job_id}/cancel")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_preview_build_job(client: AsyncClient, test_tenant: Tenant, test_project: Project):
    resp = await client.post(_preview(test_tenant, test_project), json={"job_type": "build"})
    assert resp.status_code == 200
    assert "prompt" in resp.json()


@pytest.mark.asyncio
async def test_preview_custom_job_returns_empty_prompt(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    resp = await client.post(_preview(test_tenant, test_project), json={"job_type": "custom"})
    assert resp.status_code == 200
    assert resp.json()["prompt"] == ""


@pytest.mark.asyncio
async def test_preview_enrich_job_requires_entity(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    resp = await client.post(_preview(test_tenant, test_project), json={"job_type": "enrich"})
    assert resp.status_code == 400
