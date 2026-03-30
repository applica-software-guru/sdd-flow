from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import BaseDocument


class NotificationPreference(BaseDocument):
    user_id: UUID = Field(alias="userId")
    event_type: str = Field(alias="eventType")
    email_enabled: bool = Field(default=True, alias="emailEnabled")

    class Settings:
        name = "notification_preferences"
        indexes = [
            IndexModel([("userId", 1), ("eventType", 1)], unique=True),
        ]
