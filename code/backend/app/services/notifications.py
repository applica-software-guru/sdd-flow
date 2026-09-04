"""Notification service: in-app notifications and email preferences."""

import uuid

from fastapi import HTTPException, status

from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference
from app.repositories import NotificationRepository

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


def default_email_enabled(event_type: str) -> bool:
    return event_type in DEFAULT_ENABLED_EMAIL_EVENTS


class NotificationService:
    def __init__(self, notification_repo: NotificationRepository) -> None:
        self._notification_repo = notification_repo

    async def create_notification(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        event_type: str,
        entity_type: str,
        entity_id: uuid.UUID,
        title: str,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            tenant_id=tenant_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            title=title,
        )
        return await self._notification_repo.create(notification)

    async def list_notifications_for_user(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Notification], int]:
        return await self._notification_repo.find_by_user(
            user_id, unread_only=unread_only, page=page, page_size=page_size
        )

    async def unread_notification_count(self, user_id: uuid.UUID) -> int:
        return await self._notification_repo.count_unread(user_id)

    async def mark_notification_read(
        self, notification_id: uuid.UUID, user_id: uuid.UUID
    ) -> Notification | None:
        return await self._notification_repo.mark_read(notification_id, user_id)

    async def mark_all_notifications_read(self, user_id: uuid.UUID) -> int:
        return await self._notification_repo.mark_all_read(user_id)

    async def get_email_preferences(self, user_id: uuid.UUID) -> dict[str, bool]:
        """Stored email preferences keyed by event type (stored records only)."""
        prefs = await self._notification_repo.find_preferences_by_user(user_id)
        return {p.event_type: p.email_enabled for p in prefs}

    async def get_email_preference(self, user_id: uuid.UUID, event_type: str) -> bool:
        """Resolve the email preference for (user, event_type) with defaults."""
        pref = await self._notification_repo.get_preference(user_id, event_type)
        if pref is None:
            return default_email_enabled(event_type)
        return pref.email_enabled

    async def upsert_email_preference(
        self, user_id: uuid.UUID, event_type: str, email_enabled: bool
    ) -> NotificationPreference:
        """Upsert the email preference for one event type."""
        if event_type not in SUPPORTED_EVENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported event type. Supported: {', '.join(SUPPORTED_EVENT_TYPES)}",
            )
        return await self._notification_repo.upsert_preference(user_id, event_type, email_enabled)
