import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


class WorkerStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    busy = "busy"


class Worker(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "workers"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_worker_project_name"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[WorkerStatus] = mapped_column(
        Enum(WorkerStatus, name="worker_status_enum"),
        default=WorkerStatus.offline,
        nullable=False,
    )
    agent: Mapped[str] = mapped_column(String(100), default="claude", nullable=False)
    branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    project: Mapped["Project"] = relationship("Project", back_populates="workers")
    jobs: Mapped[list["WorkerJob"]] = relationship("WorkerJob", back_populates="worker")
