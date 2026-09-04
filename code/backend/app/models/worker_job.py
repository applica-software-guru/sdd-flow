import enum
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument


class JobStatus(enum.StrEnum):
    queued = "queued"
    assigned = "assigned"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class JobType(enum.StrEnum):
    apply = "apply"
    enrich = "enrich"
    sync = "sync"
    build = "build"
    custom = "custom"


class WorkerJob(BaseDocument):
    project_id: UUID = Field()
    worker_id: UUID | None = Field(default=None)
    entity_type: str | None = Field(default=None)
    entity_id: UUID | None = Field(default=None)
    job_type: JobType = Field()
    status: JobStatus = JobStatus.queued
    prompt: str = ""
    agent: str = "claude"
    model: str | None = None
    exit_code: int | None = Field(default=None)
    created_by: UUID = Field()
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    # ChangedFile-shaped dicts (stored via model_dump in worker completion flow)
    changed_files: list[dict[str, Any]] = Field(default_factory=list[dict[str, Any]])

    class Settings:
        name = "worker_jobs"
        indexes = [
            IndexModel([("projectId", 1), ("status", 1)]),
        ]
