"""
Tests for the assignment flow on change requests and bugs (BUG-009):
resolved author/assignee in responses, POST /assign, assignment history,
author_id/assignee_id filters, and PATCH backwards compatibility.
"""

import uuid
from datetime import UTC

import pytest
from httpx import AsyncClient

from app.models.assignment_history import AssignmentHistory
from app.models.bug import Bug, BugSeverity
from app.models.change_request import ChangeRequest
from app.models.notification import Notification
from app.models.tenant import Tenant
from app.models.user import User


@pytest.fixture
async def other_user(unique_id: str) -> User:
    """A second user, member of the same tenant."""
    user = User(
        email=f"other-{unique_id}@example.com",
        display_name=f"Other User {unique_id}",
        password_hash="fakehash",
        email_verified=True,
    )
    await user.insert()
    yield user


@pytest.fixture
async def outsider_user(unique_id: str) -> User:
    """A user that is NOT a member of the tenant."""
    user = User(
        email=f"outsider-{unique_id}@example.com",
        display_name=f"Outsider {unique_id}",
        password_hash="fakehash",
        email_verified=True,
    )
    await user.insert()
    yield user


@pytest.fixture(autouse=True)
async def other_member(test_tenant: Tenant, other_user: User):
    from app.models.tenant_member import MemberRole, TenantMember

    member = TenantMember(tenant_id=test_tenant.id, user_id=other_user.id, role=MemberRole.member)
    await member.insert()
    yield member
    await member.delete()


@pytest.fixture
async def cr(test_tenant: Tenant, test_project, test_user: User) -> ChangeRequest:
    cr = ChangeRequest(
        project_id=test_project.id,
        number=1,
        slug="test-cr",
        title="Test CR",
        body="body",
        author_id=test_user.id,
    )
    await cr.insert()
    yield cr
    await _cleanup_entity(cr.id)
    await cr.delete()


@pytest.fixture
async def bug(test_tenant: Tenant, test_project, test_user: User) -> Bug:
    bug = Bug(
        project_id=test_project.id,
        number=1,
        slug="test-bug",
        title="Test bug",
        body="body",
        severity=BugSeverity.major,
        author_id=test_user.id,
    )
    await bug.insert()
    yield bug
    await _cleanup_entity(bug.id)
    await bug.delete()


async def _cleanup_entity(entity_id: uuid.UUID) -> None:
    """Remove side-effect documents (history rows, notifications, audit entries)."""
    from app.models.audit_log_entry import AuditLogEntry
    from app.models.notification import Notification

    for model, field in (
        (AssignmentHistory, "entityId"),
        (Notification, "entityId"),
        (AuditLogEntry, "entityId"),
    ):
        await model.find({field: entity_id}).delete()


def _cr_url(tenant: Tenant, project, cr: ChangeRequest, suffix: str = "") -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/change-requests/{cr.id}{suffix}"


def _bug_url(tenant: Tenant, project, bug: Bug, suffix: str = "") -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/bugs/{bug.id}{suffix}"


@pytest.fixture(params=["cr", "bug"], ids=["cr", "bug"])
def entity_urls(request, test_tenant: Tenant, test_project, cr: ChangeRequest, bug: Bug):
    """Parametrize assignment tests over both CRs and bugs."""
    if request.param == "cr":
        return _cr_url(test_tenant, test_project, cr), cr
    return _bug_url(test_tenant, test_project, bug), bug


# ---------------------------------------------------------------------------
# Resolved users in responses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_returns_resolved_author_and_assignee(
    client: AsyncClient,
    test_tenant: Tenant,
    test_project,
    test_user: User,
    other_user: User,
    cr: ChangeRequest,
):
    cr.assignee_id = other_user.id
    await cr.save()

    resp = await client.get(_cr_url(test_tenant, test_project, cr))
    assert resp.status_code == 200
    data = resp.json()
    assert data["author"]["id"] == str(test_user.id)
    assert data["author"]["display_name"] == test_user.display_name
    assert data["author"]["email"] == test_user.email
    assert data["assignee"]["id"] == str(other_user.id)
    assert data["assignee"]["display_name"] == other_user.display_name


@pytest.mark.asyncio
async def test_list_returns_resolved_users(
    client: AsyncClient,
    test_tenant: Tenant,
    test_project,
    test_user: User,
    other_user: User,
    cr: ChangeRequest,
    bug: Bug,
):
    cr.assignee_id = other_user.id
    await cr.save()

    resp = await client.get(
        f"/api/v1/tenants/{test_tenant.id}/projects/{test_project.id}/change-requests"
    )
    assert resp.status_code == 200
    found = next(i for i in resp.json()["items"] if i["id"] == str(cr.id))
    assert found["author"]["display_name"] == test_user.display_name
    assert found["assignee"]["display_name"] == other_user.display_name


