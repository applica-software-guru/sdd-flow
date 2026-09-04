import enum
from datetime import datetime
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument, utcnow


class MemberRole(enum.StrEnum):
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"


class TenantMember(BaseDocument):
    tenant_id: UUID = Field()
    user_id: UUID = Field()
    role: MemberRole
    invited_by: UUID | None = Field(default=None)
    joined_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_members"
        indexes = [
            IndexModel([("tenantId", 1), ("userId", 1)], unique=True),
        ]
