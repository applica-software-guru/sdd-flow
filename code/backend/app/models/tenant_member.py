import enum
from typing import Optional
from datetime import datetime
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import BaseDocument, utcnow


class MemberRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"


class TenantMember(BaseDocument):
    tenant_id: UUID = Field(alias="tenantId")
    user_id: UUID = Field(alias="userId")
    role: MemberRole
    invited_by: Optional[UUID] = Field(default=None, alias="invitedBy")
    joined_at: datetime = Field(default_factory=utcnow, alias="joinedAt")

    class Settings:
        name = "tenant_members"
        indexes = [
            IndexModel([("tenantId", 1), ("userId", 1)], unique=True),
        ]
