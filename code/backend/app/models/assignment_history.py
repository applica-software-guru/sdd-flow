from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import ImmutableDocument


class AssignmentHistory(ImmutableDocument):
    """Append-only assignment timeline for CRs and bugs.

    One row per change: `assignee_id = None` marks an unassignment.
    Seeded at creation when the entity is created with an assignee.
    """

    tenant_id: UUID = Field()
    entity_type: str = Field()  # "change_request" | "bug"
    entity_id: UUID = Field()
    assignee_id: UUID | None = Field(default=None)
    assigned_by: UUID | None = Field(default=None)

    class Settings:
        name = "assignment_history"
        indexes = [
            IndexModel([("tenantId", 1), ("entityType", 1), ("entityId", 1), ("createdAt", 1)]),
        ]
