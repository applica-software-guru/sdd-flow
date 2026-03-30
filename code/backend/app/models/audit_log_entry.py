from typing import Optional
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import ImmutableDocument


class AuditLogEntry(ImmutableDocument):
    tenant_id: UUID = Field(alias="tenantId")
    user_id: Optional[UUID] = Field(default=None, alias="userId")
    event_type: str = Field(alias="eventType")
    entity_type: Optional[str] = Field(default=None, alias="entityType")
    entity_id: Optional[UUID] = Field(default=None, alias="entityId")
    details: dict = Field(default_factory=dict)

    class Settings:
        name = "audit_log_entries"
        indexes = [
            IndexModel([("tenantId", 1), ("createdAt", 1)]),
            IndexModel([("tenantId", 1), ("eventType", 1)]),
        ]
