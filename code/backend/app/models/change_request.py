import enum
from typing import Optional
from datetime import datetime
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import BaseDocument


class CRStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    applied = "applied"
    closed = "closed"
    deleted = "deleted"


class ChangeRequest(BaseDocument):
    project_id: UUID = Field(alias="projectId")
    number: int
    slug: str
    path: Optional[str] = None
    title: str
    body: str
    status: CRStatus = CRStatus.draft
    author_id: UUID = Field(alias="authorId")
    assignee_id: Optional[UUID] = Field(default=None, alias="assigneeId")
    target_files: list[str] = Field(default_factory=list, alias="targetFiles")
    closed_at: Optional[datetime] = Field(default=None, alias="closedAt")

    class Settings:
        name = "change_requests"
        indexes = [
            IndexModel([("projectId", 1), ("number", 1)], unique=True),
            IndexModel([("projectId", 1), ("slug", 1)], unique=True),
        ]
