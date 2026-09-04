from typing import Optional
from uuid import UUID

from pymongo import IndexModel
from pydantic import Field

from app.models.base import ImmutableDocument


class AssignmentHistory(ImmutableDocument):
    """Append-only assignment timeline for CRs and bugs.

    One row per change: `assignee_id = None` marks an unassignment.
    Seeded at creation when the entity is created with an assignee.
    """

    tenant_id: UUID = Field(alias="tenantId")
    entity_type: str = Field(alias="entityType")  # "change_request" | "bug"
    entity_id: UUID = Field(alias="entityId")
    assignee_id: Optional[UUID] = Field(default=None, alias="assigneeId")
    assigned_by: Optional[UUID] = Field(default=None, alias="assignedBy")

    class Settings:
        name = "assignment_history"
        indexes = [
            IndexModel([("tenantId", 1), ("entityType", 1), ("entityId", 1), ("createdAt", 1)]),
        ]