# ---------------------------------------------------------------------------
# Assign endpoint (parametrized over CR and bug)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assign_success(
    client: AsyncClient,
    entity_urls,
    test_user: User,
    other_user: User,
    test_tenant: Tenant,
):
    url, entity = entity_urls
    resp = await client.post(f"{url}/assign", json={"assignee_id": str(other_user.id)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["assignee_id"] == str(other_user.id)
    assert data["assignee"]["display_name"] == other_user.display_name

    # audit entry with label + summary
    audit = await __import__(
        "app.models.audit_log_entry", fromlist=["AuditLogEntry"]
    ).AuditLogEntry.find_one(
        {
            "eventType": f"{'cr' if 'change-requests' in url else 'bug'}.assigned",
            "entityId": entity.id,
        }
    )
    assert audit is not None
    assert audit.entity_label == entity.title
    assert audit.summary == f"assigned to {other_user.display_name}"

    # history row
    history = await AssignmentHistory.find({"entityId": entity.id}).to_list()
    assert len(history) == 1
    assert history[0].assignee_id == other_user.id
    assert history[0].assigned_by == test_user.id

    # notification for the new assignee
    notification = await Notification.find_one({"userId": other_user.id, "entityId": entity.id})
    assert notification is not None


@pytest.mark.asyncio
async def test_assign_to_non_member_fails(
    client: AsyncClient,
    entity_urls,
    outsider_user: User,
):
    url, _ = entity_urls
    resp = await client.post(f"{url}/assign", json={"assignee_id": str(outsider_user.id)})
    assert resp.status_code == 404
    assert "member" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_unassign(
    client: AsyncClient,
    entity_urls,
    test_tenant: Tenant,
    test_user: User,
    other_user: User,
):
    url, entity = entity_urls
    # setup: assign first
    entity.assignee_id = other_user.id
    await entity.save()
    await AssignmentHistory(
        tenant_id=test_tenant.id,
        entity_type=_kind(url),
        entity_id=entity.id,
        assignee_id=other_user.id,
        assigned_by=test_user.id,
    ).insert()

    resp = await client.post(f"{url}/assign", json={"assignee_id": None})
    assert resp.status_code == 200
    assert resp.json()["assignee_id"] is None

    # history has 2 rows now: initial + unassignment (assignee null)
    history = (
        await AssignmentHistory.find({"entityId": entity.id}).sort([("createdAt", 1)]).to_list()
    )
    assert len(history) == 2
    assert history[1].assignee_id is None

    # no notification for unassignment
    notification = await Notification.find_one({"userId": other_user.id, "entityId": entity.id})
    assert notification is None


@pytest.mark.asyncio
async def test_assign_noop_does_not_audit(
    client: AsyncClient,
    entity_urls,
    test_tenant: Tenant,
    other_user: User,
):
    url, entity = entity_urls
    entity.assignee_id = other_user.id
    await entity.save()
    await AssignmentHistory(
        tenant_id=test_tenant.id,
        entity_type=_kind(url),
        entity_id=entity.id,
        assignee_id=other_user.id,
    ).insert()

    audit_before = await _count_audits(entity)
    history_before = len(await AssignmentHistory.find({"entityId": entity.id}).to_list())

    resp = await client.post(f"{url}/assign", json={"assignee_id": str(other_user.id)})
    assert resp.status_code == 200
    assert await _count_audits(entity) == audit_before
    assert len(await AssignmentHistory.find({"entityId": entity.id}).to_list()) == history_before


def _kind(url: str) -> str:
    return "change_request" if "change-requests" in url else "bug"


async def _count_audits(entity) -> int:
    from app.models.audit_log_entry import AuditLogEntry

    prefix = "cr" if isinstance(entity, ChangeRequest) else "bug"
    return await AuditLogEntry.find(
        {"eventType": f"{prefix}.assigned", "entityId": entity.id}
    ).count()


# ---------------------------------------------------------------------------
# History endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assignments_history_endpoint(
    client: AsyncClient,
    test_tenant: Tenant,
    test_project,
    test_user: User,
    other_user: User,
    cr: ChangeRequest,
):
    # initial assignment (as if set at creation) then reassignment — explicit
    # timestamps so the newest-first ordering is deterministic
    from datetime import datetime

    base = datetime.now(UTC)
    await AssignmentHistory(
        tenant_id=test_tenant.id,
        entity_type="change_request",
        entity_id=cr.id,
        assignee_id=test_user.id,
        assigned_by=test_user.id,
        created_at=base,
    ).insert()
    await AssignmentHistory(
        tenant_id=test_tenant.id,
        entity_type="change_request",
        entity_id=cr.id,
        assignee_id=other_user.id,
        assigned_by=test_user.id,
        created_at=base.replace(microsecond=base.microsecond + 1000),
    ).insert()

    resp = await client.get(_cr_url(test_tenant, test_project, cr, "/assignments"))
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) == 2
    # newest first
    assert entries[0]["assignee"]["display_name"] == other_user.display_name
    assert entries[0]["assigned_by_name"] == test_user.display_name
    assert entries[1]["assignee"]["display_name"] == test_user.display_name


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cr_filters_author_and_assignee(
    client: AsyncClient,
    test_tenant: Tenant,
    test_project,
    test_user: User,
    other_user: User,
    cr: ChangeRequest,
):
    cr.assignee_id = other_user.id
    await cr.save()

    base = f"/api/v1/tenants/{test_tenant.id}/projects/{test_project.id}/change-requests"

    resp = await client.get(base, params={"author_id": str(test_user.id)})
    assert str(cr.id) in [i["id"] for i in resp.json()["items"]]

    resp = await client.get(base, params={"assignee_id": str(other_user.id)})
    assert str(cr.id) in [i["id"] for i in resp.json()["items"]]

    resp = await client.get(base, params={"assignee_id": str(test_user.id)})
    assert str(cr.id) not in [i["id"] for i in resp.json()["items"]]


