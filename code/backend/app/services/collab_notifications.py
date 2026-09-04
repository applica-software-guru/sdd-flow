"""Comment and content-change notifications for CRs and bugs.

Implements the dispatch described in product/features/notifications.md:

- **Actors** of a CR/bug: author + current assignee (if any) + all distinct
  commenters, excluding the user who triggered the event and inactive members.
- In-app notifications are always created for every actor.
- Emails are sent only to actors with the matching email preference enabled
  (``comment_added`` defaults to on, ``content_changed`` to off).
- ``comment_added`` emails are coalesced: if one was already sent to the same
  recipient for the same entity within the coalescing window, the next email
  is deferred (the recipient gets at most one email per window per item).
- Dispatch failures never propagate: the triggering action must not fail.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.models.change_request import ChangeRequest
from app.models.bug import Bug
from app.models.comment import Comment, EntityType
from app.models.notification_email_log import NotificationEmailLog
from app.models.notification_preference import NotificationPreference
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.services.email_templates import render_template
from app.services.mailer import send_email
from app.services.notifications import create_notification

logger = logging.getLogger(__name__)

EVENT_ASSIGNED = "assigned"
EVENT_STATUS_CHANGED = "status_changed"
EVENT_COMMENT_ADDED = "comment_added"
EVENT_CONTENT_CHANGED = "content_changed"
EVENT_MENTIONED = "mentioned"

SUPPORTED_EVENT_TYPES = [
    EVENT_ASSIGNED,
    EVENT_STATUS_CHANGED,
    EVENT_COMMENT_ADDED,
    EVENT_CONTENT_CHANGED,
    EVENT_MENTIONED,
]

# Event types that email-notify by default when no preference record exists
DEFAULT_ENABLED_EMAIL_EVENTS = {EVENT_COMMENT_ADDED}

COMMENT_EMAIL_COALESCING_WINDOW = timedelta(minutes=5)

# Truncate long markdown bodies in the plain-text email preview
EMAIL_BODY_EXCERPT_LENGTH = 500


def _formatted_number(entity: ChangeRequest | Bug) -> str:
    """Zero-padded progressive number, same rule as the API schemas."""
    return f"{entity.number:03d}"


def default_email_enabled(event_type: str) -> bool:
    return event_type in DEFAULT_ENABLED_EMAIL_EVENTS


async def get_email_preference(user_id: uuid.UUID, event_type: str) -> bool:
    """Resolve the email preference for (user, event_type) with defaults."""
    pref = await NotificationPreference.find_one(
        {"userId": user_id, "eventType": event_type}
    )
    if pref is None:
        return default_email_enabled(event_type)
    return pref.email_enabled


async def _active_member_user_ids(tenant_id: uuid.UUID) -> set[uuid.UUID]:
    members = await TenantMember.find({"tenantId": tenant_id}).to_list()
    return {m.user_id for m in members}


async def resolve_actor_ids(
    tenant_id: uuid.UUID,
    entity_kind: str,
    entity: ChangeRequest | Bug,
    *,
    exclude_user_id: uuid.UUID | None = None,
) -> set[uuid.UUID]:
    """Actors of a CR/bug: author + assignee + distinct commenters.

    Excludes the triggering user and users who are not active tenant members.
    """
    actor_ids: set[uuid.UUID] = {entity.author_id}
    if entity.assignee_id is not None:
        actor_ids.add(entity.assignee_id)

    comments = await Comment.find(
        {"entityType": entity_kind, "entityId": entity.id}
    ).to_list()
    actor_ids.update(c.author_id for c in comments)

    active_ids = await _active_member_user_ids(tenant_id)
    actor_ids &= active_ids

    if exclude_user_id is not None:
        actor_ids.discard(exclude_user_id)
    return actor_ids


async def _resolve_recipients(
    actor_ids: set[uuid.UUID], event_type: str
) -> list[tuple[User, bool]]:
    """Load users and their email preference for the event type.

    Returns a list of (user, email_enabled) tuples.
    """
    recipients: list[tuple[User, bool]] = []
    for actor_id in actor_ids:
        user = await User.get(actor_id)
        if user is None:
            continue
        email_enabled = await get_email_preference(actor_id, event_type)
        recipients.append((user, email_enabled))
    return recipients


def _item_route(tenant_id: uuid.UUID, entity_kind: str, entity: ChangeRequest | Bug) -> str:
    base = f"/tenants/{tenant_id}/projects/{entity.project_id}"
    if entity_kind == EntityType.change_request.value:
        return f"{base}/crs/{entity.id}"
    return f"{base}/bugs/{entity.id}"


def _item_url(tenant_id: uuid.UUID, entity_kind: str, entity: ChangeRequest | Bug) -> str:
    """Deep link landing directly on the comments section."""
    return (
        f"{settings.FRONTEND_URL.rstrip('/')}"
        f"{_item_route(tenant_id, entity_kind, entity)}#comments"
    )


def _excerpt(body: str) -> str:
    text = body.strip()
    if len(text) > EMAIL_BODY_EXCERPT_LENGTH:
        text = text[:EMAIL_BODY_EXCERPT_LENGTH].rstrip() + "…"
    return text


async def _email_sent_recently(
    user_id: uuid.UUID, event_type: str, entity_kind: str, entity_id: uuid.UUID
) -> bool:
    since = datetime.now(timezone.utc) - COMMENT_EMAIL_COALESCING_WINDOW
    existing = await NotificationEmailLog.find_one(
        {
            "userId": user_id,
            "eventType": event_type,
            "entityType": entity_kind,
            "entityId": entity_id,
            "sentAt": {"$gte": since},
        }
    )
    return existing is not None


async def _record_email_sent(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    event_type: str,
    entity_kind: str,
    entity_id: uuid.UUID,
) -> None:
    await NotificationEmailLog(
        tenant_id=tenant_id,
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_kind,
        entity_id=entity_id,
    ).insert()


async def _send_comment_email(
    *,
    user: User,
    tenant_id: uuid.UUID,
    entity_kind: str,
    entity: ChangeRequest | Bug,
    project_name: str,
    comment_author_name: str,
    comment_body: str,
) -> None:
    """Send a comment email unless one was already sent inside the window."""
    noun = "CR" if entity_kind == EntityType.change_request.value else "Bug"
    number = _formatted_number(entity)
    item_url = _item_url(tenant_id, entity_kind, entity)
    context = {
        "title": f"New comment on {noun} {number}",
        "cta_label": f"Open {noun} #{number}",
        "cta_url": item_url,
        "project_name": project_name,
        "noun": noun,
        "number": number,
        "item_title": entity.title,
        "comment_author": comment_author_name,
        "comment_excerpt": _excerpt(comment_body),
    }
    await send_email(
        recipient_email=user.email,
        subject=render_template("emails/comment_added_subject.txt", **context),
        text_body=render_template("emails/comment_added_text.txt", **context),
        html_body=render_template("emails/comment_added.html", **context),
        log_label="CommentAdded",
    )
    await _record_email_sent(tenant_id, user.id, EVENT_COMMENT_ADDED, entity_kind, entity.id)


async def _send_content_changed_email(
    *,
    user: User,
    tenant_id: uuid.UUID,
    entity_kind: str,
    entity: ChangeRequest | Bug,
    project_name: str,
    editor_name: str,
    changed_fields: list[str],
) -> None:
    noun = "CR" if entity_kind == EntityType.change_request.value else "Bug"
    number = _formatted_number(entity)
    item_url = _item_url(tenant_id, entity_kind, entity)
    context = {
        "title": f"{noun} {number} content changed",
        "cta_label": f"Open {noun} #{number}",
        "cta_url": item_url,
        "project_name": project_name,
        "noun": noun,
        "number": number,
        "item_title": entity.title,
        "editor_name": editor_name,
        "changed_fields": ", ".join(changed_fields),
    }
    await send_email(
        recipient_email=user.email,
        subject=render_template("emails/content_changed_subject.txt", **context),
        text_body=render_template("emails/content_changed_text.txt", **context),
        html_body=render_template("emails/content_changed.html", **context),
        log_label="ContentChanged",
    )




async def notify_comment_added(
    tenant_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    entity_kind: str,
    entity: ChangeRequest | Bug,
    comment: Comment,
    project_name: str = "",
) -> None:
    """Notify all actors that a new comment was added.

    In-app notifications are created synchronously; emails are sent
    fire-and-forget to actors with the ``comment_added`` preference enabled.
    """
    try:
        actor_ids = await resolve_actor_ids(
            tenant_id, entity_kind, entity, exclude_user_id=actor_user_id
        )

        author = await User.get(actor_user_id)
        comment_author_name = author.display_name if author else str(actor_user_id)

        for actor_id in actor_ids:
            await create_notification(
                actor_id,
                tenant_id,
                EVENT_COMMENT_ADDED,
                entity_kind,
                entity.id,
                f"New comment on {'CR' if entity_kind == EntityType.change_request.value else 'bug'}: {entity.title}",
            )

        # Emails are best-effort: failures are logged and never propagate
        # to the triggering action (comment creation).
        for user, email_enabled in await _resolve_recipients(actor_ids, EVENT_COMMENT_ADDED):
            try:
                if not email_enabled:
                    continue
                if await _email_sent_recently(
                    user.id, EVENT_COMMENT_ADDED, entity_kind, entity.id
                ):
                    continue  # coalesced into the email already sent this window
                await _send_comment_email(
                    user=user,
                    tenant_id=tenant_id,
                    entity_kind=entity_kind,
                    entity=entity,
                    project_name=project_name,
                    comment_author_name=comment_author_name,
                    comment_body=comment.body,
                )
            except Exception:
                logger.exception("Failed to send comment_added email to %s", user.id)
    except Exception:
        logger.exception("Failed to dispatch comment_added notifications")


async def notify_content_changed(
    tenant_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    entity_kind: str,
    entity: ChangeRequest | Bug,
    changed_fields: list[str],
    project_name: str = "",
) -> None:
    """Notify all actors that the title/body of a CR/bug actually changed.

    In-app notifications are created synchronously; emails go only to actors
    who explicitly opted in to the ``content_changed`` email preference.
    """
    try:
        actor_ids = await resolve_actor_ids(
            tenant_id, entity_kind, entity, exclude_user_id=actor_user_id
        )

        editor = await User.get(actor_user_id)
        editor_name = editor.display_name if editor else str(actor_user_id)

        noun = "CR" if entity_kind == EntityType.change_request.value else "bug"
        for actor_id in actor_ids:
            await create_notification(
                actor_id,
                tenant_id,
                EVENT_CONTENT_CHANGED,
                entity_kind,
                entity.id,
                f"{noun.upper()} '{entity.title}' content changed ({', '.join(changed_fields)})",
            )

        # Emails are opt-in (content_changed defaults to off) and best-effort.
        for user, email_enabled in await _resolve_recipients(actor_ids, EVENT_CONTENT_CHANGED):
            try:
                if not email_enabled:
                    continue
                await _send_content_changed_email(
                    user=user,
                    tenant_id=tenant_id,
                    entity_kind=entity_kind,
                    entity=entity,
                    project_name=project_name,
                    editor_name=editor_name,
                    changed_fields=changed_fields,
                )
            except Exception:
                logger.exception("Failed to send content_changed email to %s", user.id)
    except Exception:
        logger.exception("Failed to dispatch content_changed notifications")
