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
from datetime import UTC, datetime, timedelta

from app.config import settings
from app.models.bug import Bug
from app.models.change_request import ChangeRequest
from app.models.comment import Comment, EntityType
from app.models.user import User
from app.repositories import (
    CommentRepository,
    NotificationRepository,
    TenantRepository,
    UserRepository,
)
from app.services.email_templates import render_template
from app.services.mailer import send_email
from app.services.notifications import (
    EVENT_COMMENT_ADDED,
    EVENT_CONTENT_CHANGED,
    NotificationService,
)

logger = logging.getLogger(__name__)

COMMENT_EMAIL_COALESCING_WINDOW = timedelta(minutes=5)

# Truncate long markdown bodies in the plain-text email preview
EMAIL_BODY_EXCERPT_LENGTH = 500


def _formatted_number(entity: ChangeRequest | Bug) -> str:
    """Zero-padded progressive number, same rule as the API schemas."""
    return f"{entity.number:03d}"


def _item_route(tenant_id: uuid.UUID, entity_kind: str, entity: ChangeRequest | Bug) -> str:
    base = f"/tenants/{tenant_id}/projects/{entity.project_id}"
    if entity_kind == EntityType.change_request.value:
        return f"{base}/crs/{entity.id}"
    return f"{base}/bugs/{entity.id}"


def _item_url(tenant_id: uuid.UUID, entity_kind: str, entity: ChangeRequest | Bug) -> str:
    """Deep link landing directly on the comments section."""
    return (
        f"{settings.FRONTEND_URL.rstrip('/')}{_item_route(tenant_id, entity_kind, entity)}#comments"
    )


def _excerpt(body: str) -> str:
    text = body.strip()
    if len(text) > EMAIL_BODY_EXCERPT_LENGTH:
        text = text[:EMAIL_BODY_EXCERPT_LENGTH].rstrip() + "…"
    return text


class CollaborationService:
    """Comment/content-change notification dispatch for CRs and bugs."""

    def __init__(
        self,
        notification_service: NotificationService,
        notification_repo: NotificationRepository,
        comment_repo: CommentRepository,
        tenant_repo: TenantRepository,
        user_repo: UserRepository,
    ) -> None:
        self._notification_service = notification_service
        self._notification_repo = notification_repo
        self._comment_repo = comment_repo
        self._tenant_repo = tenant_repo
        self._user_repo = user_repo

    async def _resolve_actor_ids(
        self,
        tenant_id: uuid.UUID,
        entity_kind: str,
        entity: ChangeRequest | Bug,
        exclude_user_id: uuid.UUID | None,
    ) -> set[uuid.UUID]:
        """Actors of a CR/bug: author + assignee + distinct commenters.

        Excludes the triggering user and users who are not active tenant members.
        """
        actor_ids: set[uuid.UUID] = {entity.author_id}
        if entity.assignee_id is not None:
            actor_ids.add(entity.assignee_id)

        comments = await self._comment_repo.find_by_entity(entity_kind, entity.id)
        actor_ids.update(c.author_id for c in comments)

        active_ids = set(await self._tenant_repo.find_member_user_ids(tenant_id))
        actor_ids &= active_ids

        if exclude_user_id is not None:
            actor_ids.discard(exclude_user_id)
        return actor_ids

    async def _resolve_recipients(
        self, actor_ids: set[uuid.UUID], event_type: str
    ) -> list[tuple[User, bool]]:
        """Load users and their email preference for the event type.

        Returns a list of (user, email_enabled) tuples.
        """
        recipients: list[tuple[User, bool]] = []
        for actor_id in actor_ids:
            user = await self._user_repo.find_by_id(actor_id)
            if user is None:
                continue
            email_enabled = await self._notification_service.get_email_preference(
                actor_id, event_type
            )
            recipients.append((user, email_enabled))
        return recipients

    async def _send_comment_email(
        self,
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
        await self._notification_repo.record_email_sent(
            tenant_id, user.id, EVENT_COMMENT_ADDED, entity_kind, entity.id
        )

    async def _send_content_changed_email(
        self,
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
        self,
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
            actor_ids = await self._resolve_actor_ids(
                tenant_id, entity_kind, entity, exclude_user_id=actor_user_id
            )

            author = await self._user_repo.find_by_id(actor_user_id)
            comment_author_name = author.display_name if author else str(actor_user_id)

            noun = "CR" if entity_kind == EntityType.change_request.value else "bug"
            for actor_id in actor_ids:
                await self._notification_service.create_notification(
                    actor_id,
                    tenant_id,
                    EVENT_COMMENT_ADDED,
                    entity_kind,
                    entity.id,
                    f"New comment on {noun}: {entity.title}",
                )

            # Emails are best-effort: failures are logged and never propagate
            # to the triggering action (comment creation).
            for user, email_enabled in await self._resolve_recipients(
                actor_ids, EVENT_COMMENT_ADDED
            ):
                try:
                    if not email_enabled:
                        continue
                    if await self._notification_repo.find_recent_email_log(
                        user.id,
                        EVENT_COMMENT_ADDED,
                        entity_kind,
                        entity.id,
                        datetime.now(UTC) - COMMENT_EMAIL_COALESCING_WINDOW,
                    ):
                        continue  # coalesced into the email already sent this window
                    await self._send_comment_email(
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
        self,
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
            actor_ids = await self._resolve_actor_ids(
                tenant_id, entity_kind, entity, exclude_user_id=actor_user_id
            )

            editor = await self._user_repo.find_by_id(actor_user_id)
            editor_name = editor.display_name if editor else str(actor_user_id)

            noun = "CR" if entity_kind == EntityType.change_request.value else "bug"
            title_msg = f"{noun.upper()} '{entity.title}' content changed"
            detail_msg = f"{title_msg} ({', '.join(changed_fields)})"
            for actor_id in actor_ids:
                await self._notification_service.create_notification(
                    actor_id,
                    tenant_id,
                    EVENT_CONTENT_CHANGED,
                    entity_kind,
                    entity.id,
                    detail_msg,
                )

            # Emails are opt-in (content_changed defaults to off) and best-effort.
            for user, email_enabled in await self._resolve_recipients(
                actor_ids, EVENT_CONTENT_CHANGED
            ):
                try:
                    if not email_enabled:
                        continue
                    await self._send_content_changed_email(
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
