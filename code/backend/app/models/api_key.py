from datetime import datetime
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument


class ApiKey(BaseDocument):
    project_id: UUID = Field()
    name: str
    key_prefix: str = Field()
    key_hash: str = Field()
    created_by: UUID = Field()
    last_used_at: datetime | None = Field(default=None)
    revoked_at: datetime | None = Field(default=None)

    class Settings:
        name = "api_keys"
        indexes = [
            IndexModel("keyHash", unique=True),
        ]
