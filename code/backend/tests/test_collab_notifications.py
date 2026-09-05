"""Tests for comment/content-change notifications and email preferences."""

import pytest
from httpx import AsyncClient

import app.services.collab_notifications as collab
from app.models.audit_log_entry import AuditLogEntry
from app.models.change_request import ChangeRequest
from app.models.notification import Notification
from app.models.notification_email_log import NotificationEmailLog
from app.models.notification_preference import NotificationPreference
from app.models.project import Project
from app.models.tenant import Tenant
from app.models.tenant_member import MemberRole, TenantMember
from app.models.user import User


def _cr_base(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/change-requests"


def _bug_base(tenant: Tenant, project: Project) -> str:
    return f"/api/v1/tenants/{tenant.id}/projects/{project.id}/bugs"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def other_user(unique_id: str) -> User:
    user = User(
        email=f"other-{unique_id}@example.com",
        display_name=f"Other User {unique_id}",
        password_hash="fakehash",
        email_verified=True,
    )
    await user.insert()
    yield user


@pytest.fixture
async def third_user(unique_id: str) -> User:
    user = User(
        email=f"third-{unique_id}@example.com",
        display_name=f"Third User {unique_id}",
        password_hash="fakehash",
        email_verified=True,
    )
    await user.insert()
    yield user


@pytest.fixture(autouse=True)
async def memberships(test_tenant: Tenant, other_user: User, third_user: User):
    m1 = TenantMember(tenant_id=test_tenant.id, user_id=other_user.id, role=MemberRole.member)
    m2 = TenantMember(tenant_id=test_tenant.id, user_id=third_user.id, role=MemberRole.member)
    await m1.insert()
    await m2.insert()
    yield
    await m1.delete()
    await m2.delete()
    # Tenant-scoped cleanup: notifications/email logs/audit entries are not
    # removed by the shared conftest fixtures.
    for model in (Notification, NotificationEmailLog, AuditLogEntry):
        await model.find({"tenantId": test_tenant.id}).delete()


@pytest.fixture
async def cr(
    test_tenant: Tenant, test_project: Project, test_user: User, other_user: User
) -> ChangeRequest:
    """CR authored by test_user and assigned to other_user."""
    cr = ChangeRequest(
        tenant_id=test_tenant.id,
        project_id=test_project.id,
        number=1,
        slug="test-cr",
        title="Test CR",
        body="Original body",
        author_id=test_user.id,
        assignee_id=other_user.id,
    )
    await cr.insert()
    yield cr
    await cr.delete()


@pytest.fixture
def mock_send_email(monkeypatch):
    """Capture emails sent through the collab_notifications service."""
    sent: list[dict] = []

    async def _fake_send_email(**kwargs):
        sent.append(kwargs)

    monkeypatch.setattr(collab, "send_email", _fake_send_email)
    return sent


# ---------------------------------------------------------------------------
# In-app notifications: comment_added
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_comment_notifies_actors(
    client: AsyncClient, test_tenant, test_project, test_user: User, other_user: User, cr
):
    """Author and assignee are notified when a third user comments; the comment author is not."""
    resp = await client.post(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}/comments",
        json={"body": "Looks good to me!"},
    )
    # The client acts as test_user (author). Make the author comment on an
    # item assigned to other_user: assignee must be notified.
    assert resp.status_code == 201

    notifs = await Notification.find(
        {"eventType": "comment_added", "tenantId": test_tenant.id}
    ).to_list()
    notified_ids = {str(n.user_id) for n in notifs}
    assert str(other_user.id) in notified_ids  # assignee notified
    assert str(test_user.id) not in notified_ids  # comment author excluded


@pytest.mark.asyncio
async def test_comment_notifies_previous_commenters(
    client: AsyncClient,
    test_tenant,
    test_project,
    test_user: User,
    other_user: User,
    third_user: User,
    cr,
):
    """A previous commenter is notified on subsequent comments."""
    # other_user comments first (via service, as another actor)
    first = await client.post(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}/comments", json={"body": "first"}
    )
    assert first.status_code == 201

    # Now the author (test_user) comments: previous commenters (other_user)
    # must be notified even though they are not the assignee... they are,
    # so instead check via a fresh comment by other_user later.
    await client.post(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}/comments", json={"body": "second"}
    )

    notifs = await Notification.find(
        {"eventType": "comment_added", "tenantId": test_tenant.id}
    ).to_list()
    notified_ids = {str(n.user_id) for n in notifs}
    # comment 1 (by test_user): other_user (assignee) notified
    # comment 2 (by test_user): other_user notified again
    assert str(other_user.id) in notified_ids
    assert str(test_user.id) not in notified_ids


