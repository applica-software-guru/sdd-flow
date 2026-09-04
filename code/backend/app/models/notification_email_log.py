from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import ImmutableDocument


class NotificationEmailLog(ImmutableDocument):
    """Record of a notification email dispatched to a user for an entity.

    Used to coalesce comment emails: if a ``comment_added`` email was already
    sent to the same user for the same entity within the coalescing window,
    subsequent comments are batched into the next eligible email instead of
    sending one email per comment.
    """

    tenant_id: UUID = Field()
    user_id: UUID = Field()
    event_type: str = Field()
    entity_type: str | None = Field(default=None)
    entity_id: UUID | None = Field(default=None)
    sent_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "notification_email_logs"
        indexes = [
            IndexModel([("userId", 1), ("eventType", 1), ("entityId", 1), ("sentAt", -1)]),
        ]
