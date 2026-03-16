import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.bug import BugSeverity, BugStatus
from app.schemas.common import PaginatedResponse


class BugCreate(BaseModel):
    title: str
    body: str
    severity: BugSeverity
    assignee_id: uuid.UUID | None = None


class BugUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    severity: BugSeverity | None = None
    assignee_id: uuid.UUID | None = None


class BugTransition(BaseModel):
    status: BugStatus


class BugResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    body: str
    status: BugStatus
    severity: BugSeverity
    author_id: uuid.UUID
    assignee_id: uuid.UUID | None = None
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BugListResponse(PaginatedResponse[BugResponse]):
    pass