@pytest.mark.asyncio
async def test_bug_filters_author_and_assignee(
    client: AsyncClient,
    test_tenant: Tenant,
    test_project,
    test_user: User,
    other_user: User,
    bug: Bug,
):
    bug.assignee_id = other_user.id
    await bug.save()

    base = f"/api/v1/tenants/{test_tenant.id}/projects/{test_project.id}/bugs"

    resp = await client.get(base, params={"author_id": str(test_user.id)})
    assert str(bug.id) in [i["id"] for i in resp.json()["items"]]

    resp = await client.get(base, params={"assignee_id": str(other_user.id)})
    assert str(bug.id) in [i["id"] for i in resp.json()["items"]]


# ---------------------------------------------------------------------------
# PATCH backwards compatibility (routes through the assignment flow)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_assignee_routes_through_assignment_flow(
    client: AsyncClient,
    test_tenant: Tenant,
    test_project,
    test_user: User,
    other_user: User,
    cr: ChangeRequest,
):
    resp = await client.patch(
        _cr_url(test_tenant, test_project, cr),
        json={"assignee_id": str(other_user.id)},
    )
    assert resp.status_code == 200
    assert resp.json()["assignee"]["display_name"] == other_user.display_name

    # side effects happened: audit + history + notification
    assert await _count_audits(cr) == 1
    history = await AssignmentHistory.find({"entityId": cr.id}).to_list()
    assert len(history) == 1


# ---------------------------------------------------------------------------
# Creation with assignee seeds history + validates member
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_cr_with_assignee_seeds_history(
    client: AsyncClient,
    test_tenant: Tenant,
    test_project,
    other_user: User,
):
    resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/projects/{test_project.id}/change-requests",
        json={"title": "Seeded", "body": "b", "assignee_id": str(other_user.id)},
    )
    assert resp.status_code == 201
    cr_id = uuid.UUID(resp.json()["id"])
    try:
        history = await AssignmentHistory.find({"entityId": cr_id}).to_list()
        assert len(history) == 1
        assert history[0].assignee_id == other_user.id
    finally:
        from app.models.change_request import ChangeRequest

        await AssignmentHistory.find({"entityId": cr_id}).delete()
        await Notification.find({"entityId": cr_id}).delete()
        await ChangeRequest.find({"_id": cr_id}).delete()


@pytest.mark.asyncio
async def test_create_cr_with_non_member_assignee_fails(
    client: AsyncClient,
    test_tenant: Tenant,
    test_project,
    outsider_user: User,
):
    resp = await client.post(
        f"/api/v1/tenants/{test_tenant.id}/projects/{test_project.id}/change-requests",
        json={"title": "Bad assignee", "body": "b", "assignee_id": str(outsider_user.id)},
    )
    assert resp.status_code == 404
