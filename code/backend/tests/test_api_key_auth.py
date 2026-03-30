"""
Tests verifying that API keys work as authentication for CLI endpoints,
and that revoked/invalid keys are rejected.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.middleware.auth import get_current_tenant_member, get_current_user
from app.models.project import Project
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember


def _api_keys_url(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/api-keys"


def _cli_pending_crs_url() -> str:
    return "/api/v1/cli/pending-crs"


@pytest.mark.asyncio
async def test_api_key_authenticates_cli_endpoint(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    """A valid API key grants access to CLI endpoints."""
    # Create key via the authenticated client
    resp = await client.post(_api_keys_url(test_tenant, test_project), json={"name": "ci-key"})
    assert resp.status_code == 201
    full_key = resp.json()["full_key"]

    # Use the raw key as Bearer token against a CLI endpoint
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as raw:
        resp = await raw.get(
            _cli_pending_crs_url(),
            headers={"Authorization": f"Bearer {full_key}"},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_revoked_api_key_is_rejected(
    client: AsyncClient, test_tenant: Tenant, test_project: Project
):
    """After revoking a key, it must no longer authenticate."""
    resp = await client.post(_api_keys_url(test_tenant, test_project), json={"name": "temp-key"})
    assert resp.status_code == 201
    data = resp.json()
    full_key = data["full_key"]
    key_id = data["id"]

    # Revoke it
    rev = await client.delete(f"{_api_keys_url(test_tenant, test_project)}/{key_id}")
    assert rev.status_code == 204

    # Key should now be rejected
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as raw:
        resp = await raw.get(
            _cli_pending_crs_url(),
            headers={"Authorization": f"Bearer {full_key}"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_api_key_is_rejected():
    """A random key that was never created must return 401."""
    fake_key = f"sdd_{'x' * 43}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as raw:
        resp = await raw.get(
            _cli_pending_crs_url(),
            headers={"Authorization": f"Bearer {fake_key}"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_missing_authorization_header_is_rejected():
    """CLI endpoint with no Authorization header must return 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as raw:
        resp = await raw.get(_cli_pending_crs_url())
    assert resp.status_code == 401
