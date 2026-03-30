import enum
from typing import Optional
from datetime import datetime
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import BaseDocument


class JobStatus(str, enum.Enum):
    queued = "queued"
    assigned = "assigned"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class JobType(str, enum.Enum):
    apply = "apply"
    enrich = "enrich"
    sync = "sync"
    build = "build"
    custom = "custom"


class WorkerJob(BaseDocument):
    project_id: UUID = Field(alias="projectId")
    worker_id: Optional[UUID] = Field(default=None, alias="workerId")
    entity_type: Optional[str] = Field(default=None, alias="entityType")
    entity_id: Optional[UUID] = Field(default=None, alias="entityId")
    job_type: JobType = Field(alias="jobType")
    status: JobStatus = JobStatus.queued
    prompt: str = ""
    agent: str = "claude"
    model: Optional[str] = None
    exit_code: Optional[int] = Field(default=None, alias="exitCode")
    created_by: UUID = Field(alias="createdBy")
    started_at: Optional[datetime] = Field(default=None, alias="startedAt")
    completed_at: Optional[datetime] = Field(default=None, alias="completedAt")
    changed_files: list[str] = Field(default_factory=list, alias="changedFiles")

    class Settings:
        name = "worker_jobs"
        indexes = [
            IndexModel([("projectId", 1), ("status", 1)]),
        ]
