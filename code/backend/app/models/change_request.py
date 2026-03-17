import enum
import uuid
from datetime import datetime

from sqlalchemy import ARRAY, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


class CRStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    applied = "applied"
    closed = "closed"


class ChangeRequest(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "change_requests"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CRStatus] = mapped_column(
        Enum(CRStatus, name="cr_status_enum"), default=CRStatus.draft, nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    target_files: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    project: Mapped["Project"] = relationship("Project", back_populates="change_requests")
    author: Mapped["User"] = relationship("User", foreign_keys=[author_id])
    assignee: Mapped["User | None"] = relationship("User", foreign_keys=[assignee_id])
