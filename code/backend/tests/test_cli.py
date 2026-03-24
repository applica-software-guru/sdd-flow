"""Tests for /api/v1/cli endpoints."""

import hashlib
import uuid

import pytest
from httpx import AsyncClient

from app.models.api_key import ApiKey


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unique_key(prefix: str) -> str:
    """Return a unique raw key for each test run to avoid hash collisions."""
    return f"{prefix}_{uuid.uuid4().hex}"


async def _make_api_key(db_session, test_project, test_user, raw_key: str) -> ApiKey:
    api_key = ApiKey(
        project_id=test_project.id,
        name="CLI Test Key",
        key_prefix=raw_key[:12],
        key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
        created_by=test_user.id,
    )
    db_session.add(api_key)
    await db_session.commit()
    return api_key


# ---------------------------------------------------------------------------
# push-docs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_push_docs_returns_fully_serialized_documents(
    client: AsyncClient,
    db_session,
    test_project,
    test_user,
):
    raw_key = _unique_key("key")
    await _make_api_key(db_session, test_project, test_user, raw_key)

    response = await client.post(
        "/api/v1/cli/push-docs",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "documents": [
                {
                    "path": "product/features/search.md",
                    "title": "Search",
                    "content": "# Search\n\nDocs content",
                },
                {
                    "path": "system/interfaces.md",
                    "title": "Interfaces",
                    "content": "# Interfaces\n\nInterface details",
                },
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 2
    assert data["updated"] == 0
    assert len(data["documents"]) == 2
    for document in data["documents"]:
        assert document["created_at"]
        assert document["updated_at"]
        assert document["status"] == "synced"


# ---------------------------------------------------------------------------
# push-crs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_push_crs_creates_with_number_and_slug(
    client: AsyncClient, db_session, test_project, test_user
):
    raw_key = _unique_key("key")
    await _make_api_key(db_session, test_project, test_user, raw_key)

    resp = await client.post(
        "/api/v1/cli/push-crs",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "change_requests": [
                {"path": "change-requests/my-cr.md", "title": "My CR", "body": "body"},
            ]
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] == 1
    cr = data["change_requests"][0]
    assert "number" in cr
    assert "formatted_number" in cr
    assert "slug" in cr
    assert cr["number"] >= 1


@pytest.mark.asyncio
async def test_push_crs_restores_number_from_numeric_path(
    client: AsyncClient, db_session, test_project, test_user
):
    raw_key = _unique_key("key")
    await _make_api_key(db_session, test_project, test_user, raw_key)

    resp = await client.post(
        "/api/v1/cli/push-crs",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "change_requests": [
                {
                    "path": "change-requests/042-fix-auth.md",
                    "title": "Fix auth",
                    "body": "Fix the auth module",
                },
            ]
        },
    )
    assert resp.status_code == 200
    cr = resp.json()["change_requests"][0]
    assert cr["number"] == 42
    assert cr["formatted_number"] == "042"
    assert cr["slug"] == "fix-auth"


@pytest.mark.asyncio
async def test_push_crs_derives_slug_from_path_remainder(
    client: AsyncClient, db_session, test_project, test_user
):
    raw_key = _unique_key("key")
    await _make_api_key(db_session, test_project, test_user, raw_key)

    resp = await client.post(
        "/api/v1/cli/push-crs",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "change_requests": [
                {
                    "path": "change-requests/007-add-dark-mode.md",
                    "title": "Add dark mode support",
                    "body": "body",
                },
            ]
        },
    )
    assert resp.status_code == 200
    cr = resp.json()["change_requests"][0]
    assert cr["number"] == 7
    assert cr["slug"] == "add-dark-mode"


@pytest.mark.asyncio
async def test_push_crs_update_does_not_change_slug_or_number(
    client: AsyncClient, db_session, test_project, test_user
):
    raw_key = _unique_key("key")
    await _make_api_key(db_session, test_project, test_user, raw_key)

    # Create
    create_resp = await client.post(
        "/api/v1/cli/push-crs",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "change_requests": [
                {"path": "change-requests/005-some-cr.md", "title": "Some CR", "body": "original"},
            ]
        },
    )
    assert create_resp.status_code == 200
    cr = create_resp.json()["change_requests"][0]
    original_number = cr["number"]
    original_slug = cr["slug"]
    cr_id = cr["id"]

    # Update by id — slug and number must not change
    update_resp = await client.post(
        "/api/v1/cli/push-crs",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "change_requests": [
                {
                    "id": cr_id,
                    "path": "change-requests/005-some-cr.md",
                    "title": "Some CR — renamed",
                    "body": "updated body",
                },
            ]
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()["change_requests"][0]
    assert updated["number"] == original_number
    assert updated["slug"] == original_slug
    assert updated["title"] == "Some CR — renamed"


# ---------------------------------------------------------------------------
# push-bugs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_push_bugs_creates_with_number_and_slug(
    client: AsyncClient, db_session, test_project, test_user
):
    raw_key = _unique_key("key")
    await _make_api_key(db_session, test_project, test_user, raw_key)

    resp = await client.post(
        "/api/v1/cli/push-bugs",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "bugs": [
                {"path": "bugs/my-bug.md", "title": "My bug", "body": "body", "severity": "minor"},
            ]
        },
    )
    assert resp.status_code == 200
    bug = resp.json()["bugs"][0]
    assert "number" in bug
    assert "formatted_number" in bug
    assert "slug" in bug
    assert bug["number"] >= 1


