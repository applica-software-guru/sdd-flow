from typing import Optional
from datetime import datetime
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import BaseDocument
from app.models.tenant_member import MemberRole


class TenantInvitation(BaseDocument):
    tenant_id: UUID = Field(alias="tenantId")
    email: str
    role: MemberRole
    invited_by: UUID = Field(alias="invitedBy")
    token: str
    expires_at: datetime = Field(alias="expiresAt")
    accepted_at: Optional[datetime] = Field(default=None, alias="acceptedAt")

    class Settings:
        name = "tenant_invitations"
        indexes = [
            IndexModel("token", unique=True),
            IndexModel("expiresAt", expireAfterSeconds=0),
        ]
