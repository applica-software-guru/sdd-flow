from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pymongo import IndexModel
from pydantic import Field

from app.models.base import ImmutableDocument


class NotificationEmailLog(ImmutableDocument):
    """Record of a notification email dispatched to a user for an entity.

    Used to coalesce comment emails: if a ``comment_added`` email was already
    sent to the same user for the same entity within the coalescing window,
    subsequent comments are batched into the next eligible email instead of
    sending one email per comment.
    """

    tenant_id: UUID = Field(alias="tenantId")
    user_id: UUID = Field(alias="userId")
    event_type: str = Field(alias="eventType")
    entity_type: Optional[str] = Field(default=None, alias="entityType")
    entity_id: Optional[UUID] = Field(default=None, alias="entityId")
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="sentAt")

    class Settings:
        name = "notification_email_logs"
        indexes = [
            IndexModel([("userId", 1), ("eventType", 1), ("entityId", 1), ("sentAt", -1)]),
        ]