@pytest.mark.asyncio
async def test_push_bugs_restores_number_from_numeric_path(
    client: AsyncClient, db_session, test_project, test_user
):
    raw_key = _unique_key("key")
    await _make_api_key(db_session, test_project, test_user, raw_key)

    resp = await client.post(
        "/api/v1/cli/push-bugs",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "bugs": [
                {
                    "path": "bugs/003-login-crash.md",
                    "title": "Login crash",
                    "body": "Crashes on login",
                    "severity": "critical",
                },
            ]
        },
    )
    assert resp.status_code == 200
    bug = resp.json()["bugs"][0]
    assert bug["number"] == 3
    assert bug["formatted_number"] == "003"
    assert bug["slug"] == "login-crash"


# ---------------------------------------------------------------------------
# pending-crs / open-bugs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pending_crs_include_number_and_slug(
    client: AsyncClient, db_session, test_project, test_user
):
    raw_key = _unique_key("key")
    await _make_api_key(db_session, test_project, test_user, raw_key)

    await client.post(
        "/api/v1/cli/push-crs",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "change_requests": [
                {"path": "change-requests/001-my-cr.md", "title": "My CR", "body": "body"},
            ]
        },
    )

    resp = await client.get(
        "/api/v1/cli/pending-crs",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert resp.status_code == 200
    crs = resp.json()
    assert len(crs) >= 1
    cr = crs[0]
    assert "number" in cr
    assert "formatted_number" in cr
    assert "slug" in cr


@pytest.mark.asyncio
async def test_open_bugs_include_number_and_slug(
    client: AsyncClient, db_session, test_project, test_user
):
    raw_key = _unique_key("key")
    await _make_api_key(db_session, test_project, test_user, raw_key)

    await client.post(
        "/api/v1/cli/push-bugs",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "bugs": [
                {"path": "bugs/001-crash.md", "title": "Crash", "body": "body", "severity": "critical"},
            ]
        },
    )

    resp = await client.get(
        "/api/v1/cli/open-bugs",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert resp.status_code == 200
    bugs = resp.json()
    assert len(bugs) >= 1
    bug = bugs[0]
    assert "number" in bug
    assert "formatted_number" in bug
    assert "slug" in bug


# ---------------------------------------------------------------------------
# mark-cr-applied / mark-bug-resolved
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mark_cr_applied_includes_number_and_slug(
    client: AsyncClient, db_session, test_project, test_user
):
    raw_key = _unique_key("key")
    await _make_api_key(db_session, test_project, test_user, raw_key)

    push_resp = await client.post(
        "/api/v1/cli/push-crs",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "change_requests": [
                {"path": "change-requests/010-some.md", "title": "Some CR", "body": "body"},
            ]
        },
    )
    cr_id = push_resp.json()["change_requests"][0]["id"]

    resp = await client.post(
        f"/api/v1/cli/crs/{cr_id}/applied",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "applied"
    assert "number" in data
    assert "formatted_number" in data
    assert "slug" in data


@pytest.mark.asyncio
async def test_mark_bug_resolved_includes_number_and_slug(
    client: AsyncClient, db_session, test_project, test_user
):
    raw_key = _unique_key("key")
    await _make_api_key(db_session, test_project, test_user, raw_key)

    push_resp = await client.post(
        "/api/v1/cli/push-bugs",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={
            "bugs": [
                {"path": "bugs/002-crash.md", "title": "Crash bug", "body": "body", "severity": "major"},
            ]
        },
    )
    bug_id = push_resp.json()["bugs"][0]["id"]

    resp = await client.post(
        f"/api/v1/cli/bugs/{bug_id}/resolved",
        headers={"Authorization": f"Bearer {raw_key}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "resolved"
    assert "number" in data
    assert "formatted_number" in data
    assert "slug" in data