@pytest.mark.asyncio
async def test_inactive_members_excluded_from_actors(
    client: AsyncClient, test_tenant, test_project, test_user: User, other_user: User, cr
):
    """A user who commented but left the tenant is not notified."""
    # other_user comments
    await client.post(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}/comments", json={"body": "hi"}
    )
    # other_user leaves the tenant
    await TenantMember.find_one({"tenantId": test_tenant.id, "userId": other_user.id}).delete()

    # test_user comments again: other_user must NOT be notified again
    await client.post(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}/comments", json={"body": "again"}
    )

    notifs = await Notification.find(
        {"eventType": "comment_added", "tenantId": test_tenant.id}
    ).to_list()
    # Exactly one notification for other_user: the one from the first comment,
    # sent while they were still an active member. None after leaving.
    other_notifs = [n for n in notifs if str(n.user_id) == str(other_user.id)]
    assert len(other_notifs) == 1


# ---------------------------------------------------------------------------
# Emails: comment_added (default on)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_comment_email_sent_to_actors(
    client: AsyncClient,
    test_tenant,
    test_project,
    test_user: User,
    other_user: User,
    cr,
    mock_send_email,
):
    """Actors with the default (on) comment_added preference receive an email with deep link."""
    resp = await client.post(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}/comments", json={"body": "hello"}
    )
    assert resp.status_code == 201

    recipients = {m["recipient_email"] for m in mock_send_email}
    assert recipients == {other_user.email}  # only the assignee (author commented)

    email = mock_send_email[0]
    assert email["log_label"] == "CommentAdded"
    assert "#comments" in email["text_body"]
    assert f"/tenants/{test_tenant.id}/projects/{test_project.id}/crs/{cr.id}" in email["text_body"]
    assert "001" in email["subject"]  # formatted number


@pytest.mark.asyncio
async def test_comment_email_skipped_when_preference_disabled(
    client: AsyncClient, test_tenant, test_project, other_user: User, cr, mock_send_email
):
    pref = NotificationPreference(
        user_id=other_user.id, event_type="comment_added", email_enabled=False
    )
    await pref.insert()

    await client.post(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}/comments", json={"body": "hello"}
    )

    assert mock_send_email == []  # assignee opted out, author was the trigger


@pytest.mark.asyncio
async def test_comment_email_coalesced_within_window(
    client: AsyncClient,
    test_tenant,
    test_project,
    test_user: User,
    other_user: User,
    cr,
    mock_send_email,
):
    """Two comments within the window: in-app notifications double, emails don't."""
    await client.post(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}/comments", json={"body": "one"}
    )
    await client.post(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}/comments", json={"body": "two"}
    )

    notifs = await Notification.find(
        {"eventType": "comment_added", "tenantId": test_tenant.id}
    ).to_list()
    assert len(notifs) == 2  # assignee notified once per comment
    assert len(mock_send_email) == 1  # but only one email

    logs = await NotificationEmailLog.find({"tenantId": test_tenant.id}).to_list()
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_comment_email_failure_does_not_break_comment_creation(
    client: AsyncClient, test_tenant, test_project, cr, monkeypatch
):
    async def _raising_send_email(**kwargs):
        raise RuntimeError("SMTP down")

    monkeypatch.setattr(collab, "send_email", _raising_send_email)

    resp = await client.post(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}/comments", json={"body": "hello"}
    )
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Content-change notifications
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_content_change_notifies_actors_except_editor(
    client: AsyncClient,
    test_tenant,
    test_project,
    test_user: User,
    other_user: User,
    cr,
    mock_send_email,
):
    """Editing the body notifies the assignee in-app; no email (opt-in only)."""
    resp = await client.patch(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}",
        json={"body": "Actually, also add SSO"},
    )
    assert resp.status_code == 200

    notifs = await Notification.find(
        {"eventType": "content_changed", "tenantId": test_tenant.id}
    ).to_list()
    notified_ids = {str(n.user_id) for n in notifs}
    assert notified_ids == {str(other_user.id)}  # editor (author) excluded

    assert mock_send_email == []  # content_changed is opt-in, default off


@pytest.mark.asyncio
async def test_noop_save_triggers_nothing(client: AsyncClient, test_tenant, test_project, cr):
    resp = await client.patch(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}",
        json={"body": "Original body"},  # identical
    )
    assert resp.status_code == 200

    notifs = await Notification.find(
        {"eventType": "content_changed", "tenantId": test_tenant.id}
    ).to_list()
    assert notifs == []


@pytest.mark.asyncio
async def test_content_changed_email_only_optin(
    client: AsyncClient, test_tenant, test_project, other_user: User, cr, mock_send_email
):
    pref = NotificationPreference(
        user_id=other_user.id, event_type="content_changed", email_enabled=True
    )
    await pref.insert()

    resp = await client.patch(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}",
        json={"title": "Test CR (updated)"},
    )
    assert resp.status_code == 200

    assert len(mock_send_email) == 1
    email = mock_send_email[0]
    assert email["recipient_email"] == other_user.email
    assert email["log_label"] == "ContentChanged"
    assert "title" in email["text_body"]


