from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument


class NotificationPreference(BaseDocument):
    user_id: UUID = Field()
    event_type: str = Field()
    email_enabled: bool = Field(default=True)

    class Settings:
        name = "notification_preferences"
        indexes = [
            IndexModel([("userId", 1), ("eventType", 1)], unique=True),
        ]
