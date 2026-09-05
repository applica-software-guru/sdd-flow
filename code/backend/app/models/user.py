from enum import StrEnum

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument


class PlatformRole(StrEnum):
    user = "user"
    super_user = "super_user"


class User(BaseDocument):
    email: str
    display_name: str = Field()
    password_hash: str | None = Field(default=None)
    google_id: str | None = Field(default=None)
    avatar_url: str | None = Field(default=None)
    email_verified: bool = Field(default=False)
    platform_role: PlatformRole = Field(default=PlatformRole.user)

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
