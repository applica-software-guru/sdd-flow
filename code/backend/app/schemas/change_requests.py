import uuid
from datetime import datetime

from pydantic import BaseModel, computed_field

from app.models.change_request import CRStatus
from app.schemas.common import PaginatedResponse


class CRCreate(BaseModel):
    title: str
    body: str
    assignee_id: uuid.UUID | None = None
    target_files: list[str] | None = None


class CRUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    assignee_id: uuid.UUID | None = None
    target_files: list[str] | None = None


class CRTransition(BaseModel):
    status: CRStatus


class CRResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    number: int
    slug: str
    path: str | None = None
    title: str
    body: str
    status: CRStatus
    author_id: uuid.UUID
    assignee_id: uuid.UUID | None = None
    target_files: list[str] | None = None
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def formatted_number(self) -> str:
        return str(self.number).zfill(3)


class CRListResponse(PaginatedResponse[CRResponse]):
    pass


class CREnrichRequest(BaseModel):
    body: str


class CRBulkItem(BaseModel):
    path: str
    title: str
    body: str
    status: CRStatus | None = None
    id: uuid.UUID | None = None


class CRBulkRequest(BaseModel):
    change_requests: list[CRBulkItem]


class CRBulkResponse(BaseModel):
    created: int
    updated: int
    change_requests: list[CRResponse]


class CRDeleteRequest(BaseModel):
    paths: list[str]


class CRDeleteResponse(BaseModel):
    deleted: int
    paths: list[str]
