from typing import Optional
from datetime import datetime
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import BaseDocument


class ApiKey(BaseDocument):
    project_id: UUID = Field(alias="projectId")
    name: str
    key_prefix: str = Field(alias="keyPrefix")
    key_hash: str = Field(alias="keyHash")
    created_by: UUID = Field(alias="createdBy")
    last_used_at: Optional[datetime] = Field(default=None, alias="lastUsedAt")
    revoked_at: Optional[datetime] = Field(default=None, alias="revokedAt")

    class Settings:
        name = "api_keys"
        indexes = [
            IndexModel("keyHash", unique=True),
        ]
