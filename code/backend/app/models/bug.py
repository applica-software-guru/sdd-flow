import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


class BugStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    wont_fix = "wont_fix"
    closed = "closed"


class BugSeverity(str, enum.Enum):
    critical = "critical"
    major = "major"
    minor = "minor"
    trivial = "trivial"


class Bug(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "bugs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[BugStatus] = mapped_column(
        Enum(BugStatus, name="bug_status_enum"), default=BugStatus.open, nullable=False
    )
    severity: Mapped[BugSeverity] = mapped_column(
        Enum(BugSeverity, name="bug_severity_enum"), nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    project: Mapped["Project"] = relationship("Project", back_populates="bugs")
    author: Mapped["User"] = relationship("User", foreign_keys=[author_id])
    assignee: Mapped["User | None"] = relationship("User", foreign_keys=[assignee_id])
