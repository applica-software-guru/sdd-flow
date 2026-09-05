from typing import Any
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import ImmutableDocument


class AuditLogEntry(ImmutableDocument):
    tenant_id: UUID | None = Field(default=None)
    user_id: UUID | None = Field(default=None)
    event_type: str = Field()
    entity_type: str | None = Field(default=None)
    entity_id: UUID | None = Field(default=None)
    entity_label: str | None = Field(default=None)
    summary: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "audit_log_entries"
        indexes = [
            IndexModel([("tenantId", 1), ("createdAt", 1)]),
            IndexModel([("tenantId", 1), ("eventType", 1)]),
            IndexModel([("createdAt", -1), ("eventType", 1)]),
        ]
