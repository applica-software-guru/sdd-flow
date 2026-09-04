from datetime import datetime
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument
from app.models.tenant_member import MemberRole


class TenantInvitation(BaseDocument):
    tenant_id: UUID = Field()
    email: str
    role: MemberRole
    invited_by: UUID = Field()
    token: str
    expires_at: datetime = Field()
    accepted_at: datetime | None = Field(default=None)

    class Settings:
        name = "tenant_invitations"
        indexes = [
            IndexModel("token", unique=True),
            IndexModel("expiresAt", expireAfterSeconds=0),
        ]
