from datetime import datetime
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import BaseDocument


class RefreshToken(BaseDocument):
    user_id: UUID = Field(alias="userId")
    token_hash: str = Field(alias="tokenHash")
    expires_at: datetime = Field(alias="expiresAt")

    class Settings:
        name = "refresh_tokens"
        indexes = [
            IndexModel("tokenHash", unique=True),
            IndexModel("expiresAt", expireAfterSeconds=0),
        ]
