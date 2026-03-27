import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.document_file import DocStatus


class DocCreate(BaseModel):
    path: str
    title: str
    content: str = ""


class DocUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    status: DocStatus | None = None


class DocResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    path: str
    title: str
    status: DocStatus
    version: int
    content: str
    last_modified_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocBulkItem(BaseModel):
    path: str
    title: str
    content: str
    status: DocStatus | None = None


class DocBulkRequest(BaseModel):
    documents: list[DocBulkItem]


class DocBulkResponse(BaseModel):
    created: int
    updated: int
    documents: list[DocResponse]


class DocEnrichRequest(BaseModel):
    content: str


class DocDeleteRequest(BaseModel):
    paths: list[str]


class DocDeleteResponse(BaseModel):
    deleted: int
    paths: list[str]
