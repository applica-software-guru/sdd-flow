import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.worker import WorkerStatus
from app.models.worker_job import JobStatus, JobType
from app.models.worker_job_message import MessageKind
from app.schemas.common import PaginatedResponse


# --- Worker schemas ---

class WorkerRegisterRequest(BaseModel):
    name: str
    agent: str = "claude"
    metadata: dict | None = None


class WorkerResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    status: WorkerStatus
    agent: str
    last_heartbeat_at: datetime | None = None
    registered_at: datetime
    is_online: bool = False

    model_config = {"from_attributes": True}


class WorkerHeartbeatRequest(BaseModel):
    status: WorkerStatus = WorkerStatus.online


# --- WorkerJob schemas ---

class WorkerJobCreate(BaseModel):
    entity_type: str  # "change_request" | "bug"
    entity_id: uuid.UUID
    job_type: JobType = JobType.apply
    agent: str | None = None


class WorkerJobResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    worker_id: uuid.UUID | None = None
    worker_name: str | None = None
    entity_type: str
    entity_id: uuid.UUID
    entity_title: str | None = None
    job_type: JobType = JobType.apply
    status: JobStatus
    agent: str
    exit_code: int | None = None
    created_by: uuid.UUID
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkerJobListResponse(PaginatedResponse[WorkerJobResponse]):
    pass


class WorkerJobMessageResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    kind: MessageKind
    content: str
    sequence: int
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkerJobDetail(WorkerJobResponse):
    messages: list[WorkerJobMessageResponse] = []


# --- CLI-side schemas ---

class WorkerJobAssignment(BaseModel):
    """Returned to the worker when it picks up a job via poll."""
    job_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    job_type: JobType
    prompt: str
    agent: str


class WorkerJobOutputRequest(BaseModel):
    lines: list[str]


class WorkerJobQuestionRequest(BaseModel):
    content: str


class WorkerJobAnswerRequest(BaseModel):
    content: str


class WorkerJobCompletedRequest(BaseModel):
    exit_code: int
