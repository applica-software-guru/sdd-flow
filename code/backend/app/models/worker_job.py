import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


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
    custom = "custom"


class WorkerJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "worker_jobs"
    __table_args__ = (
        Index("ix_worker_jobs_project_status", "project_id", "status"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    worker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workers.id", ondelete="SET NULL"), nullable=True
    )
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum"),
        default=JobStatus.queued,
        nullable=False,
    )
    job_type: Mapped[JobType] = mapped_column(
        Enum(JobType, name="job_type_enum"),
        default=JobType.apply,
        nullable=False,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    agent: Mapped[str] = mapped_column(String(100), default="claude", nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    changed_files: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="worker_jobs")
    worker: Mapped["Worker | None"] = relationship("Worker", back_populates="jobs")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    messages: Mapped[list["WorkerJobMessage"]] = relationship(
        "WorkerJobMessage", back_populates="job", order_by="WorkerJobMessage.sequence"
    )
