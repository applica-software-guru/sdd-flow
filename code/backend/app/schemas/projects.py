import uuid
from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ProjectStats(BaseModel):
    document_count: int = 0
    open_cr_count: int = 0
    open_bug_count: int = 0


class ProjectResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    stats: ProjectStats | None = None

    model_config = {"from_attributes": True}


class ProjectResetRequest(BaseModel):
    confirm_slug: str


class ProjectResetResponse(BaseModel):
    message: str
    deleted_documents: int
    deleted_change_requests: int
    deleted_bugs: int
    deleted_comments: int
    deleted_notifications: int