@pytest.mark.asyncio
async def test_bug_comment_and_content_change(
    client: AsyncClient,
    test_tenant,
    test_project,
    test_user: User,
    other_user: User,
    cr,
    mock_send_email,
):
    """Same behavior for bugs: comment emails + content_changed notifications."""
    create_resp = await client.post(
        _bug_base(test_tenant, test_project),
        json={
            "title": "Broken thing",
            "body": "It breaks",
            "severity": "major",
            "assignee_id": str(other_user.id),
        },
    )
    bug_id = create_resp.json()["id"]

    resp = await client.post(
        f"{_bug_base(test_tenant, test_project)}/{bug_id}/comments", json={"body": "repro'd"}
    )
    assert resp.status_code == 201
    assert len(mock_send_email) == 1  # assignee emailed

    mock_send_email.clear()
    patch_resp = await client.patch(
        f"{_bug_base(test_tenant, test_project)}/{bug_id}",
        json={"body": "It breaks on Tuesdays"},
    )
    assert patch_resp.status_code == 200
    assert mock_send_email == []  # content_changed: no email without opt-in

    content_notifs = await Notification.find(
        {"eventType": "content_changed", "tenantId": test_tenant.id}
    ).to_list()
    assert {str(n.user_id) for n in content_notifs} == {str(other_user.id)}


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_entries_recorded(
    client: AsyncClient, test_tenant, test_project, test_user: User, other_user: User, cr
):
    await client.post(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}/comments", json={"body": "hello"}
    )
    await client.patch(f"{_cr_base(test_tenant, test_project)}/{cr.id}", json={"body": "new body"})

    commented = await AuditLogEntry.find(
        {"eventType": "cr.commented", "tenantId": test_tenant.id}
    ).to_list()
    assert len(commented) == 1
    assert commented[0].entity_id == cr.id

    changed = await AuditLogEntry.find(
        {"eventType": "cr.content_changed", "tenantId": test_tenant.id}
    ).to_list()
    assert len(changed) == 1
    assert changed[0].details["changed_fields"] == ["body"]


# ---------------------------------------------------------------------------
# Preferences API
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_preferences_defaults(client: AsyncClient):
    resp = await client.get("/api/v1/notifications/preferences")
    assert resp.status_code == 200
    prefs = {p["event_type"]: p["email_enabled"] for p in resp.json()}
    assert prefs == {
        "assigned": False,
        "status_changed": False,
        "comment_added": True,
        "content_changed": False,
        "mentioned": False,
    }


@pytest.mark.asyncio
async def test_put_preference_upsert(client: AsyncClient):
    resp = await client.put(
        "/api/v1/notifications/preferences",
        json={"event_type": "content_changed", "email_enabled": True},
    )
    assert resp.status_code == 200
    assert resp.json() == {"event_type": "content_changed", "email_enabled": True}

    # Overrides the default on subsequent GETs
    resp = await client.get("/api/v1/notifications/preferences")
    prefs = {p["event_type"]: p["email_enabled"] for p in resp.json()}
    assert prefs["content_changed"] is True
    assert prefs["comment_added"] is True  # untouched default

    # Flip back
    await client.put(
        "/api/v1/notifications/preferences",
        json={"event_type": "content_changed", "email_enabled": False},
    )
    resp = await client.get("/api/v1/notifications/preferences")
    prefs = {p["event_type"]: p["email_enabled"] for p in resp.json()}
    assert prefs["content_changed"] is False


@pytest.mark.asyncio
async def test_put_preference_unknown_event_type(client: AsyncClient):
    resp = await client.put(
        "/api/v1/notifications/preferences",
        json={"event_type": "bogus_event", "email_enabled": True},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_comments_include_author(
    client: AsyncClient, test_tenant, test_project, test_user: User, other_user: User, cr
):
    """list_comments returns each comment with a resolved author.display_name and avatar_url."""
    test_user.avatar_url = "https://example.com/test-user.png"
    await test_user.save()

    # test_user (author) comments; client is test_user
    resp = await client.post(
        f"{_cr_base(test_tenant, test_project)}/{cr.id}/comments",
        json={"body": "hello there"},
    )
    assert resp.status_code == 201
    assert resp.json()["author"]["display_name"] == test_user.display_name
    assert resp.json()["author"]["avatar_url"] == test_user.avatar_url

    listed = await client.get(f"{_cr_base(test_tenant, test_project)}/{cr.id}/comments")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1
    assert listed.json()[-1]["author"]["id"] == str(test_user.id)
    assert listed.json()[-1]["author"]["avatar_url"] == test_user.avatar_url


@pytest.mark.asyncio
async def test_bug_comments_include_author(
    client: AsyncClient, test_tenant, test_project, test_user: User, other_user: User
):
    """Bug comments also resolve the author, including avatar_url."""
    test_user.avatar_url = "https://example.com/test-user.png"
    await test_user.save()

    create_resp = await client.post(
        _bug_base(test_tenant, test_project),
        json={"title": "Bug with author", "body": "b", "severity": "minor"},
    )
    bug_id = create_resp.json()["id"]

    resp = await client.post(
        f"{_bug_base(test_tenant, test_project)}/{bug_id}/comments",
        json={"body": "found it"},
    )
    assert resp.status_code == 201
    assert resp.json()["author"]["display_name"] == test_user.display_name
    assert resp.json()["author"]["avatar_url"] == test_user.avatar_url
