from typing import Optional
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import BaseDocument


class User(BaseDocument):
    email: str
    display_name: str = Field(alias="displayName")
    password_hash: Optional[str] = Field(default=None, alias="passwordHash")
    google_id: Optional[str] = Field(default=None, alias="googleId")
    avatar_url: Optional[str] = Field(default=None, alias="avatarUrl")
    email_verified: bool = Field(default=False, alias="emailVerified")

    @property
    def has_password(self) -> bool:
        """True when the account can log in with email/password."""
        return self.password_hash is not None

    @property
    def google_linked(self) -> bool:
        """True when the account is linked to a Google identity."""
        return self.google_id is not None

    class Settings:
        name = "users"
        indexes = [
            IndexModel("email", unique=True),
        ]
