from typing import Optional
from datetime import datetime
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import ImmutableDocument


class Notification(ImmutableDocument):
    user_id: UUID = Field(alias="userId")
    tenant_id: UUID = Field(alias="tenantId")
    event_type: str = Field(alias="eventType")
    entity_type: str = Field(alias="entityType")
    entity_id: UUID = Field(alias="entityId")
    title: str
    read_at: Optional[datetime] = Field(default=None, alias="readAt")

    class Settings:
        name = "notifications"
        indexes = [
            IndexModel([("userId", 1), ("readAt", 1)]),
        ]
