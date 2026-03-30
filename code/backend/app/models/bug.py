import enum
from typing import Optional
from datetime import datetime
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import BaseDocument


class BugStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    wont_fix = "wont_fix"
    closed = "closed"
    deleted = "deleted"


class BugSeverity(str, enum.Enum):
    critical = "critical"
    major = "major"
    minor = "minor"
    trivial = "trivial"


class Bug(BaseDocument):
    project_id: UUID = Field(alias="projectId")
    number: int
    slug: str
    path: Optional[str] = None
    title: str
    body: str
    status: BugStatus = BugStatus.draft
    severity: BugSeverity
    author_id: UUID = Field(alias="authorId")
    assignee_id: Optional[UUID] = Field(default=None, alias="assigneeId")
    closed_at: Optional[datetime] = Field(default=None, alias="closedAt")

    class Settings:
        name = "bugs"
        indexes = [
            IndexModel([("projectId", 1), ("number", 1)], unique=True),
            IndexModel([("projectId", 1), ("slug", 1)], unique=True),
        ]
