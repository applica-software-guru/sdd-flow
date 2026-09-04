from datetime import datetime
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument


class RefreshToken(BaseDocument):
    user_id: UUID = Field()
    token_hash: str = Field()
    expires_at: datetime = Field()

    class Settings:
        name = "refresh_tokens"
        indexes = [
            IndexModel("tokenHash", unique=True),
            IndexModel("expiresAt", expireAfterSeconds=0),
        ]
