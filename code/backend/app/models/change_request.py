import enum
from datetime import datetime
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument


class CRStatus(enum.StrEnum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    applied = "applied"
    closed = "closed"
    deleted = "deleted"


class ChangeRequest(BaseDocument):
    project_id: UUID = Field()
    number: int
    slug: str
    path: str | None = None
    title: str
    body: str
    status: CRStatus = CRStatus.draft
    author_id: UUID = Field()
    assignee_id: UUID | None = Field(default=None)
    target_files: list[str] = Field(default_factory=list)
    closed_at: datetime | None = Field(default=None)

    class Settings:
        name = "change_requests"
        indexes = [
            IndexModel([("projectId", 1), ("number", 1)], unique=True),
            IndexModel([("projectId", 1), ("slug", 1)], unique=True),
        ]
