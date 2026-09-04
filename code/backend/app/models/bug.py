import enum
from datetime import datetime
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument


class BugStatus(enum.StrEnum):
    draft = "draft"
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    wont_fix = "wont_fix"
    closed = "closed"
    deleted = "deleted"


class BugSeverity(enum.StrEnum):
    critical = "critical"
    major = "major"
    minor = "minor"
    trivial = "trivial"


class Bug(BaseDocument):
    project_id: UUID = Field()
    number: int
    slug: str
    path: str | None = None
    title: str
    body: str
    status: BugStatus = BugStatus.draft
    severity: BugSeverity
    author_id: UUID = Field()
    assignee_id: UUID | None = Field(default=None)
    closed_at: datetime | None = Field(default=None)

    class Settings:
        name = "bugs"
        indexes = [
            IndexModel([("projectId", 1), ("number", 1)], unique=True),
            IndexModel([("projectId", 1), ("slug", 1)], unique=True),
        ]
