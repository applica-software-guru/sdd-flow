from datetime import datetime
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import ImmutableDocument


class Notification(ImmutableDocument):
    user_id: UUID = Field()
    tenant_id: UUID = Field()
    event_type: str = Field()
    entity_type: str = Field()
    entity_id: UUID = Field()
    title: str
    read_at: datetime | None = Field(default=None)

    class Settings:
        name = "notifications"
        indexes = [
            IndexModel([("userId", 1), ("readAt", 1)]),
        ]
